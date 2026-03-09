
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer, AutoConfig
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import json
import os

class DeBERTaInterviewScorer(nn.Module):

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        num_labels: int = 8,
        dropout: float = 0.1,
        hidden_size: int = 768,
        intermediate_size: int = 256,
    ):
        super().__init__()
        self.num_labels = num_labels
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.dropout_rate = dropout

        self.config = AutoConfig.from_pretrained(model_name)
        self.encoder = AutoModel.from_pretrained(model_name)
        
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, intermediate_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(intermediate_size, num_labels),
            nn.Sigmoid(),
        )

        self._init_weights()

    def _init_weights(self):

        for module in self.classifier:
            if isinstance(module, nn.Linear):
                
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        return_dict: bool = True,
    ) -> Union[Dict[str, torch.Tensor], Tuple[torch.Tensor, ...]]:

        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        cls_output = outputs.last_hidden_state[:, 0, :]  
        
        logits = self.classifier(cls_output)  
        
        result = {"logits": logits}
        
        if labels is not None:
            
            loss_fn = nn.BCELoss()
            loss = loss_fn(logits, labels.float())
            result["loss"] = loss
            
        if not return_dict:
            output = (logits,)
            if labels is not None:
                output = (loss,) + output
            return output
            
        return result

    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        device: str = "cpu"
    ) -> np.ndarray:

        self.eval()
        self.to(device)
        
        with torch.no_grad():
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            
            outputs = self.forward(input_ids, attention_mask)
            scores = outputs["logits"].cpu().numpy()
            
        return scores

    def save_pretrained(self, save_directory: str):

        os.makedirs(save_directory, exist_ok=True)
        
        torch.save(self.state_dict(), os.path.join(save_directory, "pytorch_model.bin"))
        
        config_dict = {
            "model_name": "microsoft/deberta-v3-base",
            "num_labels": self.num_labels,
            "dropout": self.dropout_rate,
            "hidden_size": self.hidden_size,
            "intermediate_size": self.intermediate_size,
        }
        with open(os.path.join(save_directory, "config.json"), "w") as f:
            json.dump(config_dict, f, indent=2)

    @classmethod
    def from_pretrained(cls, model_path: str):

        with open(os.path.join(model_path, "config.json"), "r") as f:
            config = json.load(f)
            
        model = cls(**config)
        
        state_dict = torch.load(
            os.path.join(model_path, "pytorch_model.bin"),
            map_location=torch.device("cpu")
        )
        model.load_state_dict(state_dict)
        
        return model

class DeBERTaInferenceWrapper:

    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        max_length: int = 512,
        batch_size: int = 32
    ):

        self.device = torch.device(device)
        self.max_length = max_length
        self.batch_size = batch_size
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        self.model = DeBERTaInterviewScorer.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        self.dimension_names = [
            "technical_correctness",
            "problem_decomposition", 
            "communication_clarity",
            "handling_ambiguity",
            "edge_case_awareness",
            "time_management",
            "collaborative_signals",
            "growth_mindset"
        ]

    def _tokenize_batch(self, texts: List[str]) -> Dict[str, torch.Tensor]:

        return self.tokenizer(
            texts,
            max_length=self.max_length,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

    def score(self, text: str) -> Dict[str, float]:

        inputs = self._tokenize_batch([text])
        
        with torch.no_grad():
            input_ids = inputs["input_ids"].to(self.device)
            attention_mask = inputs["attention_mask"].to(self.device)
            
            outputs = self.model(input_ids, attention_mask)
            scores = outputs["logits"][0].cpu().numpy()
            
        return {dim: float(score) for dim, score in zip(self.dimension_names, scores)}

    def score_batch(self, texts: List[str]) -> List[Dict[str, float]]:

        results = []
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            inputs = self._tokenize_batch(batch_texts)
            
            with torch.no_grad():
                input_ids = inputs["input_ids"].to(self.device)
                attention_mask = inputs["attention_mask"].to(self.device)
                
                outputs = self.model(input_ids, attention_mask)
                batch_scores = outputs["logits"].cpu().numpy()
                
            for scores in batch_scores:
                results.append({
                    dim: float(score) for dim, score in zip(self.dimension_names, scores)
                })
                
        return results

    def get_dimension_names(self) -> List[str]:

        return self.dimension_names.copy()

if __name__ == "__main__":
    
    model = DeBERTaInterviewScorer()
    print(f"Model created with {sum(p.numel() for p in model.parameters()):,} parameters")
    
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
    test_text = "This is a sample interview response."
    inputs = tokenizer(
        test_text,
        max_length=512,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
        print(f"Output shape: {outputs['logits'].shape}")
        print(f"Sample scores: {outputs['logits'][0].tolist()}")
    
    model.save_pretrained("test_model")
    loaded_model = DeBERTaInterviewScorer.from_pretrained("test_model")
    print("Model save/load test passed!")
    
    import shutil
    shutil.rmtree("test_model")