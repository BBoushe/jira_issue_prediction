import pickle
from tqdm import tqdm
from data_extraction import JiraMongoExtractor
from text_embedding import TextEmbedder

def main():
    """
    Connects to MongoDB, extracts issue text, generates embeddings,
    and saves them to a file.
    """
    print("Connecting to MongoDB...")
    # NOTE: You will need to update this URI for Colab, possibly using
    # a free MongoDB Atlas instance where you've restored the data.
    extractor = JiraMongoExtractor(uri="mongodb://localhost:27017", db_name="JiraRepos")
    
    # Fetch only the fields needed for embedding
    issues = extractor.fetch_issues(
        collection_name="Jira",
        query={},
        projection={"fields.summary": 1, "fields.description": 1, "id": 1, "key": 1}
    )
    extractor.close()
    print(f"Fetched {len(issues)} issues.")

    print("Initializing text embedder (this may download the model)...")
    # Use a GPU on Colab by setting device="cuda"
    embedder = TextEmbedder(model_name="bert-base-uncased", device="cuda")

    embeddings_map = {}
    
    # Process issues in batches for efficiency
    batch_size = 64
    for i in tqdm(range(0, len(issues), batch_size), desc="Generating embeddings"):
        batch_issues = issues[i:i + batch_size]
        texts_to_embed = []
        issue_ids = []

        for issue in batch_issues:
            summary = embedder._safe_get(issue, "fields.summary") or ""
            description = embedder._safe_get(issue, "fields.description") or ""
            combined_text = summary + " " + description
            
            issue_id = issue.get("id") or issue.get("key")
            if issue_id:
                texts_to_embed.append(combined_text)
                issue_ids.append(issue_id)

        if texts_to_embed:
            embeddings = embedder.encode_texts(texts_to_embed)
            for issue_id, embedding in zip(issue_ids, embeddings):
                embeddings_map[issue_id] = embedding

    # Save the embeddings map to a pickle file
    output_path = "/content/drive/MyDrive/ThePublicJiraDataset/jira_embeddings.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(embeddings_map, f, pickle.HIGHEST_PROTOCOL)
        
    print(f"Embeddings saved to {output_path}")

if __name__ == "__main__":
    main()