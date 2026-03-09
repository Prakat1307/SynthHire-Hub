
import torch
import onnx
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
import os
from typing import Dict, List
import json
import time

from ml.models.deberta_classifier import DeBERTaInterviewScorer

class ONNXExporter:

    @staticmethod
    def export_deberta(
        model: DeBERTaInterviewScorer,
        tokenizer: AutoTokenizer,
        output_path: str,
        max_length: int = 512,
        opset_version: int = 14,
        quantize: bool = True,
    ):

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        model.eval()
        model.cpu()

        dummy_text = "This is a sample interview response for export."
        inputs = tokenizer(
            dummy_text,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        dynamic_axes = {
            "input_ids": {0: "batch_size"},
            "attention_mask": {0: "batch_size"},
            "output": {0: "batch_size"},
        }

        torch.onnx.export(
            model,
            (inputs["input_ids"], inputs["attention_mask"]),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
        )

        print(f"✅ ONNX model exported → {output_path}")

        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        print("✅ ONNX model validated")

        if quantize:
            from onnxruntime.quantization import quantize_dynamic, QuantType
            quantized_path = output_path.replace(".onnx", "_quantized.onnx")
            quantize_dynamic(
                output_path,
                quantized_path,
                weight_type=QuantType.QInt8,
            )
            print(f"✅ Quantized model → {quantized_path}")
            return quantized_path

        return output_path

    @staticmethod
    def export_sentence_transformer(
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        output_path: str = "ml/models/onnx/sentence_transformer.onnx",
        max_length: int = 256,
    ):

        from sentence_transformers import SentenceTransformer

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        st_model = SentenceTransformer(model_name)

        transformer = st_model[0].auto_model
        tokenizer = st_model[0].tokenizer
        transformer.eval()

        dummy = tokenizer(
            "sample text",
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        torch.onnx.export(
            transformer,
            (dummy["input_ids"], dummy["attention_mask"]),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["last_hidden_state"],
            dynamic_axes={
                "input_ids": {0: "batch", 1: "sequence"},
                "attention_mask": {0: "batch", 1: "sequence"},
                "last_hidden_state": {0: "batch", 1: "sequence"},
            },
            opset_version=14,
        )
        print(f"✅ Sentence-transformer ONNX exported → {output_path}")
        return output_path