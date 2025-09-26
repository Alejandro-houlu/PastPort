#!/usr/bin/env python3
# bert_qclass_infer.py

import argparse
import random
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Hardcoded paths
MODEL_DIR = "bert-qclass-model_3"
DATA_FILE = "QA_pairs.json"


def load_model_and_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return model, tokenizer


def predict_intent(model, tokenizer, text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=-1)[0]
        predicted_class_id = torch.argmax(probabilities).item()
        predicted_probability = probabilities[predicted_class_id].item()

    predicted_intent_label = model.config.id2label[predicted_class_id]
    return predicted_intent_label, predicted_probability


def get_suggestions(predicted_intent_label, df, species, num_same_intent=1, num_different_intent=1):
    same_intent_species_df = df[(df['Intent'] == predicted_intent_label) & (df['Species'] == species)]['Question'].tolist()
    different_intent_same_species_df = df[(df['Intent'] != predicted_intent_label) & (df['Species'] == species)]['Question'].tolist()
    diff_species_same_intent_df = df[(df['Intent'] == predicted_intent_label) & (df['Species'] != species)]['Question'].tolist()
    diff_species_intent_df = df[(df['Intent'] != predicted_intent_label) & (df['Species'] != species)]['Question'].tolist()

    suggest_same_intent_species = random.sample(same_intent_species_df, min(num_same_intent, len(same_intent_species_df)))
    suggest_diff_intent_same_species = random.sample(different_intent_same_species_df, min(num_different_intent, len(different_intent_same_species_df)))
    suggest_diff_species_same_intent = random.sample(diff_species_same_intent_df, min(num_same_intent, len(diff_species_same_intent_df)))
    suggest_diff_species_intent = random.sample(diff_species_intent_df, min(num_different_intent, len(diff_species_intent_df)))

    return suggest_same_intent_species, suggest_diff_intent_same_species, suggest_diff_species_same_intent, suggest_diff_species_intent


def main():
    parser = argparse.ArgumentParser(description="BERT Question Intent Classifier with Suggestions")
    parser.add_argument("--species", type=str, required=True, help="Species to filter suggestions (e.g. 'Sauropods')")
    parser.add_argument("--question", type=str, required=True, help="User question to classify")
    args = parser.parse_args()

    # Load model and dataset
    model, tokenizer = load_model_and_tokenizer()
    df = pd.read_json(DATA_FILE)

    # Predict intent
    predicted_intent_label, predicted_probability = predict_intent(model, tokenizer, args.question)

    print("\n================= RESULTS =================")
    print(f"User Question: {args.question}")
    print(f"Predicted Intent: {predicted_intent_label}")
    print(f"Predicted Probability: {predicted_probability:.4f}")

    # Get suggestions
    same_intent, diff_intent_same_species, diff_species_same_intent, diff_species_intent = get_suggestions(
        predicted_intent_label, df, args.species
    )

    print("\nSuggested Questions:")
    print("Same Intent and Species:")
    for q in same_intent:
        print(f"- {q}")

    print("\nDifferent Intent and Same Species:")
    for q in diff_intent_same_species:
        print(f"- {q}")

    print("\nDifferent Species and Same Intent:")
    for q in diff_species_same_intent:
        print(f"- {q}")

    print("\nDifferent Species and Intent:")
    for q in diff_species_intent:
        print(f"- {q}")


if __name__ == "__main__":
    main()
