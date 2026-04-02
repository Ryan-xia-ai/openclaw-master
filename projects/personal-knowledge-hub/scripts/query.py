#!/usr/bin/env python3
"""
CLI script for querying the Personal Knowledge Hub.
"""

import argparse
import sys
from src.core.database import KnowledgeHubDatabase
from src.core.embeddings import EmbeddingManager
from src.query.search import KnowledgeSearch


def main():
    parser = argparse.ArgumentParser(description="Query Personal Knowledge Hub")
    parser.add_argument("--collection", "-c", default="default",
                        help="Collection name (default: default)")
    parser.add_argument("--query", "-q", required=True,
                        help="Natural language query")
    parser.add_argument("--top-k", "-k", type=int, default=5,
                        help="Number of results to return (default: 5)")
    parser.add_argument("--min-similarity", "-s", type=float, default=0.3,
                        help="Minimum similarity threshold (default: 0.3)")
    parser.add_argument("--config", default="config/settings.yaml",
                        help="Path to configuration file")
    
    args = parser.parse_args()
    
    try:
        # Initialize components
        database = KnowledgeHubDatabase(args.config)
        embedding_manager = EmbeddingManager(args.config)
        search = KnowledgeSearch(database, embedding_manager, args.config)
        
        # Perform search
        results = search.search(
            query_text=args.query,
            collection_name=args.collection,
            top_k=args.top_k,
            min_similarity=args.min_similarity
        )
        
        # Display results
        if not results:
            print("No relevant results found.")
        else:
            print(f"Found {len(results)} relevant results:\n")
            for i, result in enumerate(results, 1):
                print(f"Result {i} (Score: {result['score']:.3f}):")
                print(f"Document ID: {result['id']}")
                if result['metadata']:
                    source = result['metadata'].get('source', 'unknown')
                    file_name = result['metadata'].get('file_name', 'unknown')
                    print(f"Source: {source} - {file_name}")
                print(f"Content: {result['document'][:200]}...")
                print("-" * 80)
                
    except Exception as e:
        print(f"Error during query: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()