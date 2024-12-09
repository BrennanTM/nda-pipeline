import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

def create_test_data():
    # Create base directory
    base_dir = Path("test_data")
    base_dir.mkdir(exist_ok=True)
    
    # Sample data for all file types
    subjects = pd.DataFrame({
        'subjectkey': [f'NDAR_INV{i:08d}' for i in range(1, 6)],
        'src_subject_id': [f'SUB{i:03d}' for i in range(1, 6)],
        'interview_age': np.random.randint(240, 360, 5),  # Age in months
        'interview_date': [(datetime.now() - timedelta(days=x)).strftime('%m/%d/%Y') for x in range(5)],
        'sex': np.random.choice(['F', 'M'], 5)
    })
    
    # Create collection directories and save files
    collections = ['C3996', 'C4223', 'C4819', 'C5096']
    for collection in collections:
        collection_dir = base_dir / collection
        for subdir in ['eeg', 'mri', 'behavioral', 'metadata']:
            (collection_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        # Save metadata
        subjects.to_csv(collection_dir / 'metadata' / 'research_subject.csv', index=False)
        
        # Create EEG metadata
        if collection == 'C4223':
            eeg_data = subjects.copy()
            eeg_data['eeg_file'] = [f'sub-{i:03d}_task-rest_eeg.set' for i in range(1, 6)]
            eeg_data.to_csv(collection_dir / 'eeg' / 'eeg_metadata.csv', index=False)
            
            # Create dummy EEG files
            for i in range(1, 6):
                (collection_dir / 'eeg' / f'sub-{i:03d}_task-rest_eeg.set').touch()
        
        # Create MRI metadata
        if collection == 'C4819':
            mri_data = subjects.copy()
            mri_data['mri_file'] = [f'sub-{i:03d}_T1w.nii' for i in range(1, 6)]
            mri_data.to_csv(collection_dir / 'mri' / 'mri_metadata.csv', index=False)
            
            # Create dummy MRI files
            for i in range(1, 6):
                (collection_dir / 'mri' / f'sub-{i:03d}_T1w.nii').touch()
        
        # Create behavioral data
        behavioral_data = subjects.copy()
        behavioral_data['score'] = np.random.randint(0, 100, 5)
        behavioral_data.to_csv(collection_dir / 'behavioral' / 'behavioral_data.csv', index=False)

if __name__ == '__main__':
    create_test_data()
