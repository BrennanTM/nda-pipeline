
#!/usr/bin/env python3
"""
Cross-platform setup script for NDA Validator package.
Handles macOS, Windows, and Linux environments with NDA requirements.
"""

import os
import sys
import venv
import shutil
import subprocess
import platform
from pathlib import Path
import logging
from typing import Optional, Dict
import json

class NDAPipelineSetup:
    """Sets up the NDA Validator package structure with cross-platform support."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.package_dir = self.base_path / 'nda_validator'
        self.setup_logging()
        
        # Platform-specific configurations
        self.is_windows = platform.system() == 'Windows'
        self.is_macos = platform.system() == 'Darwin'
        
        # Define directory structure for NDA
        self.directories = {
            'validators': self.package_dir / 'validators',
            'utils': self.package_dir / 'utils',
            'cli': self.package_dir / 'cli',
            'tests': self.package_dir / 'tests',
            'config': self.package_dir / 'config',
            'data': self.package_dir / 'data',
            'templates': self.package_dir / 'templates',
            'collections': self.package_dir / 'collections'
        }
        
        # Define NDA collection directories
        self.collection_dirs = {
            'C3996': self.directories['collections'] / 'C3996',
            'C4223': self.directories['collections'] / 'C4223',
            'C4819': self.directories['collections'] / 'C4819',
            'C5096': self.directories['collections'] / 'C5096'
        }
        
    def setup_logging(self):
        """Configure logging with clear formatting."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nda_setup.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('nda_setup')
        
    def create_directory_structure(self):
        """Create the package directory structure with NDA-specific directories."""
        self.logger.info("Creating directory structure...")
        
        # Create main package directory
        self.package_dir.mkdir(parents=True, exist_ok=True)
        (self.package_dir / '__init__.py').touch()
        
        # Create all directories
        for name, path in {**self.directories, **self.collection_dirs}.items():
            path.mkdir(parents=True, exist_ok=True)
            if path.parent == self.package_dir:
                (path / '__init__.py').touch()
            self.logger.info(f"Created {name} directory: {path}")
            
        # Create collection subdirectories
        for collection_path in self.collection_dirs.values():
            for subdir in ['eeg', 'mri', 'behavioral', 'metadata']:
                (collection_path / subdir).mkdir(exist_ok=True)
                
    def setup_virtual_environment(self):
        """Create and configure virtual environment with NDA tools."""
        self.logger.info("Setting up virtual environment...")
        
        venv_dir = self.base_path / 'venv'
        
        try:
            venv.create(venv_dir, with_pip=True)
            
            # Get platform-specific pip path
            if self.is_windows:
                pip_path = venv_dir / 'Scripts' / 'pip.exe'
                python_path = venv_dir / 'Scripts' / 'python.exe'
            else:
                pip_path = venv_dir / 'bin' / 'pip'
                python_path = venv_dir / 'bin' / 'python'
                
            # Install required packages
            packages = [
                'pip', 'wheel', 'setuptools',  # Base packages
                'pandas', 'numpy', 'click', 'pytest', 'pyyaml', 'tqdm',  # Core dependencies
                'nda-tools'  # NDA specific package
            ]
            
            for package in packages:
                subprocess.run([str(pip_path), 'install', '--upgrade', package], check=True)
                
            # Install package in development mode
            subprocess.run([str(pip_path), 'install', '-e', '.'], check=True)
            
            # Configure NDA tools
            self.setup_nda_config(python_path)
            
            self.logger.info("Virtual environment created successfully")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to setup virtual environment: {e}")
            raise
            
    def setup_nda_config(self, python_path: Path):
        """Configure NDA tools with default settings."""
        config = {
            'auth': {
                'username': '',  # Will be filled by user
                'password': ''   # Will be filled by user
            },
            'collections': list(self.collection_dirs.keys()),
            'file_size_limit': 2.5 * 1024 * 1024 * 1024  # 2.5GB
        }
        
        config_dir = Path.home() / '.nda'
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / 'config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    def create_config_files(self):
        """Create configuration files with NDA-specific settings."""
        self.logger.info("Creating configuration files...")
        
        # Update setup.py with NDA requirements
        setup_content = '''
from setuptools import setup, find_packages

setup(
    name="nda_validator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'click',
        'pytest',
        'pyyaml',
        'tqdm',
        'nda-tools',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'nda-validator=nda_validator.cli.main:main',
        ],
    },
    python_requires='>=3.7',
)
'''.strip()

        # Create NDA config template
        nda_config_content = '''
# NDA Configuration
collections:
  C3996:
    data_types: [eeg, behavioral, metadata]
  C4223:
    data_types: [eeg, behavioral, metadata]
  C4819:
    data_types: [eeg, behavioral, metadata]
  C5096:
    data_types: [eeg, behavioral, metadata]

validation:
  required_fields:
    - subjectkey
    - src_subject_id
    - interview_age
    - interview_date
    - sex
'''.strip()

        # Write files with proper line endings
        newline = '\r\n' if self.is_windows else '\n'
        
        with open(self.base_path / 'setup.py', 'w', newline=newline) as f:
            f.write(setup_content)
            
        with open(self.directories['config'] / 'nda_config.yaml', 'w', newline=newline) as f:
            f.write(nda_config_content)
            
        self.create_readme()
        
    def create_readme(self):
        """Create README with setup instructions."""
        readme_content = '''
# NDA Validator Pipeline

## Setup Instructions

1. Install Python 3.7 or higher
2. Run setup script: `python setup.py`
3. Activate virtual environment:
   - Windows: `.\\venv\\Scripts\\activate`
   - MacOS/Linux: `source venv/bin/activate`
4. Configure NDA credentials:
   - Run: `python -m nda_tools config`
   - Enter your NDA username and password

## Usage

See 'complete-lab-guide.md' for detailed instructions.
'''.strip()
        
        with open(self.base_path / 'README.md', 'w') as f:
            f.write(readme_content)
            
    def setup(self):
        """Run complete setup process with error handling."""
        try:
            self.logger.info("Starting NDA Validator setup...")
            
            self.create_directory_structure()
            self.create_config_files()
            self.setup_virtual_environment()
            
            # Print platform-specific activation instructions
            self.logger.info("\n=== Setup Complete ===")
            self.logger.info("\nNext steps:")
            self.logger.info("1. Activate the virtual environment:")
            if self.is_windows:
                self.logger.info("   .\\venv\\Scripts\\activate")
            else:
                self.logger.info("   source venv/bin/activate")
                
            self.logger.info("2. Configure NDA credentials:")
            self.logger.info("   python -m nda_tools config")
            
            self.logger.info("\nTo verify installation:")
            self.logger.info("1. Run tests: pytest")
            self.logger.info("2. Run CLI: nda-validator --help")
            
        except Exception as e:
            self.logger.error(f"Setup failed: {str(e)}")
            raise

if __name__ == '__main__':
    setup = NDAPipelineSetup()
    setup.setup()
