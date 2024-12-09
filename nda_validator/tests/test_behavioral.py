# nda_validator/tests/test_behavioral.py
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from nda_validator.validators.behavioral import BehavioralValidator, ValidationResult

@pytest.fixture
def validator():
    return BehavioralValidator('C4223')

@pytest.fixture
def sample_valid_data():
    """Create sample behavioral data in NDA format."""
    return pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ', 'NDARAB123456'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],  # Age in months
        'interview_date': ['01/15/2024', '01/16/2024'],  # MM/DD/YYYY format
        'sex': ['F', 'M'],
        'score_anxiety': [45, 52],
        'score_depression': [38, 41]
    })

def test_valid_data(tmp_path, validator, sample_valid_data):
    """Test validation with valid data."""
    test_file = tmp_path / "valid_data.csv"
    sample_valid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert isinstance(result, ValidationResult)
    assert result.is_valid
    assert len(result.errors) == 0
    assert 'total_records' in result.metadata
    assert 'score_statistics' in result.metadata

def test_missing_required_columns(tmp_path, validator):
    """Test handling of missing required columns."""
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456'],
        'interview_age': [240]  # Missing other required columns
    })
    
    test_file = tmp_path / "invalid_data.csv"
    invalid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('Missing required columns' in err for err in result.errors)

def test_invalid_subjectkey_format(tmp_path, validator):
    """Test GUID format validation."""
    invalid_data = pd.DataFrame({
        'subjectkey': ['INVALID123', 'NDR12345'],  # Invalid format
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['01/15/2024', '01/16/2024'],
        'sex': ['F', 'M']
    })
    
    test_file = tmp_path / "invalid_keys.csv"
    invalid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('Invalid GUID format' in err for err in result.errors)

def test_invalid_interview_age(tmp_path, validator):
    """Test age validation."""
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [-5, 1500],  # Invalid ages
        'interview_date': ['01/15/2024', '01/16/2024'],
        'sex': ['F', 'M']
    })
    
    test_file = tmp_path / "invalid_ages.csv"
    invalid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('Invalid interview_age values' in err for err in result.errors)

def test_invalid_sex_values(tmp_path, validator):
    """Test sex field validation."""
    invalid_data = pd.DataFrame({
        'subjectkey': ['NDARAB123456', 'NDARCD789012'],
        'src_subject_id': ['SUB001', 'SUB002'],
        'interview_age': [240, 360],
        'interview_date': ['01/15/2024', '01/16/2024'],
        'sex': ['X', 'Y']  # Invalid sex values
    })
    
    test_file = tmp_path / "invalid_sex.csv"
    invalid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('Invalid sex values' in err for err in result.errors)

def test_pseudo_guid_support(tmp_path, validator):
    """Test support for NDA pseudoGUID format."""
    data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],  # pseudoGUID format
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['01/15/2024'],
        'sex': ['F']
    })
    
    test_file = tmp_path / "pseudo_guid.csv"
    data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert result.is_valid
    assert len(result.errors) == 0

def test_excel_file_support(tmp_path, validator, sample_valid_data):
    """Test Excel file format support."""
    test_file = tmp_path / "valid_data.xlsx"
    sample_valid_data.to_excel(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert result.is_valid
    assert len(result.errors) == 0

def test_future_interview_date(tmp_path, validator):
    """Test future date validation."""
    future_date = (datetime.now() + timedelta(days=365)).strftime('%m/%d/%Y')
    future_data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': [future_date],
        'sex': ['F']
    })
    
    test_file = tmp_path / "future_date.csv"
    future_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('Future interview_date' in err for err in result.errors)

def test_invalid_date_format(tmp_path, validator, sample_valid_data):
    """Test date format validation (MM/DD/YYYY required)."""
    sample_valid_data['interview_date'] = ['2024-01-15', '2024-01-16']  # Wrong format
    test_file = tmp_path / "invalid_date_format.csv"
    sample_valid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert 'date format' in ' '.join(result.warnings).lower()

def test_score_validation(tmp_path, validator):
    """Test behavioral score validation."""
    data = pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ'],
        'src_subject_id': ['SUB001'],
        'interview_age': [240],
        'interview_date': ['01/15/2024'],
        'sex': ['F'],
        'score_anxiety': [150]  # Invalid score > 100
    })
    
    test_file = tmp_path / "invalid_scores.csv"
    data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert not result.is_valid
    assert any('score' in err.lower() for err in result.errors)

def test_missing_data_reporting(tmp_path, validator, sample_valid_data):
    """Test missing data detection and reporting."""
    sample_valid_data.loc[0, 'score_anxiety'] = np.nan
    test_file = tmp_path / "missing_data.csv"
    sample_valid_data.to_csv(test_file, index=False)
    
    result = validator.validate_file(test_file)
    assert result.is_valid  # Missing scores shouldn't invalidate
    assert 'missing_data_summary' in result.metadata
    assert result.metadata['missing_data_summary']['score_anxiety']['missing_count'] > 0

def test_empty_file(tmp_path, validator):
    """Test empty file handling."""
    empty_file = tmp_path / "empty.csv"
    empty_file.touch()
    
    result = validator.validate_file(empty_file)
    assert not result.is_valid
    assert any('empty' in err.lower() for err in result.errors)

def test_nonexistent_file(tmp_path, validator):
    """Test nonexistent file handling."""
    nonexistent = tmp_path / "nonexistent.csv"
    
    result = validator.validate_file(nonexistent)
    assert not result.is_valid
    assert any('not found' in err.lower() for err in result.errors)

def test_invalid_file_extension(tmp_path, validator):
    """Test invalid file extension handling."""
    invalid_file = tmp_path / "data.txt"
    invalid_file.touch()
    
    result = validator.validate_file(invalid_file)
    assert not result.is_valid
    assert any('extension' in err.lower() for err in result.errors)
