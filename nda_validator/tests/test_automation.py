# nda_validator/tests/test_automation.py
import pytest
from pathlib import Path
import pandas as pd
from nda_validator.utils.automation import validate_and_split_data

@pytest.fixture
def test_collection(tmp_path):
   # Create test collection structure
   collection_dir = tmp_path / 'collection'
   eeg_dir = collection_dir / 'eeg'
   eeg_dir.mkdir(parents=True)
   
   # Create sample EEG metadata
   metadata = pd.DataFrame({
       'subjectkey': ['NDARAB123456'],
       'src_subject_id': ['SUB001'],
       'interview_age': [240],
       'interview_date': ['2024-01-15'],
       'sex': ['F'],
       'experiment_id': ['EXP001'],
       'eeg_file': ['sub001.set']
   })
   metadata.to_csv(eeg_dir / 'metadata.csv', index=False)
   
   # Create dummy EEG file
   with open(eeg_dir / 'sub001.set', 'wb') as f:
       f.write(b'0' * (10 * 1024 * 1024))  # 10MB test file
       
   return collection_dir

def test_validate_and_split(test_collection, tmp_path):
   output_dir = tmp_path / 'output'
   results = validate_and_split_data(test_collection, output_dir)
   
   assert len(results['validations']) == 1
   assert results['validations'][0][0] == 'EEG'  # Data type
   assert results['validations'][0][1] == True   # Is valid
   assert len(results['validations'][0][2]) == 0 # No errors

# Add to test_automation.py
def test_validate_and_split_large_file(test_collection, tmp_path):
    eeg_dir = test_collection / 'eeg'
    
    # Create 3GB test file (larger than NDA limit)
    with open(eeg_dir / 'sub001.set', 'wb') as f:
        f.write(b'0' * (3 * 1024 * 1024 * 1024))
        
    output_dir = tmp_path / 'output'
    results = validate_and_split_data(test_collection, output_dir)
    
    assert len(results['splits']) > 0
    assert results['splits'][0][0] == 'EEG'
    assert len(list(Path(results['splits'][0][2][0]).parent.glob('*'))) > 1
