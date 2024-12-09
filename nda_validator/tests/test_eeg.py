# nda_validator/tests/test_eeg.py
import pytest
from pathlib import Path
import pandas as pd
from nda_validator.validators import EEGValidator

@pytest.fixture
def sample_eeg_metadata():
    """Create sample EEG metadata."""
    return pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['01/15/2024', '01/16/2024'],
        'sex': ['F', 'M'],
        'experiment_id': ['E123456', 'E789012'],
        'eeg_file': ['sub001.set', 'sub002.set']
    })

def test_eeg_validation_with_files(tmp_path, sample_eeg_metadata):
    """Test EEG validation with actual data files."""
    # Setup
    validator = EEGValidator('C4223')
    data_dir = tmp_path / "eeg_data"
    data_dir.mkdir()
    
    # Create dummy EEG files
    for filename in ['sub001.set', 'sub002.set']:
        with open(data_dir / filename, 'wb') as f:
            f.write(b'EEG data')
            
    # Save metadata
    metadata_file = data_dir / "metadata.csv"
    sample_eeg_metadata.to_csv(metadata_file, index=False)
    
    # Test
    result = validator.validate_file(metadata_file, data_dir)
    assert result.is_valid
    assert 'total_files' in result.metadata
    assert 'experiment_distribution' in result.metadata
