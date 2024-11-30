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