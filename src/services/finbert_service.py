"""FinBERT service — ONNX-based financial sentiment classification.

Uses ProsusAI/finbert exported to ONNX format for deterministic,
calibrated sentiment scoring without PyTorch dependency.
"""

import logging
import os
from pathlib import Path

import numpy as np

from transformers import AutoTokenizer

from src.services.interfaces import FinBertResult

logger = logging.getLogger(__name__)

# Default model directory (relative to project root)
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models" / "finbert"

# FinBERT label mapping: index → HuggingFace label → our label
# ProsusAI/finbert outputs: 0=positive, 1=negative, 2=neutral
FINBERT_LABELS = {0: "positive", 1: "negative", 2: "neutral"}
SENTIMENT_MAP = {"positive": "bullish", "negative": "bearish", "neutral": "neutral"}


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Compute softmax probabilities from raw logits."""
    exp = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    return exp / np.sum(exp, axis=-1, keepdims=True)


class FinBertService:
    """Singleton FinBERT service using ONNX Runtime for inference.

    Loads the ONNX model and tokenizer once, then provides batch
    sentiment classification for financial text.
    """

    def __init__(self, model_dir: str | Path | None = None) -> None:
        self._model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._session = None
        self._tokenizer = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazily load the ONNX model and tokenizer on first use."""
        if self._loaded:
            return

        import onnxruntime as ort
        from transformers import AutoTokenizer

        model_path = self._model_dir / "model.onnx"

        if not model_path.exists():
            # Fallback: download and use model directly from HuggingFace
            # (slower first run, but works without export step)
            logger.warning(
                f"ONNX model not found at {model_path}. "
                "Falling back to downloading from HuggingFace and running export. "
                "Run 'python scripts/export_finbert_onnx.py' to pre-export."
            )
            self._download_and_export()

        logger.info(f"Loading FinBERT ONNX model from {self._model_dir}")

        # Load ONNX session with CPU provider
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = int(os.environ.get("FINBERT_THREADS", "4"))

        self._session = ort.InferenceSession(
            str(model_path),
            sess_options,
            providers=["CPUExecutionProvider"],
        )

        # Load tokenizer (uses only vocab.txt + config, no torch needed)
        self._tokenizer = AutoTokenizer.from_pretrained(str(self._model_dir))
        self._loaded = True

        logger.info("FinBERT ONNX model loaded successfully")

    def _download_and_export(self) -> None:
        """Download ProsusAI/finbert and convert to ONNX on the fly.

        Uses huggingface_hub to download the PyTorch model, then exports
        to ONNX. Falls back to optimum if available.
        """
        from transformers import AutoTokenizer

        logger.info("Downloading ProsusAI/finbert and exporting to ONNX...")
        self._model_dir.mkdir(parents=True, exist_ok=True)

        # Try optimum (clean ONNX export without manual torch code)
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification

            model = ORTModelForSequenceClassification.from_pretrained(
                "ProsusAI/finbert", export=True
            )
            tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")

            model.save_pretrained(str(self._model_dir))
            tokenizer.save_pretrained(str(self._model_dir))
            logger.info(f"FinBERT ONNX model exported via optimum to {self._model_dir}")
            return
        except ImportError:
            logger.info("optimum not available, trying torch export...")

        # Try direct torch export
        try:
            import torch
            from transformers import AutoModelForSequenceClassification

            tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            model.eval()

            dummy_input = tokenizer(
                "Stock price increased significantly",
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512,
            )

            onnx_path = self._model_dir / "model.onnx"
            torch.onnx.export(
                model,
                (dummy_input["input_ids"], dummy_input["attention_mask"]),
                str(onnx_path),
                input_names=["input_ids", "attention_mask"],
                output_names=["logits"],
                dynamic_axes={
                    "input_ids": {0: "batch_size", 1: "sequence_length"},
                    "attention_mask": {0: "batch_size", 1: "sequence_length"},
                    "logits": {0: "batch_size"},
                },
                opset_version=14,
                dynamo=False,
            )
            tokenizer.save_pretrained(str(self._model_dir))
            logger.info(f"FinBERT ONNX model exported via torch to {self._model_dir}")
            return
        except ImportError:
            pass

        raise RuntimeError(
            "Cannot export FinBERT to ONNX. Install one of:\n"
            "1. 'pip install torch' and run 'python scripts/export_finbert_onnx.py'\n"
            "2. 'pip install optimum[exporters]' for auto-export\n"
            "Then place model.onnx in data/models/finbert/"
        )

    def analyze_texts(self, texts: list[str]) -> list[FinBertResult]:
        """Batch-classify a list of financial texts.

        Args:
            texts: List of financial narrative/prediction strings.

        Returns:
            List of FinBertResult with sentiment, confidence, and probabilities.
        """
        if not texts:
            return []

        self._ensure_loaded()

        # Trim texts to 300 chars (social posts/headlines are short; avoids massive zero-padding)
        trimmed_texts = [str(t)[:300] for t in texts]

        batch_size = 16
        all_logits = []

        for i in range(0, len(trimmed_texts), batch_size):
            chunk = trimmed_texts[i : i + batch_size]
            encoded = self._tokenizer(
                chunk,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="np",
            )
            ort_inputs = {
                "input_ids": encoded["input_ids"].astype(np.int64),
                "attention_mask": encoded["attention_mask"].astype(np.int64),
            }
            chunk_logits = self._session.run(None, ort_inputs)[0]
            all_logits.append(chunk_logits)

        logits = np.vstack(all_logits)
        probabilities = _softmax(logits)
        results = []

        for probs in probabilities:
            # Build probability dict
            prob_dict = {
                FINBERT_LABELS[i]: float(probs[i]) for i in range(len(FINBERT_LABELS))
            }

            # Get winning class
            winning_idx = int(np.argmax(probs))
            winning_label = FINBERT_LABELS[winning_idx]
            mapped_sentiment = SENTIMENT_MAP[winning_label]
            confidence = float(probs[winning_idx])

            results.append(
                FinBertResult(
                    sentiment=mapped_sentiment,
                    confidence=confidence,
                    probabilities=prob_dict,
                )
            )

        return results

    def analyze_text(self, text: str) -> FinBertResult:
        """Classify a single financial text.

        Convenience wrapper around analyze_texts for single inputs.
        """
        return self.analyze_texts([text])[0]
