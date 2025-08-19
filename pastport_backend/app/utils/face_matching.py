"""
Face matching utilities using pure mathematical approach
Implements cosine similarity and Euclidean distance calculations
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Face matching configuration
RECOGNITION_THRESHOLD = 0.4  # Distance threshold (lower = more strict)
MIN_CONFIDENCE = 0.6  # Minimum confidence for match (1 - distance)


def euclidean_distance(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate Euclidean distance between two face embeddings
    This replicates the face-api.js FaceMatcher logic
    
    Args:
        embedding1: First face embedding (128 dimensions)
        embedding2: Second face embedding (128 dimensions)
    
    Returns:
        Euclidean distance between embeddings
    """
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings must have the same dimensions")
    
    # Convert to numpy arrays for efficient computation
    arr1 = np.array(embedding1, dtype=np.float32)
    arr2 = np.array(embedding2, dtype=np.float32)
    
    # Calculate Euclidean distance
    distance = np.linalg.norm(arr1 - arr2)
    
    return float(distance)


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two face embeddings
    Alternative to Euclidean distance
    
    Args:
        embedding1: First face embedding (128 dimensions)
        embedding2: Second face embedding (128 dimensions)
    
    Returns:
        Cosine similarity (0-1, higher = more similar)
    """
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings must have the same dimensions")
    
    # Convert to numpy arrays
    arr1 = np.array(embedding1, dtype=np.float32)
    arr2 = np.array(embedding2, dtype=np.float32)
    
    # Calculate cosine similarity
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return float(similarity)


def find_best_match(
    input_embeddings: List[List[float]], 
    stored_user_embeddings: Dict[str, List[List[float]]]
) -> Optional[Dict[str, Any]]:
    """
    Find the best matching user for given input embeddings
    Tests each input embedding against all stored user embeddings
    
    Args:
        input_embeddings: List of face embeddings from current capture
        stored_user_embeddings: Dict mapping user_id to list of stored embeddings
    
    Returns:
        Match result with user_id, confidence, and distance, or None if no match
    """
    if not input_embeddings or not stored_user_embeddings:
        logger.info("No input embeddings or stored embeddings provided")
        return None
    
    best_match = None
    best_confidence = 0.0
    best_distance = float('inf')
    best_user_id = None
    
    logger.info(f"Testing {len(input_embeddings)} input embeddings against {len(stored_user_embeddings)} users")
    
    # Test each input embedding against all stored users
    for input_embedding in input_embeddings:
        for user_id, user_embeddings in stored_user_embeddings.items():
            
            # Test against all embeddings for this user
            for stored_embedding in user_embeddings:
                try:
                    # Calculate distance (using Euclidean like face-api.js)
                    distance = euclidean_distance(input_embedding, stored_embedding)
                    confidence = 1.0 - distance  # Convert distance to confidence
                    
                    logger.debug(f"User {user_id}: distance={distance:.4f}, confidence={confidence:.4f}")
                    
                    # Check if this is the best match so far
                    if (distance < RECOGNITION_THRESHOLD and 
                        confidence > best_confidence and 
                        confidence >= MIN_CONFIDENCE):
                        
                        best_match = {
                            "user_id": user_id,
                            "distance": distance,
                            "confidence": confidence,
                            "matched": True
                        }
                        best_confidence = confidence
                        best_distance = distance
                        best_user_id = user_id
                        
                except Exception as e:
                    logger.error(f"Error calculating distance for user {user_id}: {e}")
                    continue
    
    if best_match:
        logger.info(f"Best match found: user_id={best_user_id}, confidence={best_confidence:.4f}, distance={best_distance:.4f}")
        return best_match
    else:
        logger.info("No match found above threshold")
        return {
            "user_id": None,
            "distance": None,
            "confidence": 0.0,
            "matched": False
        }


def validate_embeddings(embeddings: List[List[float]]) -> bool:
    """
    Validate face embeddings format and dimensions
    
    Args:
        embeddings: List of face embeddings to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not embeddings or not isinstance(embeddings, list):
        return False
    
    for embedding in embeddings:
        if not isinstance(embedding, list):
            return False
        
        # Check if embedding has correct dimensions (128 for face-api.js)
        if len(embedding) != 128:
            logger.warning(f"Invalid embedding dimension: {len(embedding)}, expected 128")
            return False
        
        # Check if all values are numbers
        try:
            [float(x) for x in embedding]
        except (ValueError, TypeError):
            logger.warning("Embedding contains non-numeric values")
            return False
    
    return True


def calculate_match_statistics(
    input_embeddings: List[List[float]], 
    stored_embeddings: List[List[float]]
) -> Dict[str, float]:
    """
    Calculate detailed matching statistics for analysis
    
    Args:
        input_embeddings: Input face embeddings
        stored_embeddings: Stored face embeddings for comparison
    
    Returns:
        Dictionary with min, max, mean distances and confidences
    """
    distances = []
    confidences = []
    
    for input_emb in input_embeddings:
        for stored_emb in stored_embeddings:
            try:
                distance = euclidean_distance(input_emb, stored_emb)
                confidence = 1.0 - distance
                
                distances.append(distance)
                confidences.append(confidence)
            except Exception as e:
                logger.error(f"Error in statistics calculation: {e}")
                continue
    
    if not distances:
        return {}
    
    return {
        "min_distance": min(distances),
        "max_distance": max(distances),
        "mean_distance": sum(distances) / len(distances),
        "min_confidence": min(confidences),
        "max_confidence": max(confidences),
        "mean_confidence": sum(confidences) / len(confidences),
        "total_comparisons": len(distances)
    }
