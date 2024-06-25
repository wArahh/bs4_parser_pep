from pathlib import Path

MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_DOC_URL = 'https://peps.python.org/'

DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
OUTPUT_CHOICES = ('pretty', 'file')

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'
RESULTS_DIR = BASE_DIR / 'results'
DOWNLOADS_DIR = BASE_DIR / 'downloads'

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

FILE_HAS_SAVED = 'Файл с результатами был сохранён: {file_path}'
