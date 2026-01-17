from typing import List, Dict, Optional
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
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

        # Check apakah model_name adalah local path atau HuggingFace repo
        model_path = Path(model_name)
        
        if model_path.exists() and model_path.is_dir():
            # Load dari local directory
            self.classifier = pipeline(
                task="sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=self.device,
            )
        else:
            # Assume HuggingFace repo format
            self.classifier = pipeline(
                task="sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=self.device,
            )

    # =========================
    # INTERNAL UTIL
    # =========================
    def _normalize_label(self, label: str) -> str:
        """
        Normalisasi label agar konsisten
        - Menangani variasi seperti POSITIVE/NEGATIVE/NEUTRAL
        - Menangani format LABEL_0/1/2 dengan membaca config id2label
        """
        raw = label
        label = label.lower()

        # Direct mapping for common strings
        if label in ["positive", "positif"]:
            out = "positive"
            return (
                "negative" if settings.SENTIMENT_SWAP_POS_NEG else out
            )
        if label in ["negative", "negatif"]:
            out = "negative"
            return (
                "positive" if settings.SENTIMENT_SWAP_POS_NEG else out
            )
        if label in ["neutral", "netral"]:
            return "neutral"

        # Handle LABEL_X formats coming from some pipelines
        try:
            if label.startswith("label_"):
                idx = int(label.split("_")[-1])
                id2label = getattr(getattr(self.classifier, "model", None), "config", None)
                id2label = getattr(id2label, "id2label", None)
                mapped = None
                if isinstance(id2label, dict) and str(idx) in id2label:
                    mapped = str(id2label[str(idx)]).lower()
                # Fallback: some models expose id2label as list
                elif isinstance(id2label, list) and 0 <= idx < len(id2label):
                    mapped = str(id2label[idx]).lower()
                if mapped:
                    if mapped in ["positive", "positif"]:
                        return (
                            "negative" if settings.SENTIMENT_SWAP_POS_NEG else "positive"
                        )
                    if mapped in ["negative", "negatif"]:
                        return (
                            "positive" if settings.SENTIMENT_SWAP_POS_NEG else "negative"
                        )
                    if mapped in ["neutral", "netral"]:
                        return "neutral"
                    return mapped
        except Exception:
            # ignore mapping errors; return original lowercase
            pass

        # Unknown label: return the lowercase raw to aid debugging
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
        )

        return [
            {
                "sentiment": self._normalize_label(r["label"]),
                "confidence": float(r["score"]),
            }
            for r in results
        ]
