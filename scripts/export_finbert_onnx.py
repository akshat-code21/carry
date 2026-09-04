"""One-time script: Export ProsusAI/finbert to ONNX format.

Requires torch and optimum to be installed temporarily:
    pip install torch optimum[exporters]

Usage:
    python scripts/export_finbert_onnx.py

Produces:
    data/models/finbert/
    ├── model.onnx
    ├── tokenizer_config.json
    ├── vocab.txt
    └── special_tokens_map.json
"""

import shutil
from pathlib import Path

MODEL_NAME = "ProsusAI/finbert"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "models" / "finbert"


def _patch_transformers_for_onnx_export():
    """Patch transformers masking utility for ONNX TorchScript tracing compatibility.

    In transformers >= 5.6, sdpa_mask assumes any torch.Tensor q_length is a 1D tensor
    of cache_positions, which raises IndexError on 0-dim scalar tensors produced by JIT tracing.
    """
    import torch
    import transformers.masking_utils

    orig_sdpa = transformers.masking_utils.sdpa_mask

    def patched_sdpa_mask(
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
        if allow_is_bidirectional_skip and transformers.masking_utils._ignore_bidirectional_mask_sdpa(
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
            attention_mask = transformers.masking_utils._vmap_expansion_sdpa(
                mask_function
            )(batch_arange, head_arange, q_arange, kv_arange)

        return attention_mask

    transformers.masking_utils.sdpa_mask = patched_sdpa_mask
    if hasattr(transformers.masking_utils, "ALL_MASK_ATTENTION_FUNCTIONS"):
        transformers.masking_utils.ALL_MASK_ATTENTION_FUNCTIONS["sdpa"] = patched_sdpa_mask


def export():
    """Download ProsusAI/finbert and export to ONNX."""
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        raise SystemExit(
            "transformers is required. Install with: pip install transformers"
        )

    try:
        import torch  # noqa: F401
    except ImportError:
        raise SystemExit(
            "torch is required for export only. Install with: pip install torch"
        )

    _patch_transformers_for_onnx_export()

    print(f"Downloading {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export to ONNX
    print("Exporting to ONNX...")
    dummy_input = tokenizer(
        "Stock price increased significantly",
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=512,
    )

    onnx_path = OUTPUT_DIR / "model.onnx"

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
        dynamo=False,  # Use legacy exporter for single self-contained .onnx file
    )

    # Save tokenizer files alongside the model
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # Clean up unnecessary files (keep only what the tokenizer needs)
    keep_files = {
        "model.onnx",
        "tokenizer_config.json",
        "vocab.txt",
        "special_tokens_map.json",
        "tokenizer.json",
    }
    for f in OUTPUT_DIR.iterdir():
        if f.name not in keep_files:
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)

    model_size_mb = onnx_path.stat().st_size / (1024 * 1024)
    print(f"✓ Exported to {OUTPUT_DIR}")
    print(f"  Model size: {model_size_mb:.1f} MB")
    print(f"  Files: {[f.name for f in OUTPUT_DIR.iterdir()]}")


if __name__ == "__main__":
    export()
