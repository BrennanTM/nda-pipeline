
# nda_validator/tests/test_behavioral.py
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from nda_validator.validators.behavioral import BehavioralValidator, validate_collection_data

@pytest.fixture
def validator():
    return BehavioralValidator('C4223')

@pytest.fixture
def sample_valid_data():
    return pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ', 'NDARAB123456'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],  # Age in months
        'interview_date': ['2024-01-15', '2024-01-16'],
        'sex': ['F', 'M']
    })

def test_valid_data(tmp_path, validator, sample_valid_data):
    # Create test CSV file
    test_file = tmp_path / "valid_data.csv"
    sample_valid_data.to_csv(test_file, index=False)
    
    assert validator.validate_file(test_file)
    assert len(validator.get_validation_errors()) == 0

def test_missing_required_columns(tmp_path, validator):
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456'],
        'interview_age': [240]  # Missing other required columns
    })
    
    test_file = tmp_path / "invalid_data.csv"
    invalid_data.to_csv(test_file, index=False)
    
    assert not validator.validate_file(test_file)
    errors = validator.get_validation_errors()
    assert len(errors) > 0
    assert any('Missing required columns' in err for err in errors)

def test_invalid_subjectkey_format(tmp_path, validator):
    invalid_data = pd.DataFrame({
        'subjectkey': ['INVALID123', 'NDR12345'],  # Invalid format
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['2024-01-15', '2024-01-16'],
        'sex': ['F', 'M']
    })
    
    test_file = tmp_path / "invalid_keys.csv"
    invalid_data.to_csv(test_file, index=False)
    
    assert not validator.validate_file(test_file)
    errors = validator.get_validation_errors()
    assert any('Invalid GUID format' in err for err in errors)

def test_invalid_interview_age(tmp_path, validator):
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [-5, 1500],  # Invalid ages
        'interview_date': ['2024-01-15', '2024-01-16'],
        'sex': ['F', 'M']
    })
    
    test_file = tmp_path / "invalid_ages.csv"
    invalid_data.to_csv(test_file, index=False)
    
    assert not validator.validate_file(test_file)
    errors = validator.get_validation_errors()
    assert any('Invalid interview_age values' in err for err in errors)

def test_invalid_sex_values(tmp_path, validator):
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['2024-01-15', '2024-01-16'],
        'sex': ['X', 'Y']  # Invalid sex values
    })
    
    test_file = tmp_path / "invalid_sex.csv"
    invalid_data.to_csv(test_file, index=False)
    
    assert not validator.validate_file(test_file)
    errors = validator.get_validation_errors()
    assert any('Invalid sex values' in err for err in errors)

def test_pseudo_guid_support(tmp_path, validator):
    """Test support for NDA pseudoGUID format."""
    data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],  # pseudoGUID format
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['2024-01-15'],
        'sex': ['F']
    })
    
    test_file = tmp_path / "pseudo_guid.csv"
    data.to_csv(test_file, index=False)
    
    assert validator.validate_file(test_file)
    assert len(validator.get_validation_errors()) == 0

def test_excel_file_support(tmp_path, validator, sample_valid_data):
    """Test support for Excel file format."""
    test_file = tmp_path / "valid_data.xlsx"
    sample_valid_data.to_excel(test_file, index=False)
    
    assert validator.validate_file(test_file)
    assert len(validator.get_validation_errors()) == 0

def test_future_interview_date(tmp_path, validator):
    """Test rejection of future interview dates."""
    future_data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['2025-12-31'],  # Future date
        'sex': ['F']
    })
    
    test_file = tmp_path / "future_date.csv"
    future_data.to_csv(test_file, index=False)
    
    assert not validator.validate_file(test_file)
    errors = validator.get_validation_errors()
    assert any('Future interview_date' in err for err in errors)

def test_collection_validation(tmp_path):
    # Create mock collection structure
    collection_dir = tmp_path / 'C4223'
    behavioral_dir = collection_dir / 'raw' / 'behavioral'
    behavioral_dir.mkdir(parents=True)
    
    # Create test files
    valid_data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['2024-01-15'],
        'sex': ['F']
    })
    
    valid_file = behavioral_dir / 'valid_data.csv'
    invalid_file = behavioral_dir / 'invalid_data.csv'
    
    valid_data.to_csv(valid_file, index=False)
    valid_data.drop('sex', axis=1).to_csv(invalid_file, index=False)
    
    results = validate_collection_data(collection_dir)
    
    assert len(results) == 2
    assert results['valid_data.csv']['valid']
    assert not results['invalid_data.csv']['valid']

def test_empty_file(tmp_path, validator):
    """Test handling of empty files."""
    empty_file = tmp_path / "empty.csv"
    empty_file.touch()
    
    assert not validator.validate_file(empty_file)
    errors = validator.get_validation_errors()
    assert any('File is empty' in err for err in errors)

def test_nonexistent_file(tmp_path, validator):
    """Test handling of nonexistent files."""
    nonexistent = tmp_path / "nonexistent.csv"
    
    assert not validator.validate_file(nonexistent)
    errors = validator.get_validation_errors()
    assert any('File does not exist' in err for err in errors)

def test_invalid_file_extension(tmp_path, validator):
    """Test handling of invalid file extensions."""
    invalid_file = tmp_path / "data.txt"
    invalid_file.touch()
    
    assert not validator.validate_file(invalid_file)
    errors = validator.get_validation_errors()
    assert any('Invalid file extension' in err for err in errors)
