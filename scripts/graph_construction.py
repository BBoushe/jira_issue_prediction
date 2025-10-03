import networkx as nx
from tqdm import tqdm


def attach_embeddings_to_graph(G, text_embedder):
    """
    For each node in graph, extract the text from raw_data and store an embedding in node attributes.
    """
    nodes = list(G.nodes)

    for node in tqdm(nodes, desc="Attaching embeddings to graph"):
        issue_doc = G.nodes[node].get("raw_data", {})
        embedding = text_embedder.encode_issue_text(issue_doc)
        # Store in the node data
        G.nodes[node]["embedding"] = embedding


class GraphBuilder:
    def __init__(self, node_id_field="issue_id", link_type_field="fields.issuelinks"):
        """
        :param node_id_field: The field to use as a unique ID for each issue
        :param link_type_field: The path to the array of links
        """
        self.node_id_field = node_id_field
        self.link_type_field = link_type_field

    def build_graph(self, issues, dependency_link_types=None):
        """
        Builds a directed graph (NetworkX) from the given issues.

        :param issues: list of dicts from Mongo
        :param dependency_link_types: set or list of link types to treat as dependencies (label=1).
                                      All other links are labeled as related (label=0).
        """
        G = nx.DiGraph()

        for issue in tqdm(issues, desc="Building graph"):
            # Create a node for the issue, if not existing
            issue_id = self._extract_issue_id(issue)
            if issue_id is not None:
                G.add_node(issue_id, raw_data=issue)

                # Get the issue links, if any
                links = self._extract_links(issue)
                if links is None:
                    continue

                for link_obj in links:
                    link_type = link_obj.get("type", {}).get("name")
                    
                    # Label as 1 for dependency, 0 for related
                    if dependency_link_types and link_type in dependency_link_types:
                        edge_label = 1  # Dependency
                    else:
                        edge_label = 0  # Related

                    # Now figure out inward or outward
                    inward_issue = link_obj.get("inwardIssue")
                    outward_issue = link_obj.get("outwardIssue")

                    # If there's an inward issue, the edge is from inward->this issue
                    if inward_issue:
                        src = self._extract_issue_id(inward_issue)
                        dst = issue_id
                        if src and src != issue_id:
                            G.add_node(src)  # ensure node in graph
                            G.add_edge(src, dst, label=edge_label)

                    # If there's an outward issue, the edge is from this issue->outward
                    if outward_issue:
                        src = issue_id
                        dst = self._extract_issue_id(outward_issue)
                        if dst and dst != issue_id:
                            G.add_node(dst)  # ensure node in graph
                            G.add_edge(src, dst, label=edge_label)

        return G

    # Utility methods
    @staticmethod
    def _extract_issue_id(issue_doc):
        """
        Safely extract an issue's unique ID.
        Might be 'id', 'key', or something else depending on the doc structure.
        """
        return issue_doc.get("id") or issue_doc.get("key")

    @staticmethod
    def _extract_links(issue_doc):
        """
        Return the array of issue links from the doc if present.
        """
        fields = issue_doc.get("fields", {})
        return fields.get("issuelinks", [])