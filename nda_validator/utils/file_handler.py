# nda_validator/utils/file_handler.py
import shutil
from pathlib import Path
import hashlib

class LargeFileHandler:
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    
    @staticmethod
    def split_large_file(file_path, output_dir):
        """Split file into chunks."""
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'rb') as f:
            chunk_num = 0
            while True:
                chunk = f.read(LargeFileHandler.CHUNK_SIZE)
                if not chunk:
                    break
                chunk_path = output_dir / f"{file_path.stem}_chunk{chunk_num}{file_path.suffix}"
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunk_num += 1
                print(f"Created chunk {chunk_num}")
