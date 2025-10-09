"""
Artifact Cache Service
Manages cached list of available artifacts for quick LLM checks
"""
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.artifact import Artifact

logger = logging.getLogger(__name__)

SINGAPORE_TZ = ZoneInfo("Asia/Singapore")
CACHE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "artifacts_cache.txt"
)
CACHE_EXPIRY_MINUTES = 15


def get_singapore_now() -> datetime:
    """Get current time in Singapore timezone"""
    return datetime.now(SINGAPORE_TZ)


def get_artifact_cache_path() -> str:
    """Get the path to the artifact cache file"""
    return CACHE_FILE_PATH


async def get_all_artifact_names() -> List[str]:
    """
    Query database for all artifact names where isDisplay is true
    
    Returns:
        List of artifact names from database
    """
    try:
        logger.info("Querying database for artifact names")
        
        async for db in get_db():
            # Query artifacts where isDisplay is true
            stmt = select(Artifact.artifact_name).where(Artifact.isDisplay == True)
            result = await db.execute(stmt)
            artifact_names = [row[0] for row in result.all()]
            
            logger.info(f"Retrieved {len(artifact_names)} artifact names from database")
            return artifact_names
            
    except Exception as e:
        logger.error(f"Failed to query artifact names from database: {e}")
        return []


def read_artifact_cache() -> Tuple[Optional[datetime], List[str]]:
    """
    Read artifact cache file
    
    Returns:
        Tuple of (timestamp, artifact_list)
        Returns (None, []) if cache doesn't exist or is invalid
    """
    try:
        if not os.path.exists(CACHE_FILE_PATH):
            logger.info("Artifact cache file does not exist")
            return None, []
        
        with open(CACHE_FILE_PATH, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            logger.warning("Artifact cache file is empty")
            return None, []
        
        # First line should be timestamp comment
        first_line = lines[0].strip()
        if not first_line.startswith("# Last Updated:"):
            logger.warning("Artifact cache file has invalid format")
            return None, []
        
        # Parse timestamp
        timestamp_str = first_line.replace("# Last Updated:", "").strip()
        timestamp = datetime.fromisoformat(timestamp_str)
        
        # Read artifact names (skip first line)
        artifacts = [line.strip() for line in lines[1:] if line.strip()]
        
        logger.info(f"Read artifact cache: {len(artifacts)} artifacts, last updated {timestamp}")
        return timestamp, artifacts
        
    except Exception as e:
        logger.error(f"Failed to read artifact cache: {e}")
        return None, []


def write_artifact_cache(artifacts: List[str]) -> bool:
    """
    Write artifact names to cache file with Singapore timestamp
    
    Args:
        artifacts: List of artifact names to cache
        
    Returns:
        Boolean indicating success
    """
    try:
        # Ensure data directory exists
        data_dir = os.path.dirname(CACHE_FILE_PATH)
        os.makedirs(data_dir, exist_ok=True)
        
        # Get Singapore time for timestamp
        now = get_singapore_now()
        timestamp_str = now.isoformat()
        
        # Write cache file
        with open(CACHE_FILE_PATH, 'w') as f:
            f.write(f"# Last Updated: {timestamp_str}\n")
            for artifact in artifacts:
                f.write(f"{artifact}\n")
        
        logger.info(f"Wrote artifact cache: {len(artifacts)} artifacts at {timestamp_str}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write artifact cache: {e}")
        return False


def is_cache_valid() -> bool:
    """
    Check if cache exists and is less than 15 minutes old
    
    Returns:
        Boolean indicating if cache is valid
    """
    timestamp, artifacts = read_artifact_cache()
    
    if timestamp is None or not artifacts:
        logger.info("Cache is invalid: file missing or empty")
        return False
    
    # Check age
    now = get_singapore_now()
    
    # Make both timezone-aware for comparison
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=SINGAPORE_TZ)
    
    age_minutes = (now - timestamp).total_seconds() / 60
    is_valid = age_minutes <= CACHE_EXPIRY_MINUTES
    
    logger.info(f"Cache age: {age_minutes:.1f} minutes, valid: {is_valid}")
    return is_valid


async def get_or_refresh_artifacts() -> List[str]:
    """
    Get artifact list from cache, or refresh if needed
    
    Main method to call - handles cache validation and refresh automatically
    
    Returns:
        List of artifact names
    """
    logger.info("Getting artifact list (with auto-refresh if needed)")
    
    # Check if cache is valid
    if is_cache_valid():
        timestamp, artifacts = read_artifact_cache()
        logger.info(f"Using cached artifact list: {len(artifacts)} artifacts")
        return artifacts
    
    # Cache is invalid or expired - refresh from database
    logger.info("Cache invalid or expired, refreshing from database")
    artifacts = await get_all_artifact_names()
    
    if artifacts:
        # Write new cache
        write_artifact_cache(artifacts)
        logger.info(f"Artifact cache refreshed: {len(artifacts)} artifacts")
    else:
        logger.warning("Failed to refresh artifact cache from database")
        # Try to return stale cache as fallback
        _, stale_artifacts = read_artifact_cache()
        if stale_artifacts:
            logger.info(f"Using stale cache as fallback: {len(stale_artifacts)} artifacts")
            return stale_artifacts
    
    return artifacts
