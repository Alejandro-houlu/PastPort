#!/usr/bin/env python3
"""
Question Recommender Service
Provides question recommendations based on BERT intent classification
"""

import logging
import random
from typing import Dict, List, Optional
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path

logger = logging.getLogger(__name__)


class QuestionRecommenderService:
    """
    Service for generating question recommendations based on artifact species
    and user questions using BERT intent classification
    """
    
    def __init__(self, model_dir: str, data_file: str):
        """
        Initialize the question recommender service
        
        Args:
            model_dir: Path to the BERT model directory
            data_file: Path to the QA pairs JSON file
        """
        self.model_dir = Path(model_dir)
        self.data_file = Path(data_file)
        self.model = None
        self.tokenizer = None
        self.qa_df = None
        
        logger.info(f"Initializing QuestionRecommenderService with model: {model_dir}")
        self._load_model_and_data()
    
    def _load_model_and_data(self):
        """Load the BERT model, tokenizer, and QA pairs data"""
        try:
            # Load tokenizer and model
            logger.info(f"Loading tokenizer from {self.model_dir}")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            
            logger.info(f"Loading model from {self.model_dir}")
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_dir))
            self.model.eval()
            
            # Load QA pairs data
            logger.info(f"Loading QA pairs from {self.data_file}")
            self.qa_df = pd.read_json(str(self.data_file))
            
            logger.info("Question recommender service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error loading model or data: {e}", exc_info=True)
            raise
    
    def _predict_intent(self, text: str) -> tuple[str, float]:
        """
        Predict the intent of a given question
        
        Args:
            text: The question text
            
        Returns:
            Tuple of (predicted_intent_label, confidence_probability)
        """
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)[0]
                predicted_class_id = torch.argmax(probabilities).item()
                predicted_probability = probabilities[predicted_class_id].item()
            
            predicted_intent_label = self.model.config.id2label[predicted_class_id]
            return predicted_intent_label, predicted_probability
            
        except Exception as e:
            logger.error(f"Error predicting intent: {e}", exc_info=True)
            raise
    
    def _get_single_suggestions(
        self, 
        predicted_intent: str, 
        species: str
    ) -> Dict[str, List[str]]:
        """
        Get one suggestion from each category
        
        Args:
            predicted_intent: The predicted intent label
            species: The species name
            
        Returns:
            Dictionary with one question from each category
        """
        try:
            # Filter questions by category
            same_intent_species = self.qa_df[
                (self.qa_df['Intent'] == predicted_intent) & 
                (self.qa_df['Species'] == species)
            ]['Question'].tolist()
            
            diff_intent_same_species = self.qa_df[
                (self.qa_df['Intent'] != predicted_intent) & 
                (self.qa_df['Species'] == species)
            ]['Question'].tolist()
            
            diff_species_same_intent = self.qa_df[
                (self.qa_df['Intent'] == predicted_intent) & 
                (self.qa_df['Species'] != species)
            ]['Question'].tolist()
            
            diff_species_intent = self.qa_df[
                (self.qa_df['Intent'] != predicted_intent) & 
                (self.qa_df['Species'] != species)
            ]['Question'].tolist()
            
            # Get one random question from each category
            result = {
                'same_intent_species': random.sample(same_intent_species, min(1, len(same_intent_species))),
                'diff_intent_same_species': random.sample(diff_intent_same_species, min(1, len(diff_intent_same_species))),
                'diff_species_same_intent': random.sample(diff_species_same_intent, min(1, len(diff_species_same_intent))),
                'diff_species_intent': random.sample(diff_species_intent, min(1, len(diff_species_intent)))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}", exc_info=True)
            raise
    
    def get_recommendations(
        self, 
        species: str, 
        question: str
    ) -> Optional[Dict[str, List[str]]]:
        """
        Get question recommendations based on species and question
        
        Args:
            species: The artifact species/name
            question: The user's question
            
        Returns:
            Dictionary with 4 categories of questions (one from each category),
            or None if an error occurs
        """
        try:
            logger.info(f"Getting recommendations for species: {species}, question: {question}")
            
            # Predict intent
            predicted_intent, confidence = self._predict_intent(question)
            logger.info(f"Predicted intent: {predicted_intent} (confidence: {confidence:.4f})")
            
            # Get suggestions
            suggestions = self._get_single_suggestions(predicted_intent, species)
            
            logger.info(f"Generated {sum(len(v) for v in suggestions.values())} suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return None
