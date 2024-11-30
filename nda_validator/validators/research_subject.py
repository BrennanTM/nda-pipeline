# nda_validator/validators/research_subject.py
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from .base import NDAValidator  # Add this import

logger = logging.getLogger(__name__)

class ResearchSubjectValidator(NDAValidator):
    """Validator for Research Subject and Pedigree data structure."""
    
    STRUCTURE_COLUMNS = [
        'phenotype',
        'phenotype_description',
        'twins_study',
        'sibling_study', 
        'family_study'
    ]
    
    def __init__(self, collection_id: str):
        """Initialize validator with collection ID."""
        super().__init__(collection_id)
        
    def validate_file(self, file_path: Path, data_dir: Path = None) -> bool:
        """Validate a research subject data file."""
        try:
            df = pd.read_csv(file_path)
            
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
            if not self._validate_structure_fields(df):
                return False
                
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reading file: {str(e)}")
            return False
            
    def _validate_structure_fields(self, df: pd.DataFrame) -> bool:
        """Validate structure-specific fields."""
        is_valid = True
        
        # Validate boolean fields
        bool_fields = ['twins_study', 'sibling_study', 'family_study']
        for field in bool_fields:
            if field in df.columns:
                invalid_vals = df[~df[field].isin([0, 1])]
                if not invalid_vals.empty:
                    self.validation_errors.append(
                        f"Invalid {field} values found in rows: {invalid_vals.index.tolist()}"
                    )
                    is_valid = False
        
        return is_valid
