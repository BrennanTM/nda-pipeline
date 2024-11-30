# nda_validator/validators/demographics.py
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from .base import NDAValidator

logger = logging.getLogger(__name__)

class DemographicsValidator(NDAValidator):
    """Validator for Demographics data structure."""
    
    STRUCTURE_COLUMNS = [
        'race',
        'ethnicity',
        'education',
        'employment_status',
        'gender_identity'
    ]

    VALID_RACES = [
        'White', 
        'Black or African American',
        'Asian',
        'American Indian or Alaska Native',
        'Native Hawaiian or Other Pacific Islander',
        'Other'
    ]

    VALID_ETHNICITIES = [
        'Hispanic',
        'Non-hispanic'
    ]

    def validate_file(self, file_path: Path, data_dir: Path = None) -> bool:
        """Validate demographics data file."""
        try:
            df = pd.read_csv(file_path)
            
            # Check required columns
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
        # Validate race
        if 'race' in df.columns:
            invalid_races = df[~df['race'].isin(self.VALID_RACES)]
            if not invalid_races.empty:
                self.validation_errors.append(
                    f"Invalid race values found: {invalid_races['race'].unique().tolist()}"
                )
                return False

        # Validate ethnicity
        if 'ethnicity' in df.columns:
            invalid_ethnicities = df[~df['ethnicity'].isin(self.VALID_ETHNICITIES)]
            if not invalid_ethnicities.empty:
                self.validation_errors.append(
                    f"Invalid ethnicity values found: {invalid_ethnicities['ethnicity'].unique().tolist()}"
                )
                return False

        # Validate gender_identity (1 = Male, 2 = Female, per template)
        if 'gender_identity' in df.columns:
            invalid_gender = df[~df['gender_identity'].isin([1, 2])]
            if not invalid_gender.empty:
                self.validation_errors.append(
                    f"Invalid gender_identity values. Must be 1 or 2. Found in rows: {invalid_gender.index.tolist()}"
                )
                return False

        return True
