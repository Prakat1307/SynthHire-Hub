
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from typing import Dict, List, Optional, Tuple
import asyncio
import hashlib
import json
import time
import os
from dataclasses import dataclass, field
from collections import deque

@dataclass
class InferenceRequest:

    text: str
    request_id: str
    future: asyncio.Future
    timestamp: float = field(default_factory=time.time)

class ONNXModelServer:

    def __init__(
        self,
        model_path: str,
        tokenizer_path: str,
        model_type: str = "deberta",  
        max_batch_size: int = 8,
        max_wait_ms: int = 50,
        use_gpu: bool = False,
        redis_client = None,
        cache_ttl: int = 3600,  
    ):
        self.model_type = model_type
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.cache_ttl = cache_ttl
        self.redis = redis_client

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4
        sess_options.inter_op_num_threads = 2

        self.session = ort.InferenceSession(model_path, sess_options, providers=providers)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

        self._batch_queue: deque[InferenceRequest] = deque()
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None

        self._inference_count = 0
        self._total_latency_ms = 0.0
        self._cache_hits = 0
        self._cache_misses = 0

        print(f"✅ ONNX {model_type} server loaded: {model_path}")
        print(f"   Providers: {self.session.get_providers()}")
        print(f"   Batch: max_size={max_batch_size}, max_wait={max_wait_ms}ms")

    async def predict(self, text: str) -> np.ndarray:

        cache_key = self._cache_key(text)
        if self.redis:
            cached = await self._get_cached(cache_key)
            if cached is not None:
                self._cache_hits += 1
                return cached

        self._cache_misses += 1

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        request = InferenceRequest(
            text=text,
            request_id=cache_key,
            future=future,
        )

        async with self._batch_lock:
            self._batch_queue.append(request)

            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_batch())

        result = await future

        if self.redis:
            await self._set_cached(cache_key, result)

        return result

    async def predict_batch(self, texts: List[str]) -> List[np.ndarray]:

        results = []
        
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if self.redis:
                cached = await self._get_cached(cache_key)
                if cached is not None:
                    results.append((i, cached))
                    self._cache_hits += 1
                    continue

            self._cache_misses += 1
            uncached_indices.append(i)
            uncached_texts.append(text)

        if uncached_texts:
            batch_results = self._run_inference(uncached_texts)
            for idx, result in zip(uncached_indices, batch_results):
                results.append((idx, result))
                
                if self.redis:
                    cache_key = self._cache_key(texts[idx])
                    await self._set_cached(cache_key, result)

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    async def _process_batch(self):

        await asyncio.sleep(self.max_wait_ms / 1000.0)

        async with self._batch_lock:
            if not self._batch_queue:
                return

            batch: List[InferenceRequest] = []
            while self._batch_queue and len(batch) < self.max_batch_size:
                batch.append(self._batch_queue.popleft())

        if not batch:
            return

        texts = [req.text for req in batch]
        start = time.time()
        
        try:
            results = self._run_inference(texts)
            latency_ms = (time.time() - start) * 1000
            self._inference_count += len(batch)
            self._total_latency_ms += latency_ms

            for req, result in zip(batch, results):
                if not req.future.done():
                    req.future.set_result(result)
        except Exception as e:
            for req in batch:
                if not req.future.done():
                    req.future.set_exception(e)

        if self._batch_queue:
            self._batch_task = asyncio.create_task(self._process_batch())

    def _run_inference(self, texts: List[str]) -> List[np.ndarray]:

        if self.model_type == "deberta":
            max_len = 512
        else:
            max_len = 256

        inputs = self.tokenizer(
            texts,
            max_length=max_len,
            padding=True,
            truncation=True,
            return_tensors="np",
        )

        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }

        outputs = self.session.run(None, ort_inputs)

        if self.model_type == "deberta":
            
            scores = 1 / (1 + np.exp(-outputs[0]))
            return [scores[i] for i in range(len(texts))]
        else:
            
            hidden_states = outputs[0]  
            mask = inputs["attention_mask"]
            mask_expanded = np.expand_dims(mask, -1).astype(np.float32)
            summed = np.sum(hidden_states * mask_expanded, axis=1)
            counts = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
            embeddings = summed / counts
            
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, 1e-9, None)
            return [embeddings[i] for i in range(len(texts))]

    def _cache_key(self, text: str) -> str:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"ml_cache:{self.model_type}:{text_hash}"

    async def _get_cached(self, key: str) -> Optional[np.ndarray]:
        try:
            c = await self.redis.connect()
            data = await c.get(key)
            if data:
                return np.array(json.loads(data))
        except Exception:
            pass
        return None

    async def _set_cached(self, key: str, value: np.ndarray):
        try:
            c = await self.redis.connect()
            await c.setex(key, self.cache_ttl, json.dumps(value.tolist()))
        except Exception:
            pass

    def get_metrics(self) -> Dict:
        avg_latency = (
            self._total_latency_ms / max(self._inference_count, 1)
        )
        total_requests = self._cache_hits + self._cache_misses
        cache_rate = self._cache_hits / max(total_requests, 1)

        return {
            "model_type": self.model_type,
            "inference_count": self._inference_count,
            "avg_latency_ms": round(avg_latency, 2),
            "cache_hit_rate": round(cache_rate, 3),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "queue_size": len(self._batch_queue),
        }