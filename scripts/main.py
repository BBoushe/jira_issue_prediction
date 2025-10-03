from data_extraction import JiraMongoExtractor
from graph_construction import GraphBuilder
import networkx as nx
from torch_geometric.data import Data
import torch
import pickle

def extract_largest_component(G):
    """Extract only the largest connected component"""
    G_undirected = G.to_undirected()
    largest_cc = max(nx.connected_components(G_undirected), key=len)
    
    # Create subgraph with only largest component
    G_largest = G.subgraph(largest_cc).copy()
    
    dependency_count = sum(1 for _, _, d in G_largest.edges(data=True) if d.get('label', 0) == 1)
    related_count = sum(1 for _, _, d in G_largest.edges(data=True) if d.get('label', 0) == 0)
    
    print(f"\n=== LARGEST COMPONENT ===")
    print(f"Nodes: {G_largest.number_of_nodes()}")
    print(f"Edges: {G_largest.number_of_edges()}")
    print(f"Dependency edges: {dependency_count} ({dependency_count/G_largest.number_of_edges()*100:.2f}%)")
    print(f"Related edges: {related_count} ({related_count/G_largest.number_of_edges()*100:.2f}%)")
    print(f"Average degree: {sum(dict(G_largest.degree()).values()) / G_largest.number_of_nodes():.2f}")
    print("=========================\n")
    
    return G_largest


def main():
    # 1) Retrieve data from Mongo - ONLY issues with links
    extractor = JiraMongoExtractor(uri="mongodb://localhost:27017", db_name="JiraRepos")
    issues = extractor.fetch_issues(
        collection_name="Jira",
        query={'fields.issuelinks': {'$exists': True, '$ne': []}},  # Only issues WITH links
        projection={'fields.issuelinks': 1, 'id': 1, 'key': 1}
    )
    extractor.close()

    print(f"Fetched {len(issues)} issues with links from database")

    # 2) Smart sampling - prioritize connected issues
    issues_with_links = [iss for iss in issues if iss.get('fields', {}).get('issuelinks')]
    print(f"Issues with links: {len(issues_with_links)}")

    sampled_issues = issues_with_links
    print(f"Using all {len(sampled_issues)} issues with links.")
    issues = sampled_issues

    # 3) Build the graph with REAL link types from your data
    # Dependency types (label = 1): Blocker, Depends, Follows, Cause
    # Everything else (label = 0): Reference, Duplicate, Cloners, Detail, Part, etc.
    dependency_link_types = {"Blocker", "Depends", "Follows", "Cause"}
    
    builder = GraphBuilder()
    G = builder.build_graph(issues, dependency_link_types)

    # 4) Load pre-computed embeddings and attach to graph nodes
    print("Loading pre-computed embeddings...")
    with open("../data/embeddings/jira_embeddings.pkl", "rb") as f:
        embeddings_map = pickle.load(f)

    default_embeddings_dim = 768  # bert-base-uncased
    default_embedding = [0.0] * default_embeddings_dim

    for node in G.nodes:
        embedding = embeddings_map.get(node, default_embedding)
        G.nodes[node]["embedding"] = embedding

    # 5) Save the constructed graph to a pickle file
    with open("../data/graphs/graph_with_embeddings.gpickle", 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

    # 6) Extract and print detailed graph statistics
    print("\n=== GRAPH STATISTICS ===")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")

    # Extract largest connected component only
    print("Extracting largest connected component...")
    G = extract_largest_component(G)

    # 7) Convert to PyTorch Geometric format
    pyg_data = networkx_to_pyg(G)
    print(pyg_data)
    
    return G


def networkx_to_pyg(G):
    # Sort nodes for consistent indexing
    node_list = list(G.nodes())
    node_index_map = {node_id: i for i, node_id in enumerate(node_list)}

    # Build node feature matrix
    features = []
    for node_id in node_list:
        emb = G.nodes[node_id].get("embedding", None)
        if emb is None:
            emb = [0.0] * 768
        features.append(emb)
    
    # Convert to tensor (fix the warning by converting to numpy first)
    import numpy as np
    features_array = np.array(features)
    x = torch.tensor(features_array, dtype=torch.float)

    # Build edge list with labels
    edges_src = []
    edges_dst = []
    edge_labels = []
    
    for src, dst, data in G.edges(data=True):
        edges_src.append(node_index_map[src])
        edges_dst.append(node_index_map[dst])
        edge_labels.append(data.get('label', 0))

    edge_index = torch.tensor([edges_src, edges_dst], dtype=torch.long)
    edge_attr = torch.tensor(edge_labels, dtype=torch.long)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    # Save the geometric graph
    with open("../data/graphs/graph_data.pkl", "wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    return data


if __name__ == "__main__":
    G = main()