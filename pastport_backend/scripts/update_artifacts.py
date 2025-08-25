#!/usr/bin/env python3
"""
Developer script to update artifacts database with YOLO model labels
Run this script to automatically populate the artifacts table with all labels from your trained YOLO model.

Usage:
    cd pastport_backend
    python scripts/update_artifacts.py
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from app.services.artifact_updater import ArtifactUpdaterService


async def main():
    """Main function to run the artifact updater"""
    print("=== PastPort Artifact Database Updater ===")
    print("This script will update your artifacts database with labels from your YOLO model.\n")
    
    # Relative path to your YOLO model from pastport_backend directory
    model_path = "app/ml_models/yolo11n-seg-custom-v7.pt"
    
    try:
        # Initialize the updater service
        print(f"Initializing artifact updater with model: {model_path}")
        updater = ArtifactUpdaterService(model_path)
        
        # Run the update process
        print("Starting artifact database update...\n")
        stats = await updater.update_artifacts()
        
        # Display final results
        print("\n" + "="*50)
        print("ARTIFACT UPDATE SUMMARY")
        print("="*50)
        print(f"✅ Total labels in YOLO model: {stats['total_model_labels']}")
        print(f"📊 Existing artifacts in database: {stats['existing_artifacts']}")
        print(f"🆕 New artifacts created: {stats['new_artifacts_created']}")
        
        if stats['new_artifacts_created'] > 0:
            print(f"\n🎯 Newly added artifacts:")
            for name in stats['created_artifact_names']:
                print(f"   • {name}")
        else:
            print(f"\n✨ All artifacts from your YOLO model are already in the database!")
        
        print(f"\n🎉 Artifact database update completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please make sure your YOLO model file exists at the specified path.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        print("Please check your database connection and model file.")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
