import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from .base import NDAValidator, ValidationResult

logger = logging.getLogger(__name__)

class MRIValidator(NDAValidator):
    """Validates MRI data files for NDA submission."""
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        self.required_fields = [
            'subjectkey',
            'src_subject_id',
            'interview_age',
            'interview_date',
            'sex',
            'image_file',      # Path to MRI data file
            'image_type',      # Type of MRI scan
            'acquisition_date' # Date of scan
        ]
        self.valid_extensions = ['.nii', '.nii.gz', '.dcm']
        self.valid_image_types = ['T1', 'T2', 'fMRI', 'DTI']
    
    def validate_file(self, metadata_path: Path, data_dir: Optional[Path] = None) -> ValidationResult:
        """
        Validate MRI metadata and data files with comprehensive checking.
        
        Args:
            metadata_path: Path to MRI metadata CSV
            data_dir: Optional directory containing MRI data files
            
        Returns:
            ValidationResult containing validation details
        """
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Check file exists
            if not metadata_path.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"File not found: {metadata_path}"],
                    warnings=[],
                    metadata={}
                )

            # Read file
            try:
                df = pd.read_csv(metadata_path)
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

            # Validate MRI metadata
            invalid_types = df[~df['image_type'].isin(self.valid_image_types)]
            if not invalid_types.empty:
                errors.append(
                    f"Invalid image types: {invalid_types['image_type'].unique().tolist()}"
                )

            # Validate acquisition dates
            try:
                dates = pd.to_datetime(df['acquisition_date'])
                future_dates = dates[dates > pd.Timestamp.now()]
                if not future_dates.empty:
                    errors.append(
                        f"Future acquisition dates in rows: {future_dates.index.tolist()}"
                    )
            except Exception:
                errors.append("Invalid acquisition_date format")

            # Validate image files if data_dir provided
            if data_dir:
                for idx, row in df.iterrows():
                    if pd.isna(row['image_file']):
                        errors.append(
                            f"Missing image_file path for subject {row['subjectkey']} in row {idx + 1}"
                        )
                        continue
                    
                    file_path = data_dir / row['image_file']
                    if not file_path.exists():
                        errors.append(f"Image file not found: {file_path}")
                        continue
                    
                    if not any(str(file_path).lower().endswith(ext) for ext in self.valid_extensions):
                        errors.append(
                            f"Invalid image format for {file_path}"
                        )
                    
                    # Check file size
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb < 1:  # Less than 1MB
                        warnings.append(
                            f"Suspicious file size ({size_mb:.2f}MB) for {file_path}"
                        )

            # Collect metadata if no errors
            if len(errors) == 0:
                metadata = {
                    'total_scans': len(df),
                    'image_type_distribution': df['image_type'].value_counts().to_dict(),
                    'acquisition_date_range': {
                        'start': df['acquisition_date'].min(),
                        'end': df['acquisition_date'].max()
                    }
                }

        except Exception as e:
            logger.error(f"MRI validation error: {str(e)}")
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
