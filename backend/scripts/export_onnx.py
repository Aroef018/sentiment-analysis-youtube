"""Export HuggingFace sequence classification model to ONNX.

Usage:
  python scripts/export_onnx.py --model-path ./model --output-path ./model/model.onnx
"""

from pathlib import Path
import argparse

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers.onnx import FeaturesManager, export


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="HF repo name or local path")
    parser.add_argument("--output-path", required=True, help="Output .onnx path")
    parser.add_argument("--opset", type=int, default=18)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model_path
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    feature = "sequence-classification"
    model_type = model.config.model_type
    FeaturesManager.check_supported_model_or_raise(model, feature=feature)
    onnx_config_cls = FeaturesManager.get_config(model_type, feature=feature)
    onnx_config = onnx_config_cls(model.config)

    export(
        preprocessor=tokenizer,
        model=model,
        config=onnx_config,
        opset=args.opset,
        output=output_path,
    )

    print(f"ONNX exported to {output_path}")


if __name__ == "__main__":
    main()
