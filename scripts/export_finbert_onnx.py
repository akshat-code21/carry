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
