"""Example usage of the repository ingestion module."""

from pathlib import Path

from app.ingestion import (
    IngestionConfig,
    RepositoryIngestor,
    IngestionError,
)


def main():
    """Demonstrate repository ingestion usage."""
    
    # Example 1: Basic usage with default configuration
    print("Example 1: Basic ingestion")
    print("-" * 50)
    
    zip_path = "path/to/repository.zip"
    
    try:
        with RepositoryIngestor() as ingestor:
            files = ingestor.ingest_zip(zip_path)
            
            print(f"Successfully ingested {len(files)} files")
            
            # Display first few files
            for file_meta in files[:5]:
                print(f"\nFile: {file_meta.relative_path}")
                print(f"  Language: {file_meta.language}")
                print(f"  Size: {file_meta.size} bytes")
                print(f"  SHA256: {file_meta.sha256[:16]}...")
                print(f"  Encoding: {file_meta.encoding}")
    
    except IngestionError as e:
        print(f"Ingestion failed: {e}")
    
    print("\n")
    
    # Example 2: Custom configuration
    print("Example 2: Custom configuration")
    print("-" * 50)
    
    # Create custom config with stricter limits
    config = IngestionConfig()
    config.MAX_ARCHIVE_SIZE_MB = 100
    config.MAX_FILE_SIZE_MB = 5
    config.MAX_FILE_COUNT = 1000
    
    # Add custom language support
    config.LANGUAGE_EXTENSIONS['.py'] = 'python'
    config.LANGUAGE_EXTENSIONS['.js'] = 'javascript'
    
    try:
        with RepositoryIngestor(config=config) as ingestor:
            files = ingestor.ingest_zip(zip_path)
            
            # Group files by language
            by_language = {}
            for file_meta in files:
                lang = file_meta.language
                by_language.setdefault(lang, []).append(file_meta)
            
            print("Files by language:")
            for lang, lang_files in sorted(by_language.items()):
                print(f"  {lang}: {len(lang_files)} files")
    
    except IngestionError as e:
        print(f"Ingestion failed: {e}")
    
    print("\n")
    
    # Example 3: Manual cleanup (without context manager)
    print("Example 3: Manual cleanup")
    print("-" * 50)
    
    ingestor = RepositoryIngestor()
    
    try:
        files = ingestor.ingest_zip(zip_path)
        
        # Process files...
        print(f"Processed {len(files)} files")
        
        # Access temporary directory if needed
        print(f"Temp directory: {ingestor.temp_dir}")
        
    except IngestionError as e:
        print(f"Ingestion failed: {e}")
    
    finally:
        # Always cleanup
        ingestor.cleanup()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
