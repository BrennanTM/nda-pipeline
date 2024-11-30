
# nda_validator/validators/behavioral.py
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging
from .base import NDAValidator

logger = logging.getLogger(__name__)

class BehavioralValidator(NDAValidator):
    """Validates behavioral data files for NDA submission."""
    
    VALID_EXTENSIONS = ['.csv', '.xlsx']
    
    def __init__(self, collection_id: str):
        """Initialize validator with specific collection requirements."""
        super().__init__(collection_id)
        
    def validate_file(self, file_path: Path, data_dir: Path = None) -> bool:
        """
        Validate a behavioral data file.
        
        Args:
            file_path: Path to the data file
            data_dir: Optional path to data directory
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        if not self._validate_file_format(file_path):
            return False
            
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            # Check required columns first
            missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                self.validation_errors.append(f"Missing required columns: {missing_cols}")
                return False
                
            # Run common field validations
            errors = self._validate_common_fields(df)
            if errors:
                self.validation_errors.extend(errors)
                return False
                
            # Run structure-specific validations
            if not self._validate_data_structure(df):
                return False
                
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reading file: {str(e)}")
            return False
    
    def _validate_file_format(self, file_path: Path) -> bool:
        """Validate file format and basic properties."""
        if not file_path.exists():
            self.validation_errors.append(f"File does not exist: {file_path}")
            return False
            
        if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
            self.validation_errors.append(
                f"Invalid file extension. Must be one of: {self.VALID_EXTENSIONS}"
            )
            return False
            
        if file_path.stat().st_size == 0:
            self.validation_errors.append("File is empty")
            return False
            
        return True
        
    def _validate_data_structure(self, df: pd.DataFrame) -> bool:
        """Validate the structure and content of the data."""
        is_valid = True
        
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.validation_errors.append(
                f"Missing required columns: {missing_cols}"
            )
            is_valid = False
        
        if not is_valid:
            return False
            
        # Validate with base validator
        errors = super()._validate_common_fields(df)
        if errors:
            self.validation_errors.extend(errors)
            return False
            
        return True

def validate_collection_data(collection_path: Path) -> dict:
    """
    Validate all behavioral data files in a collection directory.
    
    Args:
        collection_path: Path to collection directory
        
    Returns:
        dict: Validation results for each file
    """
    validator = BehavioralValidator(collection_path.name)
    results = {}
    
    behavioral_dir = collection_path / 'raw' / 'behavioral'
    if not behavioral_dir.exists():
        return {"error": f"Behavioral directory not found: {behavioral_dir}"}
        
    for file_path in behavioral_dir.glob('*.*'):
        if file_path.suffix.lower() in BehavioralValidator.VALID_EXTENSIONS:
            results[file_path.name] = {
                "valid": validator.validate_file(file_path),
                "errors": validator.validation_errors.copy()
            }
            validator.validation_errors = []  # Reset for next file
            
    return results
