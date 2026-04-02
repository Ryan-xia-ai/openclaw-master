# Personal Knowledge Hub

A personal knowledge management system powered by vector embeddings and semantic search.

## Overview

The Personal Knowledge Hub allows you to store, organize, and retrieve your personal knowledge using natural language queries. It leverages ChromaDB as the vector database backend and supports various document formats for ingestion.

## Features

- **Semantic Search**: Find relevant information using natural language queries
- **Multiple Formats**: Ingest content from text files, PDFs, web pages, and more
- **Metadata Support**: Store and filter by document metadata
- **Incremental Updates**: Efficiently update your knowledge base without reprocessing everything
- **CLI Tools**: Command-line interface for easy integration with workflows

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

1. **Ingest documents**:
   ```bash
   python scripts/ingest.py --collection my_knowledge --path /path/to/documents
   ```

2. **Query your knowledge**:
   ```bash
   python scripts/query.py --collection my_knowledge --query "What did I learn about AI?"
   ```

3. **Manage collections**:
   ```bash
   python scripts/manage.py --list
   python scripts/manage.py --delete old_collection
   ```

## Configuration

Configuration is handled through `config/settings.yaml`. See the example configuration file for details.

## Architecture

The system is organized into three main components:

1. **Core**: Database interface and embedding management
2. **Ingestion**: Document processing pipeline
3. **Query**: Search interface and result handling

See the [Implementation Plan](../personal-knowledge-hub-plan.md) for more details.

## Integration with OpenClaw

This project is designed to integrate with OpenClaw as a skill or plugin, enabling seamless knowledge management within your OpenClaw workflows.