# Knowledge Base Directory

This directory should contain your medical knowledge base documents.

## Required Files

Place the following file here:
- `Question BOOK.docx` - Main medical knowledge base

## How to Add

1. Upload your `Question BOOK.docx` file to this directory
2. Restart the application to rebuild the vector store:
   ```bash
   docker-compose restart hyoda-app
   ```

## Notes

- The application will automatically process DOCX files in this directory
- Additional text files can be placed in the `txt/` directory
- The RAG system uses these files to provide context-aware responses

