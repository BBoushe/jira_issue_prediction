import torch
import pickle
from torch_geometric.utils import train_test_split_edges

# Load the graph data
with open("../data/graphs/graph_data.pkl", "rb") as f:
    data = pickle.load(f)

print(f"Total nodes: {data.x.shape[0]}")
print(f"Total edges: {data.edge_index.shape[1]}")
print(f"Dependency edges: {(data.edge_attr == 1).sum().item()} ({(data.edge_attr == 1).sum().item() / data.edge_index.shape[1] * 100:.2f}%)")
print(f"Related edges: {(data.edge_attr == 0).sum().item()} ({(data.edge_attr == 0).sum().item() / data.edge_index.shape[1] * 100:.2f}%)")

# Separate dependency and related edges for stratified split
dep_mask = data.edge_attr == 1
rel_mask = data.edge_attr == 0

dep_edges = data.edge_index[:, dep_mask]
rel_edges = data.edge_index[:, rel_mask]

# Split 70/15/15 for each type
def split_edges(edge_index, split_ratio=[0.7, 0.15, 0.15]):
    num_edges = edge_index.shape[1]
    perm = torch.randperm(num_edges)
    
    train_end = int(split_ratio[0] * num_edges)
    val_end = train_end + int(split_ratio[1] * num_edges)
    
    train_idx = perm[:train_end]
    val_idx = perm[train_end:val_end]
    test_idx = perm[val_end:]
    
    return train_idx, val_idx, test_idx

dep_train_idx, dep_val_idx, dep_test_idx = split_edges(dep_edges)
rel_train_idx, rel_val_idx, rel_test_idx = split_edges(rel_edges)

# Combine splits
train_edge_index = torch.cat([dep_edges[:, dep_train_idx], rel_edges[:, rel_train_idx]], dim=1)
train_edge_attr = torch.cat([torch.ones(len(dep_train_idx)), torch.zeros(len(rel_train_idx))]).long()

val_edge_index = torch.cat([dep_edges[:, dep_val_idx], rel_edges[:, rel_val_idx]], dim=1)
val_edge_attr = torch.cat([torch.ones(len(dep_val_idx)), torch.zeros(len(rel_val_idx))]).long()

test_edge_index = torch.cat([dep_edges[:, dep_test_idx], rel_edges[:, rel_test_idx]], dim=1)
test_edge_attr = torch.cat([torch.ones(len(dep_test_idx)), torch.zeros(len(rel_test_idx))]).long()

print("\n=== STRATIFIED SPLIT ===")
print(f"Train: {train_edge_index.shape[1]} edges ({(train_edge_attr == 1).sum().item()} dep, {(train_edge_attr == 0).sum().item()} rel)")
print(f"Val: {val_edge_index.shape[1]} edges ({(val_edge_attr == 1).sum().item()} dep, {(val_edge_attr == 0).sum().item()} rel)")
print(f"Test: {test_edge_index.shape[1]} edges ({(test_edge_attr == 1).sum().item()} dep, {(test_edge_attr == 0).sum().item()} rel)")

# Save splits
torch.save({
    'x': data.x,
    'train_edge_index': train_edge_index,
    'train_edge_attr': train_edge_attr,
    'val_edge_index': val_edge_index,
    'val_edge_attr': val_edge_attr,
    'test_edge_index': test_edge_index,
    'test_edge_attr': test_edge_attr,
}, '../data/graphs/train_val_test_split.pt')

print("\nSplit saved to '../data/graphs/train_val_test_split.pt'")