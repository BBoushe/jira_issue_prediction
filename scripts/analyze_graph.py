import pickle
import networkx as nx
from collections import Counter

with open("../data/graphs/graph_with_embeddings.gpickle", "rb") as f:
    G = pickle.load(f)

G_undirected = G.to_undirected()
components = list(nx.connected_components(G_undirected))
component_sizes = sorted([len(c) for c in components], reverse=True)

print(f"Total components: {len(components)}")
print(f"Top 10 component sizes: {component_sizes[:10]}")
print(f"Components with >100 nodes: {sum(1 for s in component_sizes if s > 100)}")
print(f"Components with 10-100 nodes: {sum(1 for s in component_sizes if 10 <= s <= 100)}")
print(f"Components with <10 nodes: {sum(1 for s in component_sizes if s < 10)}")