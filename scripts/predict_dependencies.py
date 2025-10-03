import torch
import pickle
import numpy as np
from text_embedding import TextEmbedder
from torch_geometric.nn import GCNConv

class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, num_layers=3):
        super().__init__()
        self.convs = torch.nn.ModuleList()
        self.convs.append(GCNConv(in_channels, hidden_channels))
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
        
    def encode(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = x.relu()
        return x
    
    def decode(self, z, edge_index):
        src, dst = edge_index
        return (z[src] * z[dst]).sum(dim=-1)

print("Loading model and data...")
splits = torch.load('../data/graphs/train_val_test_split.pt')
with open('../data/graphs/graph_with_embeddings.gpickle', 'rb') as f:
    G = pickle.load(f)

# Build mapping from graph raw_data
node_list = list(G.nodes())
idx_to_info = {}
for i, node_id in enumerate(node_list):
    raw_data = G.nodes[node_id].get('raw_data', {})
    fields = raw_data.get('fields', {})
    idx_to_info[i] = {
        'id': str(node_id),
        'key': raw_data.get('key', 'N/A'),
        'summary': fields.get('summary', 'No summary'),
        'description': fields.get('description', 'No description')
    }

device = torch.device('cpu')
model = GCN(splits['x'].shape[1], 128, num_layers=3).to(device)  # Match training
model.load_state_dict(torch.load('../data/graphs/best_model_balanced.pt', map_location=device))
model.eval()

def predict_dependencies(new_ticket_text, top_k=10, threshold=0.65, show_details=False):
    print(f"\nAnalyzing ticket: '{new_ticket_text[:80]}...'")
    
    embedder = TextEmbedder(model_name="bert-base-uncased", device="cpu")
    new_embedding = embedder.encode_texts([new_ticket_text])[0]
    
    with torch.no_grad():
        new_emb = torch.tensor(new_embedding, dtype=torch.float)
        existing_embs = splits['x']
        
        # Cosine similarity
        new_norm = new_emb / new_emb.norm()
        existing_norm = existing_embs / existing_embs.norm(dim=1, keepdim=True)
        scores = (new_norm @ existing_norm.T).cpu().numpy()
    
    valid_indices = np.where(scores > threshold)[0]
    if len(valid_indices) == 0:
        print(f"No predictions above threshold {threshold}")
        print(f"Max score: {scores.max():.4f}, showing top {top_k} anyway:")
        top_indices = scores.argsort()[-top_k:][::-1]
    else:
        top_indices = valid_indices[scores[valid_indices].argsort()[-top_k:][::-1]]
    
    print(f"\n{'Rank':<6} {'Issue Key':<20} {'Score':<8} {'Summary':<60}")
    print("-" * 100)
    
    results = []
    for rank, idx in enumerate(top_indices, 1):
        info = idx_to_info[idx]
        score = scores[idx]
        summary = info['summary'][:57] + '...' if len(info['summary']) > 60 else info['summary']
        print(f"{rank:<6} {info['key']:<20} {score:.4f}   {summary:<60}")
        results.append((info['key'], info['id'], score, info))
        
        if show_details and rank <= 3:
            print(f"       Description: {info['description'][:200]}...")
            print()
    
    return results

if __name__ == "__main__":
    print("\n" + "="*100)
    print("EXAMPLE 1: Login Issue")
    print("="*100)
    example1 = "Login functionality is broken. Users cannot authenticate. Need to fix ASAP."
    predictions1 = predict_dependencies(example1, top_k=10, threshold=0.7, show_details=True)
    
    print("\n" + "="*100)
    print("EXAMPLE 2: Database Connection")
    print("="*100)
    example2 = "Database connection timeout. Application cannot connect to MySQL server."
    predictions2 = predict_dependencies(example2, top_k=5, threshold=0.7)
    
    print("\n\nTo test with your own ticket:")
    print('predictions = predict_dependencies("your ticket text", threshold=0.7, show_details=True)')