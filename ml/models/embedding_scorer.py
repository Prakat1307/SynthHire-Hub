
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
import json
import os

class EmbeddingScorer:

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        max_length: int = 256
    ):

        print(f"📐 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = device
        
        print(f"  Embedding dimension: {self.embedding_dim}")
        print(f"  Device: {device}")

    def encode(self, text: str) -> np.ndarray:

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding

    def encode_batch(self, texts: List[str]) -> np.ndarray:

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings

    def cosine_similarity(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:

        return float(np.dot(embedding_a, embedding_b))

    def score_response(
        self,
        candidate_response: str,
        ideal_responses: List[str],
        question_embedding: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:

        if not ideal_responses:
            return {
                "similarity": 0.5,
                "avg_similarity": 0.5,
                "quality_score": 0.5,
                "candidate_embedding": self.encode(candidate_response).tolist()
            }

        candidate_emb = self.encode(candidate_response)

        ideal_embs = self.encode_batch(ideal_responses)

        similarities = [
            self.cosine_similarity(candidate_emb, ideal_emb)
            for ideal_emb in ideal_embs
        ]

        max_similarity = max(similarities)
        avg_similarity = np.mean(similarities)

        quality_score = self._similarity_to_quality(max_similarity)

        return {
            "similarity": float(max_similarity),
            "avg_similarity": float(avg_similarity),
            "quality_score": float(quality_score),
            "candidate_embedding": candidate_emb.tolist(),
        }

    def _similarity_to_quality(self, similarity: float) -> float:

        if similarity >= 0.85:
            
            return 0.85 + (similarity - 0.85) * 1.0
        elif similarity >= 0.70:
            
            return 0.65 + (similarity - 0.70) * (0.2 / 0.15)
        elif similarity >= 0.50:
            
            return 0.40 + (similarity - 0.50) * (0.25 / 0.20)
        else:
            
            return max(0.10, similarity * 0.60)

    def precompute_question_embeddings(
        self,
        questions: List[Dict],
        output_path: str = "ml/data/embeddings/question_embeddings.npz",
    ):

        print("🔄 Pre-computing question embeddings...")

        all_embeddings = {}
        for q in questions:
            q_id = str(q.get("id", ""))
            ideal_texts = q.get("ideal_response_texts", [])

            if ideal_texts:
                embs = self.encode_batch(ideal_texts)
                all_embeddings[q_id] = embs

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.savez_compressed(output_path, **{k: v for k, v in all_embeddings.items()})
        print(f"✅ Saved embeddings for {len(all_embeddings)} questions → {output_path}")

    def load_question_embeddings(self, path: str):

        data = np.load(path, allow_pickle=True)
        self.ideal_embeddings_cache = {k: data[k] for k in data.files}
        print(f"📂 Loaded {len(self.ideal_embeddings_cache)} question embeddings")

    def find_similar_questions(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:

        if not hasattr(self, 'ideal_embeddings_cache'):
            raise ValueError("Question embeddings not loaded. Call load_question_embeddings() first.")
            
        similarities = []
        for q_id, ideal_embs in self.ideal_embeddings_cache.items():
            
            sim_scores = [self.cosine_similarity(query_embedding, emb) for emb in ideal_embs]
            max_sim = max(sim_scores) if sim_scores else 0.0
            similarities.append((q_id, max_sim))
            
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_embedding_dimension(self) -> int:

        return self.embedding_dim

if __name__ == "__main__":
    
    scorer = EmbeddingScorer()
    
    emb = scorer.encode("Hello world!")
    print(f"Embedding shape: {emb.shape}")
    print(f"Embedding norm: {np.linalg.norm(emb):.6f}")  
    
    texts = ["Hello", "World", "Machine learning"]
    embs = scorer.encode_batch(texts)
    print(f"Batch embeddings shape: {embs.shape}")
    
    sim = scorer.cosine_similarity(emb, embs[0])
    print(f"Similarity: {sim:.4f}")
    
    candidate = "I solved the problem using dynamic programming"
    ideals = [
        "Used dynamic programming to solve the optimization problem",
        "Applied DP approach with memoization for efficiency"
    ]
    result = scorer.score_response(candidate, ideals)
    print(f"Score result: {result}")