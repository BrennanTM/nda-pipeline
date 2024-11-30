# nda_validator/tests/test_validators.py
import pytest
import pandas as pd
from pathlib import Path
from nda_validator.validators import (
    ResearchSubjectValidator,
    DemographicsValidator
)

@pytest.fixture
def sample_subject_data():
    """Create sample research subject data."""
    return pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ', 'NDARAB123456'],
        'src_subject_id': ['2082', '2438'],
        'interview_age': [396, 400],
        'interview_date': ['2023-09-02', '2023-12-04'],
        'sex': ['M', 'F'],
        'phenotype': ['Healthy', 'Healthy'],
        'phenotype_description': ['Healthy Control', 'Healthy Control'],
        'twins_study': [0, 0],
        'sibling_study': [0, 0],
        'family_study': [0, 0]
    })

@pytest.fixture
def sample_demographics_data():
    """Create sample demographics data."""
    return pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ', 'NDARAB123456'],
        'src_subject_id': ['2082', '2438'],
        'interview_age': [396, 400],
        'interview_date': ['2023-09-02', '2023-12-04'],
        'sex': ['M', 'F'],
        'race': ['Black or African American', 'Asian'],
        'ethnicity': ['Non-hispanic', 'Non-hispanic'],
        'education': [5, 5],
        'gender_identity': [1, 2]
    })

def test_research_subject_validator(tmp_path, sample_subject_data):
    """Test research subject validator with valid data."""
    validator = ResearchSubjectValidator('C4223')
    file_path = tmp_path / "subject_data.csv"
    sample_subject_data.to_csv(file_path, index=False)
    
    assert validator.validate_file(file_path)
    assert len(validator.validation_errors) == 0

def test_research_subject_invalid_boolean(tmp_path, sample_subject_data):
    """Test validation of boolean fields."""
    sample_subject_data['twins_study'] = [2, 3]  # Invalid values
    
    validator = ResearchSubjectValidator('C4223')
    file_path = tmp_path / "subject_data.csv"
    sample_subject_data.to_csv(file_path, index=False)
    
    assert not validator.validate_file(file_path)
    assert any("Invalid twins_study values" in err for err in validator.validation_errors)

def test_demographics_validator(tmp_path, sample_demographics_data):
    """Test demographics validator with valid data."""
    validator = DemographicsValidator('C4223')
    file_path = tmp_path / "demographics.csv"
    sample_demographics_data.to_csv(file_path, index=False)
    
    assert validator.validate_file(file_path)
    assert len(validator.validation_errors) == 0

def test_demographics_invalid_race(tmp_path, sample_demographics_data):
    """Test validation of race field."""
    sample_demographics_data['race'] = ['Invalid Race', 'Also Invalid']
    
    validator = DemographicsValidator('C4223')
    file_path = tmp_path / "demographics.csv"
    sample_demographics_data.to_csv(file_path, index=False)
    
    assert not validator.validate_file(file_path)
    assert any("Invalid race values" in err for err in validator.validation_errors)
