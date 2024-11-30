import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from .base import NDAValidator

logger = logging.getLogger(__name__)

class EEGValidator(NDAValidator):
    """Validates EEG data files for NDA submission."""
    
    REQUIRED_COLUMNS = [
        'subjectkey',
        'src_subject_id', 
        'interview_age',
        'interview_date',
        'sex',
        'experiment_id',  # Required for EEG
        'eeg_file'       # Path to EEG data file
    ]
    
    VALID_EXTENSIONS = ['.set', '.fdt', '.mat']
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        
    # nda_validator/validators/eeg.py
    def validate_file(self, metadata_path: Path, data_dir: Path = None) -> bool:
        """Validate EEG metadata and optionally the referenced data files."""
        try:
            df = pd.read_csv(metadata_path)
            
            # Check required columns
            missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                self.validation_errors.append(f"Missing required columns: {missing_cols}")
                return False
                
            # Run common field validations
            common_errors = self._validate_common_fields(df)
            if common_errors:
                self.validation_errors.extend(common_errors)
                return False
                
            # Check experiment IDs
            if df['experiment_id'].isna().any():
                self.validation_errors.append("Missing experiment_id values")
                return False
                
            # Validate EEG files if data_dir provided
            if data_dir and not self._validate_eeg_files(df, data_dir):
                return False
                
            return True
                
        except Exception as e:
            self.validation_errors.append(f"Error reading file: {str(e)}")
            return False
            
    def _validate_eeg_files(self, df: pd.DataFrame, data_dir: Path) -> bool:
        """Validate referenced EEG data files exist and are valid."""
        is_valid = True
        
        for _, row in df.iterrows():
            if pd.isna(row['eeg_file']):
                self.validation_errors.append(f"Missing eeg_file path for subject {row['subjectkey']}")
                is_valid = False
                continue
                
            file_path = data_dir / row['eeg_file']
            if not file_path.exists():
                self.validation_errors.append(f"EEG file not found: {file_path}")
                is_valid = False
                continue
                
            if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
                self.validation_errors.append(
                    f"Invalid EEG file format {file_path.suffix} for {file_path}"
                )
                is_valid = False
                
        return is_valid
