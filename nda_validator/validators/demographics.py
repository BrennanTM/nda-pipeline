from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging
from .base import NDAValidator, ValidationResult

logger = logging.getLogger(__name__)

class DemographicsValidator(NDAValidator):
    """Enhanced validator for NDA Demographics data structure."""
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        self.required_fields = [
            'subjectkey',
            'src_subject_id',
            'interview_age',
            'interview_date',
            'sex',
            'race',
            'ethnicity',
            'education',
            'employment_status',
            'gender_identity'
        ]
        self.valid_races = [
            'White', 
            'Black or African American',
            'Asian',
            'American Indian or Alaska Native',
            'Native Hawaiian or Other Pacific Islander',
            'Other'
        ]
        self.valid_ethnicities = [
            'Hispanic',
            'Non-hispanic'
        ]
        self.valid_education_levels = [
            'Less than high school',
            'High school graduate',
            'Some college',
            "Bachelor's degree",
            'Graduate degree'
        ]
    
    def validate_file(self, file_path: Path, data_dir: Optional[Path] = None) -> ValidationResult:
        """Validate demographics data file with enhanced error reporting."""
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Check file exists
            if not file_path.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"File not found: {file_path}"],
                    warnings=[],
                    metadata={}
                )

            # Read file
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Error reading file: {str(e)}"],
                    warnings=[],
                    metadata={}
                )

            # Validate required fields
            missing_fields = [field for field in self.required_fields if field not in df.columns]
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Missing required fields: {', '.join(missing_fields)}"],
                    warnings=[],
                    metadata={}
                )

            # Validate demographics fields
            if 'race' in df.columns:
                invalid_races = df[~df['race'].isin(self.valid_races)]
                if not invalid_races.empty:
                    errors.append(
                        f"Invalid race values: {invalid_races['race'].unique().tolist()}"
                    )

            if 'ethnicity' in df.columns:
                invalid_ethnicities = df[~df['ethnicity'].isin(self.valid_ethnicities)]
                if not invalid_ethnicities.empty:
                    errors.append(
                        f"Invalid ethnicity values: {invalid_ethnicities['ethnicity'].unique().tolist()}"
                    )

            if 'gender_identity' in df.columns:
                invalid_gender = df[~df['gender_identity'].isin([1, 2])]
                if not invalid_gender.empty:
                    errors.append(
                        f"Invalid gender_identity values in rows: {invalid_gender.index.tolist()}"
                    )

            # Collect metadata if no errors
            if len(errors) == 0:
                metadata = {
                    'total_subjects': len(df)
                }
                for column in ['race', 'ethnicity', 'gender_identity']:
                    if column in df.columns:
                        metadata[f'{column}_distribution'] = df[column].value_counts().to_dict()

        except Exception as e:
            logger.error(f"Demographics validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                metadata={}
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
