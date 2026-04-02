#!/usr/bin/env python3
"""
CLI script for ingesting documents into the Personal Knowledge Hub.
"""

import argparse
import os
import sys
from pathlib import Path
from src.core.database import KnowledgeHubDatabase
from src.core.embeddings import EmbeddingManager
from src.ingestion.processor import DocumentProcessor


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into Personal Knowledge Hub")
    parser.add_argument("--collection", "-c", default="default", 
                        help="Collection name (default: default)")
    parser.add_argument("--path", "-p", required=True,
                        help="Path to file or directory to ingest")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Recursively process directories")
    parser.add_argument("--config", default="config/settings.yaml",
                        help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Validate path
    if not os.path.exists(args.path):
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    try:
        # Initialize components
        database = KnowledgeHubDatabase(args.config)
        embedding_manager = EmbeddingManager(args.config)
        processor = DocumentProcessor(database, embedding_manager, args.config)
        
        # Process based on path type
        if os.path.isfile(args.path):
            success = processor.process_file(args.path, args.collection)
            if success:
                print(f"Successfully ingested file: {args.path}")
            else:
                print(f"Failed to ingest file: {args.path}")
                sys.exit(1)
        elif os.path.isdir(args.path):
            counts = processor.process_directory(args.path, args.collection, args.recursive)
            total = sum(counts.values())
            print(f"Successfully processed {total} files:")
            for ext, count in counts.items():
                print(f"  {ext}: {count} files")
        else:
            print(f"Error: Invalid path type: {args.path}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during ingestion: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()