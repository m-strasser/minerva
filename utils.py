import click
import sys
from pathlib import Path


def log_error(msg):
    """Logs an error and exits."""
    click.secho(msg, err=True, fg='red')
    sys.exit(1)


def read_config_file():
    """Reads the config file at ~/.libraryrc"""
    try:
        f = open('{}/.libraryrc'.format(Path.home()), 'r')
        # We only have one config option, the path to the database
        db_path = f.readline().split("=")[1].strip()
        # Replace '~' with the path to the home directory
        if db_path.startswith('~'):
            db_path = '{}{}'.format(Path.home(), db_path.lstrip('~'))
        f.close()
        return {'db_path': db_path}
    except IOError as e:
        log_error(e)
