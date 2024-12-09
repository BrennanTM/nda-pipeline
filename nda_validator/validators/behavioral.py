# nda_validator/validators/behavioral.py
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging
from .base import NDAValidator, ValidationResult

class BehavioralValidator(NDAValidator):
    """Validates behavioral data files for NDA submission."""
    
    VALID_EXTENSIONS = ['.csv', '.xlsx']
    
    # NDA-specific behavioral data requirements
    SCORE_RANGE = {
        'min_score': 0,
        'max_score': 100
    }
    
    def validate_file(self, file_path: Path, data_dir: Optional[Path] = None) -> ValidationResult:
        """
        Validate behavioral data file according to NDA standards.
        
        Args:
            file_path: Path to behavioral data file
            data_dir: Optional directory containing additional data
            
        Returns:
            ValidationResult with validation details
        """
        self.reset_validation_state()
        
        try:
            if not self._validate_file_format(file_path):
                return self.result
                
            df = self._read_behavioral_file(file_path)
            if df is None:
                return self.result
                
            self._validate_structure(df)
            if not self.result.is_valid:
                return self.result
                
            self._validate_common_fields(df)
            self._validate_behavioral_data(df)
            self._check_data_completeness(df)
            
            # Add metadata for reporting
            self.result.metadata.update({
                'total_records': len(df),
                'missing_data_summary': self._get_missing_data_summary(df),
                'score_statistics': self._get_score_statistics(df)
            })
            
            return self.result
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            self.result.is_valid = False
            self.result.errors.append(f"Unexpected error: {str(e)}")
            return self.result
            
    def _validate_file_format(self, file_path: Path) -> bool:
        """Validate file format and accessibility."""
        if not file_path.exists():
            self.result.is_valid = False
            self.result.errors.append(f"File not found: {file_path}")
            return False
            
        if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
            self.result.is_valid = False
            self.result.errors.append(
                f"Invalid file type. Must be one of: {self.VALID_EXTENSIONS}"
            )
            return False
            
        return True
        
    def _read_behavioral_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read behavioral data with appropriate handling."""
        try:
            if file_path.suffix.lower() == '.csv':
                return pd.read_csv(file_path)
            return pd.read_excel(file_path)
        except Exception as e:
            self.result.is_valid = False
            self.result.errors.append(f"Error reading file: {str(e)}")
            return None
            
    def _validate_behavioral_data(self, df: pd.DataFrame):
        """Validate behavioral-specific data requirements."""
        # Validate score ranges if present
        score_columns = [col for col in df.columns if 'score' in col.lower()]
        for col in score_columns:
            invalid_scores = df[
                (df[col] < self.SCORE_RANGE['min_score']) |
                (df[col] > self.SCORE_RANGE['max_score'])
            ]
            if not invalid_scores.empty:
                self.result.is_valid = False
                self.result.errors.append(
                    f"Invalid {col} values in rows: {invalid_scores.index.tolist()}"
                )
                
    def _check_data_completeness(self, df: pd.DataFrame):
        """Check for missing or incomplete data."""
        for column in df.columns:
            missing_count = df[column].isna().sum()
            if missing_count > 0:
                missing_percent = (missing_count / len(df)) * 100
                if missing_percent > 10:  # More than 10% missing
                    self.result.warnings.append(
                        f"High missing data rate in {column}: {missing_percent:.1f}%"
                    )
                    
    def _get_missing_data_summary(self, df: pd.DataFrame) -> Dict:
        """Generate missing data summary."""
        return {
            column: {
                'missing_count': int(df[column].isna().sum()),
                'missing_percentage': float(df[column].isna().mean() * 100)
            }
            for column in df.columns
        }
        
    def _get_score_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate score statistics for reporting."""
        score_columns = [col for col in df.columns if 'score' in col.lower()]
        return {
            column: {
                'mean': float(df[column].mean()),
                'std': float(df[column].std()),
                'min': float(df[column].min()),
                'max': float(df[column].max())
            }
            for column in score_columns if df[column].dtype in ['int64', 'float64']
        }
