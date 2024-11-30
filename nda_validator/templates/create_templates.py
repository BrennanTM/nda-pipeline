# nda_validator/templates/create_templates.py
import pandas as pd
from pathlib import Path

def create_eeg_template(output_path: Path):
    """Create EEG metadata template."""
    template = pd.DataFrame(columns=[
        'subjectkey',
        'src_subject_id',
        'interview_age',
        'interview_date',
        'sex',
        'experiment_id',
        'eeg_file'
    ])
    template.to_csv(output_path, index=False)

def create_mri_template(output_path: Path):
    """Create MRI metadata template."""
    template = pd.DataFrame(columns=[
        'subjectkey',
        'src_subject_id',
        'interview_age',
        'interview_date',
        'sex',
        'image_file',
        'image_type',
        'acquisition_date'
    ])
    template.to_csv(output_path, index=False)