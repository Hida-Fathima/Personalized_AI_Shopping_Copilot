import numpy as np
from sentence_transformers import SentenceTransformer, util
import torch


class VectorMemory:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.memory_texts = []       # stored text messages
        self.memory_vectors = []     # stored embeddings (tensors)

    def _is_valid_embedding(self, emb):
        """Check if embedding is a valid vector."""
        try:
            return (
                isinstance(emb, torch.Tensor)
                and emb.dim() == 1
                and emb.numel() == 384    # MiniLM-L6 vector size
            )
        except:
            return False

    def add_memory(self, text):
        """Safely embed text and store."""
        text = text.strip()
        if not text:
            return

        try:
            embedding = self.model.encode(text, convert_to_tensor=True)

            if not self._is_valid_embedding(embedding):
                print(f"[VectorMemory] Invalid embedding dropped for text: {text}")
                return

            self.memory_texts.append(text)
            self.memory_vectors.append(embedding)

        except Exception as e:
            print(f"[VectorMemory] Error embedding '{text}':", e)

    def search_memory(self, query, top_k=2):
        """Semantic recall: find most similar stored memories."""
        query = query.strip()
        if not query:
            return []

        if not self.memory_vectors:
            return []

        try:
            query_vec = self.model.encode(query, convert_to_tensor=True)

            if not self._is_valid_embedding(query_vec):
                print("[VectorMemory] Invalid query embedding, skipping recall.")
                return []

            # Filter only valid vectors
            valid_vectors = [
                v for v in self.memory_vectors
                if self._is_valid_embedding(v)
            ]

            if not valid_vectors:
                return []

            scores = util.cos_sim(query_vec, valid_vectors)[0]
            top_results = scores.topk(k=min(top_k, len(valid_vectors)))

            recalled = []
            for score, idx in zip(top_results.values, top_results.indices):
                recalled.append(
                    (float(score), self.memory_texts[int(idx)])
                )

            return recalled

        except Exception as e:
            print("[VectorMemory] Recall error:", e)
            return []


vector_memory = VectorMemory()
