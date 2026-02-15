from typing import List, Dict, Optional
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
import torch

from app.core.config import settings


class SentimentService:
    """
    Service untuk melakukan analisis sentimen komentar
    menggunakan model Transformer (HuggingFace).
    """

    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        batch_size: int = 16,
    ):
        """
        Parameters
        ----------
        model_name : str
            Nama model HuggingFace atau path ke local model directory
        device : str | None
            "cpu" atau "cuda". Jika None → auto detect
        batch_size : int
            Ukuran batch untuk inferensi
        """

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = 0 if device == "cuda" else -1
        self.batch_size = batch_size
        self.max_length = 512

        self.classifier = pipeline(
            task="sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=self.device,
        )

        try:
            tokenizer = getattr(self.classifier, "tokenizer", None)
            if tokenizer is not None:
                max_len = getattr(tokenizer, "model_max_length", None)
                if isinstance(max_len, int) and 1 < max_len < 100000:
                    self.max_length = max_len
        except Exception:
            pass

    # =========================
    # INTERNAL UTIL
    # =========================
    def _apply_swap(self, label: str) -> str:
        if label == "positive":
            return "negative" if settings.SENTIMENT_SWAP_POS_NEG else "positive"
        if label == "negative":
            return "positive" if settings.SENTIMENT_SWAP_POS_NEG else "negative"
        return label

    def _map_from_id2label(self, idx: int) -> Optional[str]:
        id2label = getattr(getattr(self.classifier, "model", None), "config", None)
        id2label = getattr(id2label, "id2label", None)

        if isinstance(id2label, dict):
            if str(idx) in id2label:
                return str(id2label[str(idx)]).lower()
            if idx in id2label:
                return str(id2label[idx]).lower()
        elif isinstance(id2label, list) and 0 <= idx < len(id2label):
            return str(id2label[idx]).lower()

        return None

    def _normalize_label(self, label: str) -> str:
        """
        Normalisasi label agar konsisten
        - Menangani variasi seperti POSITIVE/NEGATIVE/NEUTRAL
        - Menangani format LABEL_0/1/2 dengan membaca config id2label
        """
        label = label.lower()

        direct_map = {
            "positive": "positive",
            "positif": "positive",
            "negative": "negative",
            "negatif": "negative",
            "neutral": "neutral",
            "netral": "neutral",
        }

        if label in direct_map:
            return self._apply_swap(direct_map[label])

        if label.startswith("label_"):
            try:
                idx = int(label.split("_")[-1])
                mapped = self._map_from_id2label(idx)
                if mapped and mapped in direct_map:
                    return self._apply_swap(direct_map[mapped])
                if mapped:
                    return mapped
            except Exception:
                pass

        return label

    # =========================
    # SINGLE ANALYSIS
    # =========================
    def analyze(self, text: str) -> Dict:
        """
        Analisis satu teks

        Return:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "confidence": float
        }
        """

        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
            }

        result = self.classifier(text)[0]

        return {
            "sentiment": self._normalize_label(result["label"]),
            "confidence": float(result["score"]),
        }

    # =========================
    # BATCH ANALYSIS
    # =========================
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analisis banyak teks sekaligus (lebih cepat)

        Return:
        [
            {
                "sentiment": str,
                "confidence": float
            },
            ...
        ]
        """

        if not texts:
            return []

        # Ganti teks kosong agar tidak error
        safe_texts = [
            text if text and text.strip() else " "
            for text in texts
        ]

        results = self.classifier(
            safe_texts,
            batch_size=self.batch_size,
            truncation=True,
            max_length=self.max_length,
        )

        return [
            {
                "sentiment": self._normalize_label(r["label"]),
                "confidence": float(r["score"]),
            }
            for r in results
        ]


class OnnxSentimentService:
    """
    Service untuk melakukan analisis sentimen menggunakan ONNX Runtime.
    """

    def __init__(
        self,
        model_name_or_path: str,
        onnx_model_path: Optional[str] = None,
        batch_size: int = 16,
    ):
        self.batch_size = batch_size
        self.max_length = 512

        model_dir = Path(model_name_or_path)
        if onnx_model_path:
            onnx_path = Path(onnx_model_path)
        else:
            onnx_path = model_dir / "model.onnx"

        if not onnx_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {onnx_path}")

        # Tokenizer from local dir or HF repo
        if model_dir.exists() and model_dir.is_dir():
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
            self.config = AutoConfig.from_pretrained(str(model_dir))
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
            self.config = AutoConfig.from_pretrained(model_name_or_path)

        try:
            max_len = getattr(self.tokenizer, "model_max_length", None)
            if isinstance(max_len, int) and 1 < max_len < 100000:
                self.max_length = max_len
        except Exception:
            pass

        self.id2label = self._normalize_id2label(getattr(self.config, "id2label", None))

        self.session = ort.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"],
        )

        self.input_names = {i.name for i in self.session.get_inputs()}

    def _normalize_id2label(self, id2label):
        if isinstance(id2label, dict):
            label0 = str(id2label.get(0) or id2label.get("0") or "").lower()
            label1 = str(id2label.get(1) or id2label.get("1") or "neutral").lower()
            label2 = str(id2label.get(2) or id2label.get("2") or "").lower()
            if label0 == "positive" and label2 == "negative":
                return {0: "negative", 1: label1 or "neutral", 2: "positive"}
            return id2label

        if isinstance(id2label, list) and len(id2label) >= 3:
            label0 = str(id2label[0]).lower()
            label1 = str(id2label[1]).lower()
            label2 = str(id2label[2]).lower()
            if label0 == "positive" and label2 == "negative":
                return ["negative", label1 or "neutral", "positive"]
            return id2label

        return id2label

    def _normalize_label(self, label: str) -> str:
        raw = label
        label = label.lower()

        if label in ["positive", "positif"]:
            out = "positive"
            return "negative" if settings.SENTIMENT_SWAP_POS_NEG else out
        if label in ["negative", "negatif"]:
            out = "negative"
            return "positive" if settings.SENTIMENT_SWAP_POS_NEG else out
        if label in ["neutral", "netral"]:
            return "neutral"

        return label if label else raw

    def _map_label(self, idx: int) -> str:
        mapped = None
        if isinstance(self.id2label, dict):
            mapped = self.id2label.get(idx) or self.id2label.get(str(idx))
        elif isinstance(self.id2label, list) and 0 <= idx < len(self.id2label):
            mapped = self.id2label[idx]

        if mapped:
            return self._normalize_label(str(mapped))
        return str(idx)

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        logits = logits - np.max(logits, axis=-1, keepdims=True)
        exp = np.exp(logits)
        return exp / np.sum(exp, axis=-1, keepdims=True)

    def analyze(self, text: str) -> Dict:
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
            }

        result = self.analyze_batch([text])[0]
        return result

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        if not texts:
            return []

        safe_texts = [text if text and text.strip() else " " for text in texts]

        tokens = self.tokenizer(
            safe_texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="np",
        )

        inputs = {}
        if "input_ids" in self.input_names:
            inputs["input_ids"] = tokens["input_ids"]
        if "attention_mask" in self.input_names and "attention_mask" in tokens:
            inputs["attention_mask"] = tokens["attention_mask"]
        if "token_type_ids" in self.input_names and "token_type_ids" in tokens:
            inputs["token_type_ids"] = tokens["token_type_ids"]

        outputs = self.session.run(None, inputs)
        logits = outputs[0]

        probs = self._softmax(logits)
        labels_idx = np.argmax(probs, axis=-1)
        scores = np.max(probs, axis=-1)

        results = []
        for idx, score in zip(labels_idx, scores):
            label = self._map_label(int(idx))
            results.append(
                {
                    "sentiment": self._normalize_label(label),
                    "confidence": float(score),
                }
            )

        return results
