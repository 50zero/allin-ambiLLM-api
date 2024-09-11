from .main import create_app
from .config import Config
from .utils import setup_logging, parse_assistant_response

__all__ = ['create_app', 'Config', 'setup_logging', 'parse_assistant_response']

__version__ = '0.1.0'

def get_version():
    return __version__
