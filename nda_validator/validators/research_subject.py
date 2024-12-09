
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging
import numpy as np

from .base import NDAValidator, ValidationResult

logger = logging.getLogger(__name__)

class ResearchSubjectValidator(NDAValidator):
    """Validates research subject data for NDA submission."""
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        self.required_fields = [
            'subjectkey',
            'src_subject_id',
            'interview_age',
            'interview_date',
            'sex'
        ]
        self.guid_pattern = r'^NDAR_INV[A-Z0-9]{8}$'
        self.max_age_months = 1200  # 100 years in months
        self.date_format = '%m/%d/%Y'
        self.allowed_sex_values = ['M', 'F']
    
    def validate_guid(self, guid: str, row_idx: int) -> Optional[str]:
        """Validates GUID format."""
        if not pd.isna(guid) and not pd.Series(guid).str.match(self.guid_pattern).iloc[0]:
            return f"Invalid GUID format in row {row_idx + 1}: {guid}"
        return None

    def validate_age(self, age: int, row_idx: int) -> Optional[str]:
        """Validates interview age is within acceptable range."""
        try:
            age_val = float(age)
            if not 0 <= age_val <= self.max_age_months:
                return f"Invalid interview age in row {row_idx + 1}: {age}"
        except (ValueError, TypeError):
            return f"Invalid interview age format in row {row_idx + 1}: {age}"
        return None

    def validate_date(self, date_str: str, row_idx: int) -> Optional[str]:
        """Validates date format."""
        if pd.isna(date_str):
            return f"Missing interview date in row {row_idx + 1}"
        try:
            datetime.strptime(str(date_str), self.date_format)
        except ValueError:
            return f"Invalid date format in row {row_idx + 1}: {date_str}. Expected format: MM/DD/YYYY"
        return None

    def validate_sex(self, sex: str, row_idx: int) -> Optional[str]:
        """Validates sex value."""
        if pd.isna(sex) or str(sex).upper() not in self.allowed_sex_values:
            return f"Invalid sex value in row {row_idx + 1}: {sex}. Must be 'M' or 'F'"
        return None

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validates a research subject metadata file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            ValidationResult with validation outcome
        """
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

            # Validate each row
            for idx, row in df.iterrows():
                # GUID validation
                guid_error = self.validate_guid(row['subjectkey'], idx)
                if guid_error:
                    errors.append(guid_error)

                # Age validation
                age_error = self.validate_age(row['interview_age'], idx)
                if age_error:
                    errors.append(age_error)

                # Date validation
                date_error = self.validate_date(row['interview_date'], idx)
                if date_error:
                    errors.append(date_error)

                # Sex validation
                sex_error = self.validate_sex(row['sex'], idx)
                if sex_error:
                    errors.append(sex_error)

                # Subject ID validation
                if pd.isna(row['src_subject_id']) or str(row['src_subject_id']).strip() == '':
                    errors.append(f"Missing subject ID in row {idx + 1}")

            # Collect metadata
            if len(errors) == 0:
                metadata = {
                    'total_subjects': len(df),
                    'sex_distribution': df['sex'].value_counts().to_dict(),
                    'age_statistics': {
                        'min_age_months': float(df['interview_age'].min()),
                        'max_age_months': float(df['interview_age'].max()),
                        'mean_age_months': float(df['interview_age'].mean()),
                        'median_age_months': float(df['interview_age'].median())
                    },
                    'date_range': {
                        'earliest': df['interview_date'].min(),
                        'latest': df['interview_date'].max()
                    }
                }

                # Add warnings for potential data quality issues
                if len(df) != len(df['subjectkey'].unique()):
                    warnings.append("Duplicate subject keys found")
                
                if df['interview_age'].std() > 240:  # 20 years in months
                    warnings.append("Large age variation detected")

        except Exception as e:
            logger.error(f"Validation error in {file_path}: {str(e)}")
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

    def get_validation_summary(self, result: ValidationResult) -> Dict:
        """
        Creates a summary of the validation results.
        
        Args:
            result: ValidationResult object
            
        Returns:
            Dictionary containing validation summary
        """
        return {
            'status': 'valid' if result.is_valid else 'invalid',
            'error_count': len(result.errors),
            'warning_count': len(result.warnings),
            'subject_count': result.metadata.get('total_subjects', 0),
            'sex_distribution': result.metadata.get('sex_distribution', {}),
            'age_statistics': result.metadata.get('age_statistics', {}),
            'date_range': result.metadata.get('date_range', {})
        }
