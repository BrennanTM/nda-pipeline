# nda_validator/validate.py
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from .validators import (
    BehavioralValidator,
    EEGValidator,
    MRIValidator,
    ResearchSubjectValidator,
    ValidationResult
)

class CollectionValidator:
    """Manages validation for entire NDA collections."""
    
    def __init__(self, collection_id: str):
        """Initialize validator with collection ID."""
        self.collection_id = collection_id
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
            
    def validate_collection(self, data_dir: Path, parallel: bool = True) -> Dict[str, ValidationResult]:
        """
        Validate all data types in a collection with parallel processing.
        
        Args:
            data_dir: Collection directory path
            parallel: Use parallel processing
            
        Returns:
            Dict mapping data types to their validation results
        """
        self.logger.info(f"Validating collection {self.collection_id}")
        
        validation_tasks = self._create_validation_tasks(data_dir)
        results = {}
        
        if parallel and len(validation_tasks) > 1:
            results = self._validate_parallel(validation_tasks)
        else:
            results = self._validate_sequential(validation_tasks)
            
        return self._summarize_results(results)
        
    def _create_validation_tasks(self, data_dir: Path) -> List[Tuple[str, type, Path]]:
        """Create validation tasks for each data type."""
        tasks = []
        
        # Required subject validation
        subject_file = data_dir / 'metadata' / 'research_subject.csv'
        if subject_file.exists():
            tasks.append(('subject', ResearchSubjectValidator, subject_file))
            
        # Data type specific validation
        data_types = {
            'behavioral': (BehavioralValidator, 'behavioral.csv'),
            'eeg': (EEGValidator, 'eeg.csv'),
            'mri': (MRIValidator, 'mri.csv')
        }
        
        for data_type, (validator_class, filename) in data_types.items():
            data_dir_type = data_dir / data_type
            file_path = data_dir_type / filename
            if file_path.exists():
                tasks.append((data_type, validator_class, file_path))
                
        if not tasks:
            self.logger.warning(f"No data files found in {data_dir}")
            
        return tasks
        
    def _validate_parallel(self, tasks: List[Tuple[str, type, Path]]) -> Dict[str, ValidationResult]:
        """Run validation tasks in parallel."""
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    self._run_validation, 
                    task_type, 
                    validator_class, 
                    file_path
                ): task_type
                for task_type, validator_class, file_path in tasks
            }
            
            with tqdm(total=len(futures), desc="Validating data types") as pbar:
                for future in futures:
                    task_type = futures[future]
                    try:
                        results[task_type] = future.result()
                    except Exception as e:
                        self.logger.error(f"Validation failed for {task_type}: {e}")
                        results[task_type] = ValidationResult(
                            is_valid=False,
                            errors=[f"Validation failed: {str(e)}"],
                            warnings=[],
                            metadata={}
                        )
                    pbar.update(1)
                    
        return results
        
    def _validate_sequential(self, tasks: List[Tuple[str, type, Path]]) -> Dict[str, ValidationResult]:
        """Run validation tasks sequentially with progress tracking."""
        results = {}
        with tqdm(tasks, desc="Validating data types") as pbar:
            for task_type, validator_class, file_path in pbar:
                try:
                    results[task_type] = self._run_validation(
                        task_type, 
                        validator_class, 
                        file_path
                    )
                except Exception as e:
                    self.logger.error(f"Validation failed for {task_type}: {e}")
                    results[task_type] = ValidationResult(
                        is_valid=False,
                        errors=[f"Validation failed: {str(e)}"],
                        warnings=[],
                        metadata={}
                    )
                pbar.set_postfix(type=task_type)
                
        return results
        
    def _run_validation(self, task_type: str, 
                       validator_class: type, 
                       file_path: Path) -> ValidationResult:
        """Run single validation task."""
        validator = validator_class(self.collection_id)
        
        # Handle different validator types
        if task_type == 'eeg':
            return validator.validate_file(file_path, file_path.parent)
        else:
            return validator.validate_file(file_path)
        
    def _summarize_results(self, results: Dict[str, ValidationResult]) -> Dict:
        """Create validation summary."""
        summary = {
            'all_valid': all(r.is_valid for r in results.values()),
            'results': results,
            'error_count': sum(len(r.errors) for r in results.values()),
            'warning_count': sum(len(r.warnings) for r in results.values()),
            'metadata': {
                data_type: result.metadata
                for data_type, result in results.items()
            }
        }
        
        # Log summary
        self.logger.info(f"Validation complete for {self.collection_id}")
        self.logger.info(f"All valid: {summary['all_valid']}")
        self.logger.info(f"Total errors: {summary['error_count']}")
        self.logger.info(f"Total warnings: {summary['warning_count']}")
        
        return summary
