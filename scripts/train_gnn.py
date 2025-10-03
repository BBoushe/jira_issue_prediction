import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.nn import GATConv
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report, confusion_matrix
import numpy as np

splits = torch.load('../data/graphs/train_val_test_split.pt')
x = splits['x']
train_edge_index = splits['train_edge_index']
train_edge_attr = splits['train_edge_attr']
val_edge_index = splits['val_edge_index']
val_edge_attr = splits['val_edge_attr']
test_edge_index = splits['test_edge_index']
test_edge_attr = splits['test_edge_attr']

# === MODERATE OVERSAMPLING (5x instead of 15x) ===
dep_mask = train_edge_attr == 1
rel_mask = train_edge_attr == 0
dep_edges = train_edge_index[:, dep_mask]
rel_edges = train_edge_index[:, rel_mask]

oversample_factor = 5  # Reduced from 15
dep_edges_oversampled = dep_edges.repeat(1, oversample_factor)
dep_labels_oversampled = torch.ones(dep_edges_oversampled.shape[1], dtype=torch.long)

train_edge_index = torch.cat([rel_edges, dep_edges_oversampled], dim=1)
train_edge_attr = torch.cat([train_edge_attr[rel_mask], dep_labels_oversampled])

perm = torch.randperm(train_edge_index.shape[1])
train_edge_index = train_edge_index[:, perm]
train_edge_attr = train_edge_attr[perm]

print(f"Balanced training: {train_edge_index.shape[1]} edges")
print(f"  Dependency: {(train_edge_attr==1).sum()} ({(train_edge_attr==1).sum()/len(train_edge_attr)*100:.1f}%)")
print(f"  Related: {(train_edge_attr==0).sum()}\n")

class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, num_layers=2):
        super().__init__()
        self.convs = torch.nn.ModuleList()
        self.convs.append(GCNConv(in_channels, hidden_channels))
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
        
    def encode(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:  # ReLU on all but last layer
                x = x.relu()
        return x
    
    def decode(self, z, edge_index):
        src, dst = edge_index
        return (z[src] * z[dst]).sum(dim=-1)

# Test with 3 layers
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = GCN(x.shape[1], 128, num_layers=3).to(device)
    

# class GAT(torch.nn.Module):
#     def __init__(self, in_channels, hidden_channels):
#         super().__init__()
#         self.conv1 = GATConv(in_channels, hidden_channels, heads=4, concat=True)
#         self.conv2 = GATConv(hidden_channels*4, hidden_channels, heads=1)
    
#     def encode(self, x, edge_index):
#         x = self.conv1(x, edge_index).relu()
#         return self.conv2(x, edge_index)
    
#     def decode(self, z, edge_index):
#         src, dst = edge_index
#         return (z[src] * z[dst]).sum(dim=-1)

# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# model = GCN(x.shape[1], 128).to(device)
# model = GAT(x.shape[1], 128).to(device)

# Moderate class weighting (not too aggressive)
pos_weight = torch.tensor([3.0]).to(device)  # Fixed weight instead of computed
print(f"Using pos_weight: {pos_weight.item()}\n")

optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)

x = x.to(device)
train_edge_index = train_edge_index.to(device)
train_edge_attr = train_edge_attr.to(device)
val_edge_index = val_edge_index.to(device)
val_edge_attr = val_edge_attr.to(device)
test_edge_index = test_edge_index.to(device)
test_edge_attr = test_edge_attr.to(device)

def train():
    model.train()
    optimizer.zero_grad()
    z = model.encode(x, train_edge_index)
    out = model.decode(z, train_edge_index)
    
    # Weighted BCE (no focal loss)
    loss = F.binary_cross_entropy_with_logits(
        out, 
        train_edge_attr.float(),
        pos_weight=pos_weight
    )
    
    loss.backward()
    optimizer.step()
    return loss.item()

@torch.no_grad()
def test(edge_index, edge_attr):
    model.eval()
    z = model.encode(x, train_edge_index)
    out = model.decode(z, edge_index).sigmoid()
    preds = out.cpu().numpy()
    labels = edge_attr.cpu().numpy()
    auc = roc_auc_score(labels, preds)
    ap = average_precision_score(labels, preds)
    binary_preds = (preds > 0.5).astype(int)
    return auc, ap, preds, labels, binary_preds

@torch.no_grad()
def find_optimal_threshold(edge_index, edge_attr):
    """Find optimal threshold on validation set"""
    model.eval()
    z = model.encode(x, train_edge_index)
    out = model.decode(z, edge_index).sigmoid()
    preds = out.cpu().numpy()
    labels = edge_attr.cpu().numpy()
    
    thresholds = np.arange(0.3, 0.8, 0.05)
    best_f1 = 0
    best_threshold = 0.5
    
    print("\nThreshold optimization on validation set:")
    print("Thresh | Precision | Recall | F1-Score")
    print("-" * 45)
    
    for thresh in thresholds:
        binary_preds = (preds > thresh).astype(int)
        tp = ((binary_preds == 1) & (labels == 1)).sum()
        fp = ((binary_preds == 1) & (labels == 0)).sum()
        fn = ((binary_preds == 0) & (labels == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
        
        print(f"{thresh:.2f}   |   {precision:.4f}  |  {recall:.4f} | {f1:.4f}")
    
    print(f"\nOptimal threshold: {best_threshold:.2f} (F1: {best_f1:.4f})")
    return best_threshold

print("Training with moderate oversampling + class weighting...\n")
best_val_auc = 0
patience_counter = 0

for epoch in range(1, 301):
    loss = train()
    if epoch % 10 == 0:
        train_auc, train_ap, _, _, _ = test(train_edge_index, train_edge_attr)
        val_auc, val_ap, _, _, _ = test(val_edge_index, val_edge_attr)
        print(f'Epoch {epoch:03d}: Loss: {loss:.4f}, Train AUC: {train_auc:.4f}, Val AUC: {val_auc:.4f}')
        
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            patience_counter = 0
            torch.save(model.state_dict(), '../data/graphs/best_model_balanced.pt')
        else:
            patience_counter += 1
        if patience_counter >= 30:
            print(f"\nEarly stopping at epoch {epoch}")
            break

# Load best model
model.load_state_dict(torch.load('../data/graphs/best_model_balanced.pt'))

# Find optimal threshold
optimal_threshold = find_optimal_threshold(val_edge_index, val_edge_attr)

# Test with optimal threshold
@torch.no_grad()
def test_with_threshold(edge_index, edge_attr, threshold):
    model.eval()
    z = model.encode(x, train_edge_index)
    out = model.decode(z, edge_index).sigmoid()
    preds = out.cpu().numpy()
    labels = edge_attr.cpu().numpy()
    auc = roc_auc_score(labels, preds)
    ap = average_precision_score(labels, preds)
    binary_preds = (preds > threshold).astype(int)
    return auc, ap, preds, labels, binary_preds

test_auc, test_ap, test_preds, test_labels, test_binary = test_with_threshold(
    test_edge_index, test_edge_attr, optimal_threshold
)

print(f'\n=== FINAL RESULTS (Threshold={optimal_threshold:.2f}) ===')
print(f'Test AUC: {test_auc:.4f}')
print(f'Test AP: {test_ap:.4f}\n')
print(classification_report(test_labels, test_binary, target_names=['Related', 'Dependency']))

cm = confusion_matrix(test_labels, test_binary)
print(f'\nConfusion Matrix:')
print(f'              Predicted')
print(f'              Related  Dependency')
print(f'Actual Related    {cm[0][0]:4d}      {cm[0][1]:4d}')
print(f'       Dependency {cm[1][0]:4d}      {cm[1][1]:4d}')

# Dependency analysis
dep_mask = test_labels == 1
dep_preds = test_preds[dep_mask]
print(f'\nDependency prediction analysis:')
print(f'  Count: {dep_mask.sum()}')
print(f'  Mean score: {dep_preds.mean():.4f}')
print(f'  Correctly classified: {(dep_preds > optimal_threshold).sum()}/{len(dep_preds)} ({(dep_preds > optimal_threshold).sum()/len(dep_preds)*100:.1f}%)')