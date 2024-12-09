from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging
from .base import NDAValidator, ValidationResult

logger = logging.getLogger(__name__)

class EEGValidator(NDAValidator):
    """Validates EEG data files for NDA submission."""
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        self.required_fields = [
            'subjectkey',
            'src_subject_id',
            'interview_age',
            'interview_date',
            'sex',
            'experiment_id',
            'eeg_file'
        ]
    
    def validate_file(self, metadata_path: Path, data_dir: Optional[Path] = None) -> ValidationResult:
        """
        Validates an EEG metadata file and its associated data files.
        
        Args:
            metadata_path: Path to the metadata CSV file
            data_dir: Optional directory containing the EEG data files
            
        Returns:
            ValidationResult with validation outcome
        """
        errors = []
        warnings = []
        metadata = {}
        
        try:
            if not metadata_path.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Metadata file not found: {metadata_path}"],
                    warnings=[],
                    metadata={}
                )
            
            df = pd.read_csv(metadata_path)
            
            # Validate required fields
            missing_fields = [field for field in self.required_fields if field not in df.columns]
            if missing_fields:
                errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            
            if not errors:
                # Validate each row
                for idx, row in df.iterrows():
                    # Validate EEG file exists if data_dir provided
                    if data_dir and 'eeg_file' in row:
                        eeg_file = data_dir / row['eeg_file']
                        if not eeg_file.exists():
                            errors.append(f"EEG file not found: {row['eeg_file']}")
                    
                    # Validate experiment_id format (assuming format requirements)
                    if not str(row['experiment_id']).startswith('EXP'):
                        errors.append(f"Invalid experiment_id format in row {idx + 1}: {row['experiment_id']}")
                
                # Collect metadata
                metadata = {
                    'total_files': len(df),
                    'unique_experiments': df['experiment_id'].nunique(),
                    'file_types': df['eeg_file'].str.split('.').str[-1].value_counts().to_dict()
                }
        
        except Exception as e:
            errors.append(f"EEG validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
