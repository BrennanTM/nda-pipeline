# nda_validator/utils/automation.py
from pathlib import Path
from ..validators import EEGValidator, MRIValidator
from .file_handler import LargeFileHandler

def validate_and_split_data(collection_path: Path, output_dir: Path):
    results = {
        'validations': [],
        'splits': []
    }
    
    # Validate EEG data
    eeg_validator = EEGValidator('C4223')
    eeg_metadata = collection_path / 'eeg' / 'metadata.csv'
    if eeg_metadata.exists():
        is_valid = eeg_validator.validate_file(eeg_metadata, collection_path / 'eeg')
        results['validations'].append(('EEG', is_valid, eeg_validator.validation_errors))
        
        # Split large files
        if is_valid:
            for eeg_file in (collection_path / 'eeg').glob('*.*'):
                if eeg_file.suffix in ['.set', '.fdt'] and \
                   eeg_file.stat().st_size > (2.5 * 1024 * 1024 * 1024):
                    split_dir = output_dir / 'eeg' / eeg_file.stem
                    LargeFileHandler.split_large_file(eeg_file, split_dir)
                    results['splits'].append(('EEG', eeg_file.name, list(split_dir.glob('*'))))
    
    return results