# nda_validator/tests/test_eeg.py
import pytest
from pathlib import Path
import pandas as pd
from nda_validator.validators import EEGValidator

@pytest.fixture
def eeg_validator():
    return EEGValidator('C4223')

@pytest.fixture
def sample_eeg_metadata():
    return pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['2024-01-15', '2024-01-16'],
        'sex': ['F', 'M'],
        'experiment_id': ['EXP001', 'EXP002'],
        'eeg_file': ['sub001.set', 'sub002.set']
    })

def test_valid_eeg_metadata(tmp_path, eeg_validator, sample_eeg_metadata):
    metadata_file = tmp_path / "valid_metadata.csv"
    sample_eeg_metadata.to_csv(metadata_file, index=False)
    
    assert eeg_validator.validate_file(metadata_file)