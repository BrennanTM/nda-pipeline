# nda_validator/validate.py
from pathlib import Path
from .validators import (
    BehavioralValidator,
    EEGValidator,
    MRIValidator,
    ResearchSubjectValidator
)

def validate_collection(data_dir: Path, collection_id: str) -> dict:
    """Validate all data types in a collection."""
    results = {}
    
    # Required subject validation
    subject_file = data_dir / 'research_subject.csv'
    if subject_file.exists():
        subject_validator = ResearchSubjectValidator(collection_id)
        results['subject'] = subject_validator.validate_file(subject_file)
    
    # Behavioral validation
    behavioral_file = data_dir / 'behavioral.csv'
    if behavioral_file.exists():
        behavioral_validator = BehavioralValidator(collection_id)
        results['behavioral'] = behavioral_validator.validate_file(behavioral_file)
    
    # EEG validation
    eeg_file = data_dir / 'eeg.csv'
    if eeg_file.exists():
        eeg_validator = EEGValidator(collection_id)
        results['eeg'] = eeg_validator.validate_file(eeg_file)
    
    # MRI validation
    mri_file = data_dir / 'mri.csv'
    if mri_file.exists():
        mri_validator = MRIValidator(collection_id)
        results['mri'] = mri_validator.validate_file(mri_file)
    
    return results
