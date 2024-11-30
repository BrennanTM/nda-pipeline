import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from .base import NDAValidator

logger = logging.getLogger(__name__)

class MRIValidator(NDAValidator):
    """Validates MRI data files for NDA submission."""
    
    REQUIRED_COLUMNS = [
        'subjectkey',
        'src_subject_id',
        'interview_age',
        'interview_date',
        'sex',
        'image_file',      # Path to MRI data file
        'image_type',      # Type of MRI scan
        'acquisition_date' # Date of scan
    ]
    
    VALID_EXTENSIONS = ['.nii', '.nii.gz', '.dcm']
    VALID_IMAGE_TYPES = ['T1', 'T2', 'fMRI', 'DTI']
    
    def __init__(self, collection_id: str):
        super().__init__(collection_id)
        
    def validate_file(self, metadata_path: Path, data_dir: Path = None) -> bool:
        """
        Validate MRI metadata and optionally the referenced data files.
        
        Args:
            metadata_path: Path to MRI metadata CSV
            data_dir: Optional directory containing MRI data files
        """
        if not self._validate_file_format(metadata_path):
            return False
            
        try:
            df = pd.read_csv(metadata_path)
            
            # Validate basic structure
            if not self._validate_data_structure(df):
                return False
                
            # Validate image types
            invalid_types = df[~df['image_type'].isin(self.VALID_IMAGE_TYPES)]
            if not invalid_types.empty:
                self.validation_errors.append(
                    f"Invalid image types found: {invalid_types['image_type'].unique().tolist()}"
                )
                return False
                
            # Validate acquisition dates
            try:
                pd.to_datetime(df['acquisition_date'])
            except Exception:
                self.validation_errors.append("Invalid acquisition_date format")
                return False
                
            # If data directory provided, validate image files
            if data_dir:
                if not self._validate_image_files(df, data_dir):
                    return False
                    
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reading file: {str(e)}")
            return False
            
    def _validate_image_files(self, df: pd.DataFrame, data_dir: Path) -> bool:
        """Validate referenced MRI data files exist and are valid."""
        is_valid = True
        
        for _, row in df.iterrows():
            if pd.isna(row['image_file']):
                self.validation_errors.append(f"Missing image_file path for subject {row['subjectkey']}")
                is_valid = False
                continue
                
            file_path = data_dir / row['image_file']
            if not file_path.exists():
                self.validation_errors.append(f"Image file not found: {file_path}")
                is_valid = False
                continue
                
            if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
                self.validation_errors.append(
                    f"Invalid image file format {file_path.suffix} for {file_path}"
                )
                is_valid = False
                
        return is_valid
