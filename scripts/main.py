from data_extraction import JiraMongoExtractor
from graph_construction import GraphBuilder, attach_embeddings_to_graph
from text_embedding import TextEmbedder
from torch_geometric.data import Data
import torch
import pickle


def main():
    # 1) Retrieve data from Mongo
    extractor = JiraMongoExtractor(uri="mongodb://localhost:27017", db_name="JiraRepos")
    issues = extractor.fetch_issues(
        collection_name="Jira",
        query={},  # or limit to certain issues
        projection={"fields.summary":1, "fields.description":1, "fields.issuelinks":1, "id":1, "key":1}
    )
    extractor.close()

    # 2) Build the graph
    # Suppose we unify all "dependency-like" links. You might define them externally:
    chosen_link_types = {"Block", "Blocks", "Depend", "Depends", "Dependency", "Blocker", "dependent"}
    builder = GraphBuilder()
    G = builder.build_graph(issues, chosen_link_types=chosen_link_types)

    # 3) Embed text
    embedder = TextEmbedder(model_name="bert-base-uncased", device="cpu")
    attach_embeddings_to_graph(G, embedder)

    # Save the constructed graph to a pickle file
    with open("/Users/alek/Developer/Programming/WBS/jira_graph_prediction/data/graphs/graph.gpickle", 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

    # Return the constructed graph for further processing
    return G


def networkx_to_pyg(G):
    # Sort nodes so we can assign consistent indices
    node_list = list(G.nodes())
    node_index_map = {node_id: i for i, node_id in enumerate(node_list)}

    # Build node feature matrix
    features = []
    for node_id in node_list:
        emb = G.nodes[node_id].get("embedding", None)
        if emb is None:
            emb = [0.0] * 768  # or however large your embedding is
        features.append(emb)
    x = torch.tensor(features, dtype=torch.float)

    # Build edge list
    edges_src = []
    edges_dst = []
    for src, dst in G.edges():
        edges_src.append(node_index_map[src])
        edges_dst.append(node_index_map[dst])

    edge_index = torch.tensor([edges_src, edges_dst], dtype=torch.long)

    data = Data(x=x, edge_index=edge_index)

    # Save the geometric graph
    with open("/Users/alek/Developer/Programming/WBS/jira_graph_prediction/data/graphs/graph_data.pkl", "wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    return data


if __name__ == "__main__":
    G = main()
    pyg_data = networkx_to_pyg(G)
    print(pyg_data)