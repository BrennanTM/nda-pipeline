import shutil
from pathlib import Path
import hashlib
from typing import Optional, Dict, List
import logging
from tqdm import tqdm
from dataclasses import dataclass

@dataclass
class FileHandlingResult:
    """Result of file handling operations."""
    success: bool
    chunks: List[str]
    checksums: Dict[str, str]
    errors: List[str]
    warnings: List[str]

class LargeFileHandler:
    """Handles large file operations for NDA submission."""
    
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    NDA_SIZE_LIMIT = 2.5 * 1024 * 1024 * 1024  # 2.5GB NDA limit
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def split_large_file(self, file_path: Path, output_dir: Path) -> FileHandlingResult:
        """
        Split file into chunks with progress tracking and validation.
        
        Args:
            file_path: Path to large file
            output_dir: Directory to store chunks
            
        Returns:
            FileHandlingResult containing operation results
        """
        errors = []
        warnings = []
        checksums = {}
        chunks = []

        try:
            if not self._validate_file(file_path):
                return FileHandlingResult(
                    success=False,
                    chunks=[],
                    checksums={},
                    errors=[f"Invalid file: {file_path}"],
                    warnings=[]
                )
                
            output_dir.mkdir(parents=True, exist_ok=True)
            file_size = file_path.stat().st_size
            total_chunks = (file_size // self.CHUNK_SIZE) + 1

            self.logger.info(f"Splitting {file_path.name} into {total_chunks} chunks")
            
            with open(file_path, 'rb') as f:
                with tqdm(total=total_chunks, desc=f"Splitting {file_path.name}") as pbar:
                    chunk_num = 0
                    while True:
                        chunk = f.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                            
                        chunk_path = output_dir / f"{file_path.stem}_chunk{chunk_num}{file_path.suffix}"
                        checksum = self._write_chunk(chunk, chunk_path)
                        checksums[str(chunk_path)] = checksum
                        chunks.append(str(chunk_path))
                        
                        chunk_num += 1
                        pbar.update(1)
            
            # Validate chunks
            try:
                self._validate_chunks(checksums)
            except ValueError as e:
                errors.append(f"Chunk validation failed: {str(e)}")
                
        except Exception as e:
            errors.append(f"Error splitting file: {str(e)}")
            
        return FileHandlingResult(
            success=len(errors) == 0,
            chunks=chunks,
            checksums=checksums,
            errors=errors,
            warnings=warnings
        )
        
    def _validate_file(self, file_path: Path) -> bool:
        """Validate file exists and needs splitting."""
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
            
        if file_path.stat().st_size <= self.NDA_SIZE_LIMIT:
            self.logger.warning(f"File under NDA limit, splitting not needed: {file_path}")
            return False
            
        return True
        
    def _write_chunk(self, chunk: bytes, chunk_path: Path) -> str:
        """Write chunk to file and generate checksum."""
        checksum = hashlib.sha256(chunk).hexdigest()
        
        with open(chunk_path, 'wb') as chunk_file:
            chunk_file.write(chunk)
            
        return checksum
        
    def _validate_chunks(self, checksums: Dict[str, str]) -> None:
        """Verify all chunks were created correctly."""
        for chunk_path, expected_checksum in checksums.items():
            with open(chunk_path, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
                
            if actual_checksum != expected_checksum:
                raise ValueError(f"Chunk validation failed: {chunk_path}")

    def merge_chunks(self, chunk_dir: Path, output_path: Path) -> FileHandlingResult:
        """
        Merge chunks back into single file.
        
        Args:
            chunk_dir: Directory containing chunks
            output_path: Path for merged file
            
        Returns:
            FileHandlingResult containing operation results
        """
        errors = []
        warnings = []
        
        try:
            chunks = sorted(chunk_dir.glob(f"*chunk*"), 
                          key=lambda x: int(x.stem.split('chunk')[-1]))

            if not chunks:
                return FileHandlingResult(
                    success=False,
                    chunks=[],
                    checksums={},
                    errors=["No chunks found to merge"],
                    warnings=[]
                )
                           
            with open(output_path, 'wb') as outfile:
                with tqdm(chunks, desc=f"Merging chunks") as pbar:
                    for chunk_path in pbar:
                        with open(chunk_path, 'rb') as chunk:
                            shutil.copyfileobj(chunk, outfile)
                        pbar.set_postfix(file=chunk_path.name)
                        
        except Exception as e:
            errors.append(f"Error merging chunks: {str(e)}")
            
        return FileHandlingResult(
            success=len(errors) == 0,
            chunks=[str(c) for c in chunks],
            checksums={},  # We don't generate checksums for merge operations
            errors=errors,
            warnings=warnings
        )

    def needs_splitting(self, file_path: Path) -> bool:
        """Check if file needs to be split."""
        if not file_path.exists():
            return False
        return file_path.stat().st_size > self.NDA_SIZE_LIMIT
