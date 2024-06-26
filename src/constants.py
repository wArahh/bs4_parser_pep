from pathlib import Path

from bs4 import BeautifulSoup

from utils import get_response

MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_DOC_URL = 'https://peps.python.org/'

BASE_DIR = Path(__file__).parent
RESULTS_FILENAME = 'results'
DOWNLOAD_FILENAME = 'downloads'
PRETTY_FILEDATA = 'pretty'
DEFAULT_OUTPUT = 'default'
FILE_OUTPUT = 'file'
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'

DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
OUTPUT_CHOICES = (PRETTY_FILEDATA, FILE_OUTPUT)

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}


def fetch_and_parse(session, url, encoding='utf-8', features='lxml'):
    return BeautifulSoup(get_response(session, url, encoding).text, features)
