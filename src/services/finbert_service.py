"""FinBERT service - ONNX-based financial sentiment classification.

Uses ProsusAI/finbert exported to ONNX format for deterministic,
calibrated sentiment scoring without PyTorch dependency.
"""

import logging
import os
import threading
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

    _shared_session = None
    _shared_tokenizer = None
    _shared_loaded = False
    _class_lock = threading.Lock()

    def __init__(self, model_dir: str | Path | None = None) -> None:
        self._model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._session = None
        self._tokenizer = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazily load the ONNX model and tokenizer on first use (thread-safe)."""
        if self._loaded:
            return

        with FinBertService._class_lock:
            if self._loaded:
                return

            if not FinBertService._shared_loaded:
                import onnxruntime as ort

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

                FinBertService._shared_session = ort.InferenceSession(
                    str(model_path),
                    sess_options,
                    providers=["CPUExecutionProvider"],
                )

                # Load tokenizer (uses only vocab.txt + config, no torch needed)
                FinBertService._shared_tokenizer = AutoTokenizer.from_pretrained(
                    str(self._model_dir)
                )
                FinBertService._shared_loaded = True

                logger.info("FinBERT ONNX model loaded successfully")

            self._session = FinBertService._shared_session
            self._tokenizer = FinBertService._shared_tokenizer
            self._loaded = True

    def _download_and_export(self) -> None:
        """Download ProsusAI/finbert and convert to ONNX on the fly.

        Uses huggingface_hub to download the PyTorch model, then exports
        to ONNX. Falls back to optimum if available.
        """

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
            import transformers.masking_utils
            from transformers import AutoModelForSequenceClassification

            # Patch transformers masking for ONNX TorchScript
            # tracing compatibility (transformers >= 5.6)
            def _patched_sdpa_mask(
                batch_size,
                q_length,
                kv_length,
                q_offset=0,
                kv_offset=0,
                mask_function=None,
                attention_mask=None,
                allow_is_causal_skip=False,
                allow_is_bidirectional_skip=False,
                local_size=None,
                dtype=torch.bool,
                device="cpu",
                config=None,
                use_vmap=False,
                **kwargs,
            ):
                if isinstance(q_length, torch.Tensor) and q_length.ndim > 0:
                    q_length, q_offset = q_length.shape[0], q_length[0].to(device)

                padding_mask = transformers.masking_utils.prepare_padding_mask(
                    attention_mask, kv_length, kv_offset
                )

                if allow_is_causal_skip and transformers.masking_utils._ignore_causal_mask_sdpa(
                    padding_mask, q_length, kv_length, kv_offset, local_size
                ):
                    return None
                mask_utils = transformers.masking_utils
                if allow_is_bidirectional_skip and mask_utils._ignore_bidirectional_mask_sdpa(
                    padding_mask, kv_length, local_size
                ):
                    return None

                if padding_mask is not None:
                    mask_function = transformers.masking_utils.and_masks(
                        mask_function,
                        transformers.masking_utils.padding_mask_function(padding_mask),
                    )

                batch_arange = torch.arange(batch_size, device=device)
                head_arange = torch.arange(1, device=device)
                q_arange = torch.arange(q_length, device=device) + q_offset
                kv_arange = torch.arange(kv_length, device=device) + kv_offset

                if not use_vmap:
                    attention_mask = mask_function(
                        *transformers.masking_utils._non_vmap_expansion_sdpa(
                            batch_arange, head_arange, q_arange, kv_arange
                        )
                    )
                    attention_mask = attention_mask.expand(batch_size, -1, q_length, kv_length)
                else:
                    attention_mask = transformers.masking_utils._vmap_expansion_sdpa(mask_function)(
                        batch_arange, head_arange, q_arange, kv_arange
                    )

                return attention_mask

            transformers.masking_utils.sdpa_mask = _patched_sdpa_mask
            if hasattr(transformers.masking_utils, "ALL_MASK_ATTENTION_FUNCTIONS"):
                transformers.masking_utils.ALL_MASK_ATTENTION_FUNCTIONS["sdpa"] = _patched_sdpa_mask

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
            prob_dict = {FINBERT_LABELS[i]: float(probs[i]) for i in range(len(FINBERT_LABELS))}

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
