from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

MODEL_PATH = "model/roberta_finetuned"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=-1  # CPU
)

label_map = {
    "LABEL_0": "positif",
    "LABEL_1": "netral",
    "LABEL_2": "negatif"
}

def predict_sentiment(text: str):
    result = sentiment_pipeline(text)[0]
    label = label_map.get(result["label"], result["label"])

    return {
        "label": label,
        "score": float(result["score"])
    }
