# test_sample_data.py
from pathlib import Path
from nda_validator.validators import validate_collection_data

def test_sample_data():
    collection_path = Path('test_data')
    collection_id = 'C4223'
    
    # Run validation
    results = validate_collection_data(collection_path, collection_id)
    
    # Print results
    for data_type, is_valid in results.items():
        print(f"{data_type}: {'PASSED' if is_valid else 'FAILED'}")

if __name__ == '__main__':
    test_sample_data()
