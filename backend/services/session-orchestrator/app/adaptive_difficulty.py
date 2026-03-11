from typing import Dict, List, Optional

class AdaptiveDifficultyController:

    def __init__(self, initial_difficulty: int=5, persona_type: str='kind_mentor'):
        self.current_difficulty = initial_difficulty
        self.persona_type = persona_type
        self.score_history: List[float] = []

    def update(self, dimension_scores: Dict[str, float]) -> dict:
        performance = self._calculate_performance_signal(dimension_scores)
        self.score_history.append(performance)
        recent = self.score_history[-3:]
        rolling_avg = sum(recent) / len(recent)
        delta = 0
        action = 'continue_normal_flow'
        if rolling_avg > 0.85:
            delta = 1
            action = 'ask_deeper_follow_up'
        elif rolling_avg > 0.7:
            delta = 0
            action = 'continue_normal_flow'
        elif rolling_avg > 0.5:
            delta = 0
            action = 'give_subtle_hint' if self.persona_type in ['kind_mentor', 'collaborative_peer'] else 'rephrase_question'
        else:
            delta = -1
            action = 'simplify_or_hint'
        if self.persona_type == 'tough_lead':
            delta = max(delta, 0)
            if action == 'give_subtle_hint':
                action = 'probe_deeper'
        elif self.persona_type == 'kind_mentor' and delta < 0:
            action = 'encourage_and_hint'
        elif self.persona_type == 'silent_observer':
            action = 'continue_normal_flow'
        self.current_difficulty = max(1, min(10, self.current_difficulty + delta))
        return {'new_difficulty': self.current_difficulty, 'delta': delta, 'action': action, 'rolling_performance': rolling_avg}

    def _calculate_performance_signal(self, scores: Dict[str, float]) -> float:
        weights = {'technical_correctness': 0.3, 'problem_decomposition': 0.25, 'communication_clarity': 0.15, 'edge_case_awareness': 0.15, 'handling_ambiguity': 0.15}
        total = 0.0
        weight_sum = 0.0
        for dim, weight in weights.items():
            if dim in scores:
                total += scores[dim] * weight
                weight_sum += weight
        return total / weight_sum if weight_sum > 0 else 0.5