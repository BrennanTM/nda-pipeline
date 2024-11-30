# nda_validator/cli/main.py
import click
from pathlib import Path
from ..validators import BehavioralValidator, EEGValidator, MRIValidator

@click.group()
def cli():
    """NDA Data Validation Tool"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--data-dir', type=click.Path(exists=True), help='Directory containing data files')
def validate_eeg(file_path, data_dir):
    """Validate EEG metadata and data files."""
    validator = EEGValidator('C4223')
    result = validator.validate_file(Path(file_path), Path(data_dir) if data_dir else None)
    if result:
        click.echo("Validation passed!")
    else:
        click.echo("Validation failed:")
        for error in validator.validation_errors:
            click.echo(f"- {error}")