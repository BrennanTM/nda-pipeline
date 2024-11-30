# nda_validator/validators/base.py
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict, Optional
from datetime import datetime

class NDAValidator:
    """Base validator class for all NDA data types."""
    
    REQUIRED_COLUMNS = [
        'subjectkey',
        'src_subject_id', 
        'interview_age',
        'interview_date',
        'sex'
    ]
    
    def __init__(self, collection_id: str):
        self.collection_id = collection_id
        self.validation_errors = []
        self.validation_warnings = []
        
    def validate_guid(self, guid: str) -> bool:
        """Validate NDA GUID format including pseudoGUIDs."""
        if pd.isna(guid):
            return False
        if guid.startswith('NDAR_INV'):
            return bool(re.match(r'^NDAR_INV[A-Z0-9]{8}$', guid))
        return bool(re.match(r'^NDAR[A-Z0-9]{8}$', guid))
    
    def _validate_common_fields(self, df: pd.DataFrame) -> List[str]:
        """Validate fields common to all NDA data types."""
        errors = []
        
        # Validate GUIDs
        invalid_guids = df[~df['subjectkey'].apply(self.validate_guid)]
        if not invalid_guids.empty:
            errors.append(f"Invalid GUID format in rows: {invalid_guids.index.tolist()}")
        
        # Validate interview_age (in months)
        if 'interview_age' in df.columns:
            invalid_ages = df[
                (df['interview_age'] < 0) |
                (df['interview_age'] > 1200)  # 100 years in months
            ]
            if not invalid_ages.empty:
                errors.append(f"Invalid interview_age values in rows: {invalid_ages.index.tolist()}")
        
        # Validate interview_date
        if 'interview_date' in df.columns:
            try:
                dates = pd.to_datetime(df['interview_date'])
                future_dates = dates[dates > pd.Timestamp.now()]
                if not future_dates.empty:
                    errors.append(f"Future interview_date values found in rows: {future_dates.index.tolist()}")
            except Exception:
                errors.append("Invalid interview_date format")
        
        # Validate sex values
        if 'sex' in df.columns:
            invalid_sex = df[~df['sex'].isin(['M', 'F'])]
            if not invalid_sex.empty:
                errors.append(f"Invalid sex values found: {invalid_sex['sex'].unique().tolist()}")
        
        return errors

    def get_validation_errors(self) -> list:
        """Return list of validation errors."""
        return self.validation_errors.copy()
