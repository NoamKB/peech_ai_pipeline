"""
This module provides the HeadlineClassifier class for categorizing YouTube video titles (or other text) using a zero-shot classification model.
Refactored for modularity: the classifier is now encapsulated in a class for easier testing and reuse, and supports custom candidate categories.
"""
from transformers import pipeline

class HeadlineClassifier:
    def __init__(self, model_name="facebook/bart-large-mnli"):
        self.model = pipeline("zero-shot-classification", model=model_name)

    def classify(self, text, candidate_labels):
        """
        Classifies the input text into one of the candidate_labels using zero-shot classification.
        Returns the best category, all scores, and the raw model output.
        """
        result = self.model(text, candidate_labels)
        best_idx = result['scores'].index(max(result['scores']))
        best_category = result['labels'][best_idx]
        return best_category, result['scores'], result
