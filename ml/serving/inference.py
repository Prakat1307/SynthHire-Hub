
import os
import json
import numpy as np
from typing import Dict, Optional, List, Union
from datetime import datetime

from ml.models.deberta_classifier import DeBERTaInferenceWrapper
from ml.models.embedding_scorer import EmbeddingScorer
from ml.models.ensemble import ScoreEnsemble
from ml.models.emotion_analyzer import EmotionAnalysisPipeline

class MLInferencePipeline:

    def __init__(
        self,
        deberta_model_path: str = None,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        use_gpu: bool = False,
        device: str = None,
    ):

        if device is None:
            if use_gpu:
                device = "cuda" if self._is_cuda_available() else "cpu"
            else:
                device = "cpu"
        self.device = device

        self.deberta = None
        if deberta_model_path and os.path.exists(deberta_model_path):
            try:
                self.deberta = DeBERTaInferenceWrapper(
                    model_path=deberta_model_path,
                    device=self.device
                )
                print("✅ DeBERTa model loaded")
            except Exception as e:
                print(f"⚠️ DeBERTa not loaded: {e}")

        self.embedding_scorer = EmbeddingScorer(
            model_name=embedding_model_name,
            device=self.device
        )

        self.ensemble = ScoreEnsemble()

        self.inference_count = 0
        self.total_latency_ms = 0.0

    def _is_cuda_available(self) -> bool:

        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def score_response(
        self,
        candidate_response: str,
        gpt4o_scores: Optional[Dict[str, float]] = None,
        ideal_responses: Optional[List[str]] = None,
        behavioral_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Union[Dict[str, float], float, List[float]]]:

        import time
        start_time = time.time()

        results = {}

        if self.deberta:
            deberta_scores = self.deberta.score(candidate_response)
        else:
            
            if gpt4o_scores is None:
                gpt4o_scores = {dim: 0.5 for dim in self.ensemble.dimension_names}
            deberta_scores = gpt4o_scores
        results["deberta_scores"] = deberta_scores

        if gpt4o_scores is None:
            gpt4o_scores = {dim: 0.5 for dim in self.ensemble.dimension_names}
        results["gpt4o_scores"] = gpt4o_scores

        if ideal_responses:
            embed_result = self.embedding_scorer.score_response(candidate_response, ideal_responses)
            embedding_quality = embed_result["quality_score"]
            results["embedding_similarity"] = embed_result["similarity"]
            results["embedding_quality"] = embedding_quality
            results["candidate_embedding"] = embed_result["candidate_embedding"]
        else:
            embedding_quality = 0.5
            results["embedding_similarity"] = 0.5
            results["embedding_quality"] = 0.5

        if behavioral_scores is None:
            behavioral_scores = {dim: 0.5 for dim in self.ensemble.dimension_names}
        results["behavioral_scores"] = behavioral_scores

        combined = self.ensemble.combine_scores(
            deberta_scores=deberta_scores,
            gpt4o_scores=gpt4o_scores,
            embedding_score=embedding_quality,
            behavioral_scores=behavioral_scores,
        )
        results["ensemble_scores"] = combined

        latency_ms = (time.time() - start_time) * 1000
        self.inference_count += 1
        self.total_latency_ms += latency_ms

        return results

    def aggregate_session(
        self,
        exchange_scores: List[Dict[str, float]],
        session_type: str = "coding",
    ) -> Dict[str, Union[Dict[str, float], float]]:

        session_scores = self.ensemble.aggregate_session_scores(exchange_scores)
        overall = self.ensemble.calculate_overall_score(session_scores, session_type)

        return {
            "dimension_scores": session_scores,
            "overall_score": overall,
        }

    def get_metrics(self) -> Dict[str, float]:

        avg_latency = self.total_latency_ms / max(self.inference_count, 1)
        return {
            "inference_count": self.inference_count,
            "avg_latency_ms": round(avg_latency, 2),
            "total_latency_ms": round(self.total_latency_ms, 2),
        }

    def reset_metrics(self):

        self.inference_count = 0
        self.total_latency_ms = 0.0

    def get_dimension_names(self) -> List[str]:

        return self.ensemble.dimension_names.copy()

    def get_ensemble_weights(self) -> Dict[str, float]:

        return self.ensemble.get_weights()

    def set_ensemble_weights(
        self,
        deberta_weight: Optional[float] = None,
        gpt4o_weight: Optional[float] = None,
        embedding_weight: Optional[float] = None,
        behavioral_weight: Optional[float] = None,
    ):

        self.ensemble.set_weights(
            deberta_weight=deberta_weight,
            gpt4o_weight=gpt4o_weight,
            embedding_weight=embedding_weight,
            behavioral_weight=behavioral_weight,
        )

if __name__ == "__main__":
    
    pipeline = MLInferencePipeline()
    
    candidate = "I solved this using dynamic programming with O(n) space complexity."
    ideals = ["Used dynamic programming approach with optimal space complexity."]
    gpt4o = {dim: 0.8 for dim in pipeline.get_dimension_names()}
    behavioral = {dim: 0.9 for dim in pipeline.get_dimension_names()}
    
    result = pipeline.score_response(
        candidate_response=candidate,
        gpt4o_scores=gpt4o,
        ideal_responses=ideals,
        behavioral_scores=behavioral,
    )
    
    print("Scoring result:")
    print(f"  DeBERTa: {result['deberta_scores']}")
    print(f"  GPT-4o: {result['gpt4o_scores']}")
    print(f"  Embedding similarity: {result['embedding_similarity']:.3f}")
    print(f"  Behavioral: {result['behavioral_scores']}")
    print(f"  Ensemble: {result['ensemble_scores']}")
    
    exchanges = [
        result['ensemble_scores'],
        {dim: score * 0.9 for dim, score in result['ensemble_scores'].items()},
        {dim: score * 1.1 for dim, score in result['ensemble_scores'].items()},
    ]
    session_result = pipeline.aggregate_session(exchanges, "coding")
    print(f"\nSession result: {session_result}")
    
    print(f"\nMetrics: {pipeline.get_metrics()}")