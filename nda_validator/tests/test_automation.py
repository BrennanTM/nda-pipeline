# nda_validator/tests/test_automation.py
import pytest
from pathlib import Path
import pandas as pd
from nda_validator.utils.automation import NDAAutomation

@pytest.fixture
def test_collection(tmp_path):
    """Create test collection structure."""
    collection_dir = tmp_path / 'collection'
    
    # Create directories
    for subdir in ['eeg', 'mri', 'behavioral', 'metadata']:
        (collection_dir / subdir).mkdir(parents=True)
        
    # Create sample metadata
    metadata = pd.DataFrame({
        'subjectkey': ['NDARAB123456'],
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['01/15/2024'],
        'sex': ['F']
    })
    
    metadata.to_csv(collection_dir / 'metadata' / 'research_subject.csv', index=False)
    return collection_dir

def test_collection_processing(test_collection, tmp_path):
    """Test full collection processing."""
    automation = NDAAutomation()
    output_dir = tmp_path / 'output'
    
    results = automation.process_collection(
        'C4223',
        test_collection,
        output_dir
    )
    
    assert 'validations' in results
    assert 'errors' in results
    assert len(results['validations']) > 0

def test_parallel_processing(test_collection, tmp_path):
    """Test parallel processing of multiple collections."""
    # Create multiple test collections
    collections = {}
    for cid in ['C3996', 'C4223', 'C4819', 'C5096']:
        collection_path = test_collection.parent / cid
        collection_path.mkdir()
        collections[cid] = collection_path
        
    output_dir = tmp_path / 'output'
    results = validate_all_collections(test_collection.parent, output_dir)
    
    assert len(results) == len(collections)
    for cid in collections:
        assert cid in results

def test_large_file_handling(test_collection, tmp_path):
    """Test handling of files over 2.5GB."""
    large_file = test_collection / 'eeg' / 'large.set'
    
    # Create file just over 2.5GB
    size = int(2.6 * 1024 * 1024 * 1024)  # 2.6GB
    large_file.write_bytes(b'0' * size)
    
    automation = NDAAutomation()
    output_dir = tmp_path / 'output'
    
    results = automation.process_collection(
        'C4223',
        test_collection,
        output_dir
    )
    
    assert any(split[1] == 'large.set' for split in results['splits'])
    assert len(list((output_dir / 'eeg' / 'large').glob('chunk*'))) > 0
