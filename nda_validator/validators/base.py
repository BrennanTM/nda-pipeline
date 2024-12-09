# nda_validator/validators/base.py
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Structured validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, any]

class NDAValidator:
    """Enhanced base validator with comprehensive NDA requirements."""
    
    REQUIRED_COLUMNS = [
        'subjectkey',
        'src_subject_id', 
        'interview_age',
        'interview_date',
        'sex'
    ]
    
    # NDA-specific constraints
    GUID_PATTERNS = {
        'standard': r'^NDAR[A-Z0-9]{8}$',
        'pseudo': r'^NDAR_INV[A-Z0-9]{8}$'
    }
    
    MAX_AGE_MONTHS = 1200  # 100 years in months
    
    def __init__(self, collection_id: str):
        """Initialize validator with collection-specific settings."""
        self.collection_id = self._validate_collection_id(collection_id)
        self.logger = logging.getLogger(f"nda_validator.{self.__class__.__name__}")
        self.reset_validation_state()
        
    def reset_validation_state(self):
        """Reset validation state between runs."""
        self.result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            metadata={}
        )
        
    def _validate_collection_id(self, collection_id: str) -> str:
        """Validate NDA collection ID format."""
        if not re.match(r'^C\d{4}$', collection_id):
            raise ValueError(f"Invalid collection ID format: {collection_id}")
        return collection_id
        
    def validate_file(self, file_path: Path, data_dir: Optional[Path] = None) -> ValidationResult:
        """Validate file with comprehensive error checking."""
        self.reset_validation_state()
        
        try:
            if not self._validate_file_exists(file_path):
                return self.result
                
            df = self._read_file(file_path)
            if df is None:
                return self.result
                
            # Validate structure and content
            self._validate_structure(df)
            self._validate_common_fields(df)
            self._validate_specific_fields(df, data_dir)
            
            return self.result
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            self.result.is_valid = False
            self.result.errors.append(f"Unexpected error: {str(e)}")
            return self.result
            
    def _read_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read and perform initial data validation."""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                self.result.is_valid = False
                self.result.errors.append("File is empty")
                return None
            return df
        except Exception as e:
            self.result.is_valid = False
            self.result.errors.append(f"Error reading file: {str(e)}")
            return None
            
    def _validate_structure(self, df: pd.DataFrame):
        """Validate data structure against NDA requirements."""
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.result.is_valid = False
            self.result.errors.append(f"Missing required columns: {missing_cols}")
            
    def _validate_common_fields(self, df: pd.DataFrame):
        """Enhanced validation of common NDA fields."""
        # Validate GUIDs
        invalid_guids = df[~df['subjectkey'].apply(self.validate_guid)]
        if not invalid_guids.empty:
            self.result.is_valid = False
            self.result.errors.append(
                f"Invalid GUID format in rows: {invalid_guids.index.tolist()}"
            )
            
        # Validate interview_age
        if 'interview_age' in df.columns:
            invalid_ages = df[
                (df['interview_age'] < 0) |
                (df['interview_age'] > self.MAX_AGE_MONTHS) |
                (~df['interview_age'].astype(str).str.match(r'^\d+$'))
            ]
            if not invalid_ages.empty:
                self.result.is_valid = False
                self.result.errors.append(
                    f"Invalid interview_age values in rows: {invalid_ages.index.tolist()}"
                )
                
        # Validate interview_date
        if 'interview_date' in df.columns:
            try:
                dates = pd.to_datetime(df['interview_date'])
                future_dates = dates[dates > pd.Timestamp.now()]
                if not future_dates.empty:
                    self.result.is_valid = False
                    self.result.errors.append(
                        f"Future interview_date values in rows: {future_dates.index.tolist()}"
                    )
                    
                # Check date format (MM/DD/YYYY)
                invalid_format = ~df['interview_date'].astype(str).str.match(
                    r'^\d{2}/\d{2}/\d{4}$'
                )
                if invalid_format.any():
                    self.result.warnings.append(
                        "Some dates not in MM/DD/YYYY format"
                    )
                    
            except Exception:
                self.result.is_valid = False
                self.result.errors.append("Invalid interview_date format")
                
        # Validate sex values
        if 'sex' in df.columns:
            invalid_sex = df[~df['sex'].isin(['M', 'F'])]
            if not invalid_sex.empty:
                self.result.is_valid = False
                self.result.errors.append(
                    f"Invalid sex values: {invalid_sex['sex'].unique().tolist()}"
                )
                
    def validate_guid(self, guid: str) -> bool:
        """Enhanced GUID validation."""
        if pd.isna(guid):
            return False
            
        if guid.startswith('NDAR_INV'):
            return bool(re.match(self.GUID_PATTERNS['pseudo'], guid))
        return bool(re.match(self.GUID_PATTERNS['standard'], guid))
        
    def _validate_specific_fields(self, df: pd.DataFrame, data_dir: Optional[Path] = None):
        """Template method for data type specific validation."""
        pass
