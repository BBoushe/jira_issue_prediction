from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np


class TextEmbedder:
    def __init__(self, model_name="bert-base-uncased", device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(device)
        self.device = device

    def encode_texts(self, texts):
        """
        Encodes a list of strings into a list of vector embeddings using a transformer model.
        :returns numpy array of shape (len(texts), embedding_dim).
        """
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**encodings)
            # Typically, the [CLS] token embedding is at index 0
            # Or you can do a mean pooling of the last hidden states for the entire sequence
            # Here we'll do a simple CLS pooling:
            cls_embeddings = outputs.last_hidden_state[:, 0, :]

        return cls_embeddings.cpu().numpy()

    def encode_issue_text(self, issue_doc, summary_field="fields.summary", desc_field="fields.description"):
        """
        Grab summary & description from the issue_doc, then generate a single combined embedding.
        """
        summary = self._safe_get(issue_doc, summary_field)
        description = self._safe_get(issue_doc, desc_field)
        combined_text = (summary or "") + " " + (description or "")

        # You can do more sophisticated approaches here
        embeddings = self.encode_texts([combined_text])
        return embeddings[0]  # shape (embedding_dim,)

    @staticmethod
    def _safe_get(doc, path_str):
        """
        If path_str = "fields.description", safely go doc["fields"]["description"]
        If a field is missing, return None.
        """
        parts = path_str.split(".")
        current = doc
        for p in parts:
            if isinstance(current, dict) and p in current:
                current = current[p]
            else:
                return None
        return current