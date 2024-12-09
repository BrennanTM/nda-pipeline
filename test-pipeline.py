import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta  # Added timedelta
from tqdm import tqdm
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_large_test_file():
    """Create a test file over 2.5GB for split testing."""
    logging.info("Creating large test file...")
    
    # Create a 3GB test file (slightly over NDA limit)
    file_size = 3 * 1024 * 1024 * 1024  # 3GB in bytes
    chunk_size = 1024 * 1024  # 1MB chunks for creation
    file_path = Path('test_data/C4223/eeg/large_file.set')
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tqdm(total=file_size, unit='B', unit_scale=True, desc="Creating large file") as pbar:
        with open(file_path, 'wb') as f:
            remaining = file_size
            while remaining > 0:
                # Write 1MB chunks of random data
                chunk = os.urandom(min(chunk_size, remaining))
                f.write(chunk)
                remaining -= len(chunk)
                pbar.update(len(chunk))
    
    logging.info(f"Created test file: {file_path} ({file_size / (1024**3):.2f} GB)")
    return file_path

# Create config directory and file first
def setup_config():
    config_dir = Path('nda_validator/config')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        'collections': {
            'C3996': {
                'type': 'behavioral',
                'required_fields': ['subjectkey', 'src_subject_id', 'interview_age', 'interview_date', 'sex'],
                'data_directory': 'test_data/C3996'
            },
            'C4223': {
                'type': 'eeg',
                'required_fields': ['subjectkey', 'src_subject_id', 'interview_age', 'interview_date', 'sex', 'eeg_file'],
                'data_directory': 'test_data/C4223'
            },
            'C4819': {
                'type': 'mri',
                'required_fields': ['subjectkey', 'src_subject_id', 'interview_age', 'interview_date', 'sex', 'mri_file'],
                'data_directory': 'test_data/C4819'
            },
            'C5096': {
                'type': 'behavioral',
                'required_fields': ['subjectkey', 'src_subject_id', 'interview_age', 'interview_date', 'sex'],
                'data_directory': 'test_data/C5096'
            }
        },
        'validation': {
            'file_size_limit': 2.5,
            'allowed_extensions': {
                'eeg': ['.set', '.edf', '.bdf'],
                'mri': ['.nii', '.dcm'],
                'behavioral': ['.csv', '.xlsx'],
                'metadata': ['.csv']
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'file': 'nda_validation.log'
        }
    }
    
    config_path = config_dir / 'nda_config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return config_path

def create_test_structure():
    logging.info("Creating test directory structure...")
    collections = ['C3996', 'C4223', 'C4819', 'C5096']
    base_dir = Path('test_data')
    
    for collection in tqdm(collections, desc="Creating collections"):
        collection_dir = base_dir / collection
        for subdir in ['eeg', 'mri', 'behavioral', 'metadata']:
            (collection_dir / subdir).mkdir(parents=True, exist_ok=True)

def create_sample_data():
    logging.info("Creating sample data files...")
    collections = ['C3996', 'C4223', 'C4819', 'C5096']
    base_dir = Path('test_data')
    
    # Sample data for subjects
    subjects_data = pd.DataFrame({
        'subjectkey': [f'NDAR_INV{i:08d}' for i in range(1, 6)],
        'src_subject_id': [f'SUB{i:03d}' for i in range(1, 6)],
        'interview_age': np.random.randint(240, 360, 5),
        'interview_date': [(datetime.now()).strftime('%m/%d/%Y') for _ in range(5)],
        'sex': np.random.choice(['F', 'M'], 5)
    })
    
    # Demographics data
    demographics_data = subjects_data.copy()
    demographics_data['race'] = np.random.choice([
        'White', 
        'Black or African American',
        'Asian',
        'American Indian or Alaska Native',
        'Native Hawaiian or Other Pacific Islander',
        'Other'
    ], 5)
    demographics_data['ethnicity'] = np.random.choice(['Hispanic', 'Non-hispanic'], 5)
    demographics_data['education'] = np.random.choice([
        'Less than high school',
        'High school graduate',
        'Some college',
        "Bachelor's degree",
        'Graduate degree'
    ], 5)
    demographics_data['employment_status'] = np.random.choice([
        'Employed', 'Unemployed', 'Student', 'Retired'
    ], 5)
    demographics_data['gender_identity'] = np.random.choice([1, 2], 5)
    
    # Create data for each collection
    for collection in tqdm(collections, desc="Creating sample files"):
        collection_dir = base_dir / collection
        
        # Save subject data
        subjects_data.to_csv(collection_dir / 'metadata' / 'research_subject.csv', index=False)
        
        # Save demographics data
        demographics_data.to_csv(collection_dir / 'metadata' / 'demographics.csv', index=False)
        
        # Create EEG data for C4223
        if collection == 'C4223':
            eeg_data = subjects_data.copy()
            eeg_data['experiment_id'] = [f'EXP{i:03d}' for i in range(1, 6)]
            eeg_data['eeg_file'] = [f'sub-{i:03d}_eeg.set' for i in range(1, 6)]
            eeg_data.to_csv(collection_dir / 'eeg' / 'eeg_metadata.csv', index=False)
            # Create dummy EEG files
            for i in range(1, 6):
                (collection_dir / 'eeg' / f'sub-{i:03d}_eeg.set').touch()
        
        # Create MRI data for C4819
        if collection == 'C4819':
            mri_data = subjects_data.copy()
            mri_data['image_file'] = [f'sub-{i:03d}_T1w.nii' for i in range(1, 6)]
            mri_data['image_type'] = np.random.choice(['T1', 'T2', 'fMRI', 'DTI'], 5)
            mri_data['acquisition_date'] = [(datetime.now() - timedelta(days=i)).strftime('%m/%d/%Y') 
                                          for i in range(5)]
            mri_data.to_csv(collection_dir / 'mri' / 'mri_metadata.csv', index=False)
            # Create dummy MRI files
            for i in range(1, 6):
                (collection_dir / 'mri' / f'sub-{i:03d}_T1w.nii').touch()
        
        # Create behavioral data
        behavioral_data = subjects_data.copy()
        behavioral_data['score'] = np.random.randint(0, 100, 5)
        behavioral_data.to_csv(collection_dir / 'behavioral' / 'behavioral_data.csv', index=False)

def test_validators():
    logging.info("Testing validators...")
    from nda_validator.validators import (
        ResearchSubjectValidator,
        DemographicsValidator,
        BehavioralValidator,
        EEGValidator,
        MRIValidator
    )
    
    results = {}
    
    # Define collection-specific data directories
    data_dirs = {
        'mri': Path('test_data/C4819'),  # MRI data is in C4819
        'default': Path('test_data/C4223')  # Other validators use C4223
    }
    
    for name, validator_class in tqdm([
        ('subject', ResearchSubjectValidator),
        ('demographics', DemographicsValidator),
        ('behavioral', BehavioralValidator),
        ('eeg', EEGValidator),
        ('mri', MRIValidator)
    ], desc="Testing validators"):
        try:
            # Use C4819 for MRI, C4223 for others
            collection_id = 'C4819' if name == 'mri' else 'C4223'
            validator = validator_class(collection_id)
            data_dir = data_dirs['mri'] if name == 'mri' else data_dirs['default']
            
            # Handle different validator types
            if name == 'subject':
                result = validator.validate_file(data_dir / 'metadata' / 'research_subject.csv')
            elif name == 'demographics':
                result = validator.validate_file(data_dir / 'metadata' / 'demographics.csv')
            elif name == 'behavioral':
                result = validator.validate_file(data_dir / 'behavioral' / 'behavioral_data.csv')
            elif name == 'eeg':
                result = validator.validate_file(
                    data_dir / 'eeg' / 'eeg_metadata.csv',
                    data_dir / 'eeg'
                )
            elif name == 'mri':
                result = validator.validate_file(
                    data_dir / 'mri' / 'mri_metadata.csv',
                    data_dir / 'mri'
                )
            
            # Format results
            result_items = [
                'valid' if result.is_valid else 'error'
            ]
            if result.errors:
                result_items.append('errors')
                logging.error(f"{name} validation errors: {result.errors}")
            if result.warnings:
                result_items.append('warnings')
            if result.metadata:
                result_items.append('metadata')
            
            results[name] = result_items
            
        except Exception as e:
            logging.error(f"Error testing {name} validator: {str(e)}")
            results[name] = ['error', str(e)]
    
    return results

def test_file_handling():
    logging.info("Testing large file handling...")
    from nda_validator.utils.file_handler import LargeFileHandler
    
    # Create large test file
    file_path = create_large_test_file()
    handler = LargeFileHandler()
    output_dir = Path('test_data/C4223/eeg/chunks')
    
    try:
        if file_path.exists():
            size_gb = file_path.stat().st_size / (1024**3)
            logging.info(f"Test file size: {size_gb:.2f} GB")
            
            if size_gb > 2.5:  # NDA limit
                logging.info("File exceeds NDA limit, splitting...")
                result = handler.split_large_file(file_path, output_dir)
                
                # Verify splits
                if result:
                    total_chunks = len(list(output_dir.glob('*')))
                    logging.info(f"Split into {total_chunks} chunks")
                    return {
                        'success': True,
                        'chunks': total_chunks,
                        'original_size': f"{size_gb:.2f} GB"
                    }
            else:
                logging.warning(f"File under NDA limit, splitting not needed: {file_path}")
                return None
        else:
            return {'error': f"File not found: {file_path}"}
            
    except Exception as e:
        return {'error': str(e)}
    
    return None

def test_automation():
    logging.info("Testing automation...")
    from nda_validator.utils.automation import NDAAutomation
    
    automation = NDAAutomation()
    try:
        result = automation.process_collection('C4223', Path('test_data/C4223'), Path('output'))
    except Exception as e:
        result = {'error': str(e)}
    
    return result

def main():
    # Setup configuration first
    config_path = setup_config()
    
    # Create test structure and data
    create_test_structure()
    create_sample_data()
    
    # Run tests
    validator_results = test_validators()
    file_handling_results = test_file_handling()
    automation_results = test_automation()
    
    # Print results
    print("\n=== NDA Pipeline Test Results ===\n")
    
    print("\nVALIDATORS TESTS:")
    print("-" * 50)
    for name, result in validator_results.items():
        print(f"{name}:")
        for item in result:
            print(f"  - {item}")
    
    print("\nFILE_HANDLING TESTS:")
    print("-" * 50)
    if isinstance(file_handling_results, dict):
        if 'error' in file_handling_results:
            print(f"Error: {file_handling_results['error']}")
        else:
            print(f"Success: Split {file_handling_results['original_size']} file into {file_handling_results['chunks']} chunks")
    elif file_handling_results is None:
        print("No file splitting needed")
    
    print("\nAUTOMATION TESTS:")
    print("-" * 50)
    if isinstance(automation_results, dict) and 'error' in automation_results:
        print(f"Error: {automation_results['error']}")
    else:
        print(f"Result: {automation_results}")
    
    logging.info("Testing completed successfully")

    # Clean up large test file
    large_file = Path('test_data/C4223/eeg/large_file.set')
    if large_file.exists():
        large_file.unlink()
        logging.info("Cleaned up large test file")

if __name__ == "__main__":
    main()
