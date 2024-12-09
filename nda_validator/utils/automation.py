from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from tqdm import tqdm
import yaml
from concurrent.futures import ThreadPoolExecutor

from ..validators import (
    EEGValidator, 
    MRIValidator, 
    BehavioralValidator, 
    ResearchSubjectValidator
)
from .file_handler import LargeFileHandler

class NDAAutomation:
    """Automated validation and processing for NDA data submission."""
    
    # NDA file size threshold (2.5GB)
    SIZE_THRESHOLD = 2.5 * 1024 * 1024 * 1024
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.file_handler = LargeFileHandler()
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from YAML file."""
        if not config_path:
            config_path = Path(__file__).parent.parent / 'config' / 'nda_config.yaml'
            
        with open(config_path) as f:
            return yaml.safe_load(f)
            
    def process_collection(self, collection_id: str, 
                         collection_path: Path, 
                         output_dir: Path) -> Dict:
        """
        Process all data for a specific collection.
        
        Args:
            collection_id: NDA collection ID (e.g., 'C4223')
            collection_path: Path to collection data
            output_dir: Path for processed outputs
            
        Returns:
            Dict containing validation results and processing details
        """
        self.logger.info(f"Processing collection {collection_id}")
        
        results = {
            'collection_id': collection_id,
            'validations': [],
            'splits': [],
            'errors': []
        }
        
        try:
            # Validate research subject data first
            subject_results = self._validate_subject_data(collection_id, collection_path)
            results['validations'].append({
                'type': 'subject',
                'is_valid': subject_results.is_valid,
                'errors': subject_results.errors,
                'warnings': subject_results.warnings,
                'metadata': subject_results.metadata
            })
            
            if not subject_results.is_valid:
                self.logger.error("Subject validation failed, stopping processing")
                return results
                
            # Process each data type
            data_types = self._get_data_types(collection_path)
            for data_type in data_types:
                type_results = self._process_data_type(
                    collection_id, 
                    collection_path, 
                    output_dir, 
                    data_type
                )
                results['validations'].extend(type_results.get('validations', []))
                results['splits'].extend(type_results.get('splits', []))
                results['errors'].extend(type_results.get('errors', []))
                
        except Exception as e:
            self.logger.error(f"Error processing collection {collection_id}: {str(e)}")
            results['errors'].append(str(e))
            
        return results
        
    def _validate_subject_data(self, collection_id: str, collection_path: Path):
        """Validate research subject metadata."""
        validator = ResearchSubjectValidator(collection_id)
        subject_file = collection_path / 'metadata' / 'research_subject.csv'
        
        if not subject_file.exists():
            return {
                'is_valid': False,
                'errors': ['Research subject file not found'],
                'warnings': [],
                'metadata': {}
            }
            
        return validator.validate_file(subject_file)
        
    def _get_data_types(self, collection_path: Path) -> List[str]:
        """Identify available data types in collection."""
        data_types = []
        for data_type in ['eeg', 'mri', 'behavioral']:
            if (collection_path / data_type).exists():
                data_types.append(data_type)
        return data_types
        
    def _process_data_type(self, collection_id: str, 
                          collection_path: Path, 
                          output_dir: Path, 
                          data_type: str) -> Dict:
        """Process specific data type within collection."""
        results = {
            'validations': [],
            'splits': [],
            'errors': []
        }
        
        try:
            # Select appropriate validator
            validator = self._get_validator(data_type, collection_id)
            if not validator:
                results['errors'].append(f"No validator found for {data_type}")
                return results
                
            # Validate metadata
            metadata_file = collection_path / data_type / 'metadata.csv'
            if metadata_file.exists():
                validation_result = validator.validate_file(
                    metadata_file, 
                    collection_path / data_type
                )
                results['validations'].append({
                    'type': data_type,
                    'is_valid': validation_result.is_valid,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'metadata': validation_result.metadata
                })
                
                # Process large files if validation passed
                if validation_result.is_valid:
                    self._process_large_files(
                        collection_path / data_type,
                        output_dir / data_type,
                        data_type,
                        results
                    )
                    
        except Exception as e:
            error_msg = f"Error processing {data_type}: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            
        return results
        
    def _get_validator(self, data_type: str, collection_id: str):
        """Get appropriate validator for data type."""
        validators = {
            'eeg': EEGValidator,
            'mri': MRIValidator,
            'behavioral': BehavioralValidator
        }
        return validators.get(data_type, None)(collection_id)
        
    def _process_large_files(self, data_dir: Path, 
                           output_dir: Path, 
                           data_type: str, 
                           results: Dict):
        """Process large files for a specific data type."""
        extensions = {
            'eeg': ['.set', '.fdt'],
            'mri': ['.nii', '.nii.gz'],
            'behavioral': ['.csv', '.xlsx']
        }
        
        valid_extensions = extensions.get(data_type, [])
        
        for file_path in data_dir.glob('*.*'):
            if (file_path.suffix in valid_extensions and 
                file_path.stat().st_size > self.SIZE_THRESHOLD):
                try:
                    split_dir = output_dir / file_path.stem
                    self.file_handler.split_large_file(file_path, split_dir)
                    results['splits'].append({
                        'type': data_type,
                        'filename': file_path.name,
                        'chunks': list(str(p) for p in split_dir.glob('*'))
                    })
                except Exception as e:
                    results['errors'].append(
                        f"Error splitting {file_path.name}: {str(e)}"
                    )

def validate_all_collections(base_path: Path, output_dir: Path) -> Dict:
    """
    Validate and process all NDA collections.
    
    Args:
        base_path: Base directory containing all collections
        output_dir: Directory for processed outputs
        
    Returns:
        Dict with results for all collections
    """
    automation = NDAAutomation()
    results = {}
    
    # Process each collection in parallel
    with ThreadPoolExecutor() as executor:
        futures = {}
        for collection_dir in base_path.glob('C*'):
            if collection_dir.is_dir():
                collection_id = collection_dir.name
                futures[executor.submit(
                    automation.process_collection,
                    collection_id,
                    collection_dir,
                    output_dir / collection_id
                )] = collection_id
                
        # Gather results with progress tracking
        with tqdm(total=len(futures), desc="Processing collections") as pbar:
            for future in futures:
                collection_id = futures[future]
                try:
                    results[collection_id] = future.result()
                except Exception as e:
                    results[collection_id] = {
                        'collection_id': collection_id,
                        'error': str(e)
                    }
                pbar.update(1)
                
    return results
