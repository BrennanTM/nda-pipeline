# nda_validator/tests/test_validators.py
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from nda_validator.validators import (
    ResearchSubjectValidator,
    DemographicsValidator,
    ValidationResult
)

@pytest.fixture
def sample_subject_data():
    """Create sample research subject data."""
    return pd.DataFrame({
        'subjectkey': ['NDAR_INVMB337LUJ', 'NDARAB123456'],
        'src_subject_id': ['2082', '2438'],
        'interview_age': [396, 400],
        'interview_date': ['01/02/2023', '12/04/2023'],  # NDA format MM/DD/YYYY
        'sex': ['M', 'F'],
        'phenotype': ['Healthy', 'Healthy'],
        'phenotype_description': ['Healthy Control', 'Healthy Control'],
        'twins_study': [0, 0],
        'sibling_study': [0, 0],
        'family_study': [0, 0],
        'family_id': ['', ''],
        'relative_type': ['', '']
    })

@pytest.fixture
def invalid_collection_id():
    """Invalid collection ID for testing."""
    return "invalid_id"

def test_research_subject_validator_success(tmp_path, sample_subject_data):
    """Test successful validation of research subject data."""
    validator = ResearchSubjectValidator('C4223')
    file_path = tmp_path / "subject_data.csv"
    sample_subject_data.to_csv(file_path, index=False)
    
    result = validator.validate_file(file_path)
    assert isinstance(result, ValidationResult)
    assert result.is_valid
    assert len(result.errors) == 0
    assert 'total_subjects' in result.metadata

def test_research_subject_family_study(tmp_path, sample_subject_data):
    """Test family study validation logic."""
    sample_subject_data.loc[0, 'family_study'] = 1
    sample_subject_data.loc[0, 'family_id'] = 'FAM001'
    
    validator = ResearchSubjectValidator('C4223')
    file_path = tmp_path / "subject_data.csv"
    sample_subject_data.to_csv(file_path, index=False)
    
    result = validator.validate_file(file_path)
    assert result.is_valid
    assert any('family_study' in key for key in result.metadata.keys())
