
import numpy as np
from typing import Dict, List, Optional
from sklearn.isotonic import IsotonicRegression
import json
import os
import pickle

class ScoreEnsemble:

    def __init__(
        self,
        deberta_weight: float = 0.40,
        gpt4o_weight: float = 0.35,
        embedding_weight: float = 0.15,
        behavioral_weight: float = 0.10,
        dimension_names: Optional[List[str]] = None
    ):

        self.deberta_weight = deberta_weight
        self.gpt4o_weight = gpt4o_weight
        self.embedding_weight = embedding_weight
        self.behavioral_weight = behavioral_weight
        
        self.dimension_names = dimension_names or [
            "technical_correctness",
            "problem_decomposition",
            "communication_clarity", 
            "handling_ambiguity",
            "edge_case_awareness",
            "time_management",
            "collaborative_signals",
            "growth_mindset"
        ]
        
        self.calibrators: Dict[str, IsotonicRegression] = {}

    def combine_scores(
        self,
        deberta_scores: Dict[str, float],
        gpt4o_scores: Dict[str, float],
        embedding_score: float,
        behavioral_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:

        combined = {}

        for dim in self.dimension_names:
            
            deberta_val = deberta_scores.get(dim, 0.5)
            gpt4o_val = gpt4o_scores.get(dim, 0.5)
            embedding_val = embedding_score  
            behavioral_val = behavioral_scores.get(dim, 0.5) if behavioral_scores else 0.5

            raw_score = (
                self.deberta_weight * deberta_val
                + self.gpt4o_weight * gpt4o_val
                + self.embedding_weight * embedding_val
                + self.behavioral_weight * behavioral_val
            )

            if dim in self.calibrators:
                calibrated = self.calibrators[dim].predict([raw_score])[0]
                combined[dim] = float(np.clip(calibrated, 0.0, 1.0))
            else:
                combined[dim] = float(np.clip(raw_score, 0.0, 1.0))

        return combined

    def aggregate_session_scores(
        self,
        exchange_scores: List[Dict[str, float]],
    ) -> Dict[str, float]:

        if not exchange_scores:
            return {dim: 0.0 for dim in self.dimension_names}

        n = len(exchange_scores)
        weights = [0.5 + 0.5 * (i / n) for i in range(n)]
        weight_sum = sum(weights)

        session_scores = {}
        for dim in self.dimension_names:
            weighted_sum = sum(
                weights[i] * exchange_scores[i].get(dim, 0.0) for i in range(n)
            )
            session_scores[dim] = float(weighted_sum / weight_sum)

        return session_scores

    def calculate_overall_score(
        self,
        dimension_scores: Dict[str, float],
        session_type: str = "coding",
        dimension_weights: Optional[Dict[str, float]] = None
    ) -> float:

        if dimension_weights is None:
            
            if session_type == "coding":
                weights = {
                    "technical_correctness": 0.25,
                    "problem_decomposition": 0.20,
                    "communication_clarity": 0.15,
                    "handling_ambiguity": 0.10,
                    "edge_case_awareness": 0.15,
                    "time_management": 0.05,
                    "collaborative_signals": 0.05,
                    "growth_mindset": 0.05,
                }
            elif session_type == "behavioral":
                weights = {
                    "technical_correctness": 0.05,
                    "problem_decomposition": 0.10,
                    "communication_clarity": 0.25,
                    "handling_ambiguity": 0.10,
                    "edge_case_awareness": 0.05,
                    "time_management": 0.05,
                    "collaborative_signals": 0.20,
                    "growth_mindset": 0.20,
                }
            elif session_type == "system_design":
                weights = {
                    "technical_correctness": 0.20,
                    "problem_decomposition": 0.25,
                    "communication_clarity": 0.15,
                    "handling_ambiguity": 0.15,
                    "edge_case_awareness": 0.10,
                    "time_management": 0.05,
                    "collaborative_signals": 0.05,
                    "growth_mindset": 0.05,
                }
            else:  
                weights = {
                    "technical_correctness": 0.15,
                    "problem_decomposition": 0.15,
                    "communication_clarity": 0.15,
                    "handling_ambiguity": 0.15,
                    "edge_case_awareness": 0.10,
                    "time_management": 0.10,
                    "collaborative_signals": 0.10,
                    "growth_mindset": 0.10,
                }
        else:
            weights = dimension_weights

        overall = sum(
            dimension_scores.get(dim, 0.0) * weight
            for dim, weight in weights.items()
        )

        return float(np.clip(overall * 100, 0.0, 100.0))

    def fit_calibrators(
        self,
        raw_scores: List[Dict[str, float]],
        true_scores: List[Dict[str, float]],
    ):

        for dim in self.dimension_names:
            raw_vals = np.array([s.get(dim, 0.5) for s in raw_scores])
            true_vals = np.array([s.get(dim, 0.5) for s in true_scores])

            if np.std(true_vals) > 0.01:
                calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
                calibrator.fit(raw_vals, true_vals)
                self.calibrators[dim] = calibrator
            else:
                
                pass

        print(f"✅ Fitted calibrators for {len(self.calibrators)} dimensions")

    def save_calibrators(self, path: str = "ml/models/calibrators.pkl"):

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.calibrators, f)
        print(f"💾 Calibrators saved to {path}")

    def load_calibrators(self, path: str = "ml/models/calibrators.pkl"):

        if os.path.exists(path):
            with open(path, "rb") as f:
                self.calibrators = pickle.load(f)
            print(f"📂 Calibrators loaded from {path}")
        else:
            print(f"⚠️ Calibrators file not found: {path}")

    def get_weights(self) -> Dict[str, float]:

        return {
            "deberta": self.deberta_weight,
            "gpt4o": self.gpt4o_weight,
            "embedding": self.embedding_weight,
            "behavioral": self.behavioral_weight,
        }

    def set_weights(
        self,
        deberta_weight: Optional[float] = None,
        gpt4o_weight: Optional[float] = None,
        embedding_weight: Optional[float] = None,
        behavioral_weight: Optional[float] = None,
    ):

        weights = [
            deberta_weight or self.deberta_weight,
            gpt4o_weight or self.gpt4o_weight,
            embedding_weight or self.embedding_weight,
            behavioral_weight or self.behavioral_weight,
        ]
        
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
            
        self.deberta_weight = weights[0]
        self.gpt4o_weight = weights[1]
        self.embedding_weight = weights[2]
        self.behavioral_weight = weights[3]
        
        print(f"🔄 Updated ensemble weights: {self.get_weights()}")

if __name__ == "__main__":
    
    ensemble = ScoreEnsemble()
    
    deberta = {dim: 0.8 for dim in ensemble.dimension_names}
    gpt4o = {dim: 0.7 for dim in ensemble.dimension_names}
    behavioral = {dim: 0.9 for dim in ensemble.dimension_names}
    
    combined = ensemble.combine_scores(deberta, gpt4o, 0.75, behavioral)
    print(f"Combined scores: {combined}")
    
    exchanges = [
        {dim: 0.6 for dim in ensemble.dimension_names},
        {dim: 0.7 for dim in ensemble.dimension_names},
        {dim: 0.8 for dim in ensemble.dimension_names},
    ]
    session_scores = ensemble.aggregate_session_scores(exchanges)
    print(f"Session scores: {session_scores}")
    
    overall = ensemble.calculate_overall_score(session_scores, "coding")
    print(f"Overall score: {overall:.1f}%")