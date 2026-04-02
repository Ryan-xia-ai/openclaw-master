#!/usr/bin/env python3
"""
CLI script for managing Personal Knowledge Hub collections.
"""

import argparse
import sys
from src.core.database import KnowledgeHubDatabase
from src.core.embeddings import EmbeddingManager
from src.query.search import KnowledgeSearch


def main():
    parser = argparse.ArgumentParser(description="Manage Personal Knowledge Hub collections")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all collections")
    parser.add_argument("--stats", "-s", 
                        help="Show statistics for a collection")
    parser.add_argument("--delete", "-d",
                        help="Delete a collection")
    parser.add_argument("--config", default="config/settings.yaml",
                        help="Path to configuration file")
    
    args = parser.parse_args()
    
    try:
        database = KnowledgeHubDatabase(args.config)
        
        if args.list:
            collections = database.list_collections()
            if collections:
                print("Available collections:")
                for collection in collections:
                    print(f"  - {collection}")
            else:
                print("No collections found.")
                
        elif args.stats:
            embedding_manager = EmbeddingManager(args.config)
            search = KnowledgeSearch(database, embedding_manager, args.config)
            stats = search.get_collection_stats(args.stats)
            if stats:
                print(f"Collection: {stats['collection_name']}")
                print(f"Documents: {stats['document_count']}")
                print(f"Embedding dimensions: {stats['embedding_dimensions']}")
                print(f"Distance metric: {stats['distance_metric']}")
            else:
                print(f"No statistics available for collection: {args.stats}")
                
        elif args.delete:
            confirm = input(f"Are you sure you want to delete collection '{args.delete}'? (y/N): ")
            if confirm.lower() == 'y':
                database.delete_collection(args.delete)
                print(f"Collection '{args.delete}' deleted.")
            else:
                print("Deletion cancelled.")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error during management operation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()