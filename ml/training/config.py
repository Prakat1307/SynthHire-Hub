
from dataclasses import dataclass, field
from typing import List

@dataclass
class DeBERTaTrainingConfig:

    model_name: str = "microsoft/deberta-v3-base"
    num_labels: int = 8
    max_length: int = 512
    
    num_epochs: int = 10
    batch_size: int = 16
    gradient_accumulation_steps: int = 1
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    
    fp16: bool = True
    max_grad_norm: float = 1.0
    
    logging_steps: int = 50
    eval_steps: int = 500
    save_steps: int = 500
    
    output_dir: str = "ml/models/deberta_interview_scorer"
    seed: int = 42
    
    label_names: List[str] = field(default_factory=lambda: [
        "technical_correctness",
        "problem_decomposition",
        "communication_clarity",
        "handling_ambiguity",
        "edge_case_awareness",
        "time_management",
        "collaborative_signals",
        "growth_mindset"
    ])