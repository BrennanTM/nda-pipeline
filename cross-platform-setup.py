#!/usr/bin/env python3
"""
Cross-platform setup script for NDA Validator package.
Handles macOS, Windows, and Linux environments.
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

class NDAPipelineSetup:
    """Sets up the NDA Validator package structure with cross-platform support."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.package_dir = self.base_path / 'nda_validator'
        self.setup_logging()
        
        # Platform-specific configurations
        self.is_windows = platform.system() == 'Windows'
        self.is_macos = platform.system() == 'Darwin'
        
        # Define directory structure
        self.directories = {
            'validators': self.package_dir / 'validators',
            'utils': self.package_dir / 'utils',
            'cli': self.package_dir / 'cli',
            'tests': self.package_dir / 'tests',
            'config': self.package_dir / 'config'
        }
        
    def setup_logging(self):
        """Configure logging with clear formatting."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('nda_setup')
        
        # Add console handler for better visibility
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        self.logger.addHandler(console_handler)
        
    def create_directory_structure(self):
        """Create the package directory structure."""
        self.logger.info("Creating directory structure...")
        
        # Create main package directory
        self.package_dir.mkdir(parents=True, exist_ok=True)
        (self.package_dir / '__init__.py').touch()
        
        # Create subdirectories
        for name, path in self.directories.items():
            path.mkdir(parents=True, exist_ok=True)
            (path / '__init__.py').touch()
            self.logger.info(f"Created {name} directory: {path}")

    def find_project_files(self) -> Dict[str, Path]:
        """Find all relevant project files in the current directory and subdirectories."""
        self.logger.info("Searching for existing project files...")
        
        target_files = {
            'behavioral_validator.py': None,
            'test_behavioral.py': None
        }
        
        # Search in current directory and all subdirectories
        for path in Path('.').rglob('*'):
            if path.name in target_files:
                target_files[path.name] = path
                self.logger.info(f"Found {path.name} at: {path}")
                
        # Report any files not found
        missing_files = [name for name, path in target_files.items() if path is None]
        if missing_files:
            self.logger.warning(f"Could not find the following files: {missing_files}")
            
        return {name: path for name, path in target_files.items() if path is not None}

    def move_existing_files(self):
        """Move existing files with automatic file finding."""
        self.logger.info("Moving existing files...")
        
        # Find existing files
        found_files = self.find_project_files()
        
        # Define destinations
        destinations = {
            'behavioral_validator.py': self.directories['validators'] / 'behavioral.py',
            'test_behavioral.py': self.directories['tests'] / 'test_behavioral.py'
        }
        
        # Move found files
        for filename, source_path in found_files.items():
            if source_path and filename in destinations:
                dest_path = destinations[filename]
                shutil.move(str(source_path), str(dest_path))
                self.logger.info(f"Moved {filename} from {source_path} to {dest_path}")
                
    def setup_virtual_environment(self):
        """Create and configure virtual environment with platform-specific handling."""
        self.logger.info("Setting up virtual environment...")
        
        venv_dir = self.base_path / 'venv'
        
        try:
            venv.create(venv_dir, with_pip=True)
            
            # Get platform-specific pip path
            if self.is_windows:
                pip_path = venv_dir / 'Scripts' / 'pip.exe'
            else:
                pip_path = venv_dir / 'bin' / 'pip'
                
            # Ensure pip is up to date
            subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)
            
            # Install package in development mode
            subprocess.run([str(pip_path), 'install', '-e', '.'], check=True)
            
            self.logger.info("Virtual environment created successfully")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to setup virtual environment: {e}")
            raise
            
    def create_config_files(self):
        """Create configuration files with platform-specific line endings."""
        self.logger.info("Creating configuration files...")
        
        # Create setup.py
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
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'nda-validator=nda_validator.cli.main:main',
        ],
    },
    python_requires='>=3.7',
)
'''.strip()

        # Create pytest.ini
        pytest_content = '''
[pytest]
testpaths = nda_validator/tests
python_files = test_*.py
'''.strip()

        # Create .gitignore with platform-specific patterns
        gitignore_content = '''
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
.env

# IDE
.vscode/
.idea/
*.swp

# macOS specific
.DS_Store
.AppleDouble
.LSOverride

# Windows specific
Thumbs.db
ehthumbs.db
Desktop.ini

# Project specific
logs/
temp/
'''.strip()

        # Write files with proper line endings
        newline = '\r\n' if self.is_windows else '\n'
        
        with open(self.base_path / 'setup.py', 'w', newline=newline) as f:
            f.write(setup_content)
            
        with open(self.base_path / 'pytest.ini', 'w', newline=newline) as f:
            f.write(pytest_content)
            
        with open(self.base_path / '.gitignore', 'w', newline=newline) as f:
            f.write(gitignore_content)
            
        self.logger.info("Configuration files created")
        
    def setup(self):
        """Run complete setup process with error handling."""
        try:
            self.logger.info("Starting NDA Validator setup...")
            
            self.create_directory_structure()
            self.move_existing_files()
            self.create_config_files()
            self.setup_virtual_environment()
            
            # Print platform-specific activation instructions
            self.logger.info("\n=== Setup Complete ===")
            self.logger.info("\nTo activate the virtual environment:")
            if self.is_windows:
                self.logger.info("    .\\venv\\Scripts\\activate")
            else:
                self.logger.info("    source venv/bin/activate")
                
            self.logger.info("\nTo verify installation:")
            self.logger.info("1. Activate the virtual environment (see above)")
            self.logger.info("2. Run tests: pytest")
            self.logger.info("3. Run CLI: nda-validator --help")
            
        except Exception as e:
            self.logger.error(f"Setup failed: {str(e)}")
            raise

if __name__ == '__main__':
    setup = NDAPipelineSetup()
    setup.setup()
