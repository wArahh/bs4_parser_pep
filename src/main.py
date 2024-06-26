import logging
import re
from urllib.parse import urljoin

from collections import defaultdict
import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOADS, MAIN_DOC_URL, PEP_DOC_URL,)
from outputs import control_output
from utils import find_tag, fetch_and_parse

CANT_CONNECT = 'Невозможно подключистя {e}'
RESPONSE_IS_NONE = 'response is None'
UNEXPECTED_STATUS = (
    'Несовпадающие статусы: \n'
    '{CERTAIN_URL} \n'
    'Статус в карточке: {certain_doc_status} \n'
    'Ожидаемый статус: {status}'
    ''
)
UNEXPECTED_STATUS_HAS_FOUND = 'Был найден неожиданный статус'
PARSER_STARTED = 'Парсер запущен!'
CMD_ARGUMENTS = 'Аргументы командной строки: {args}'
ERROR_EXPECTED = 'Произошла ошибка в процессе выполнения парсера: {e}'
PARSER_ENDED = 'Парсер успешно завершил свою работу'


def whats_new(session):
    connection_errors = []
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = fetch_and_parse(session, whats_new_url)
    all_notes = soup.find_all('li', attrs={'class': 'toctree-l1'})
    tags = []
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for note in all_notes:
        tags.append(find_tag(note, 'a'))
    for tag in tqdm(tags):
        href = tag['href']
        version_link = urljoin(whats_new_url, href)
        try:
            soup = fetch_and_parse(session, version_link)
        except ConnectionError as e:
            connection_errors.append(CANT_CONNECT.format(e=e))
        results.append(
            (
                version_link,
                find_tag(soup, 'h1'),
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    if connection_errors:
        logging.error(connection_errors)
    return results


def latest_versions(session):
    soup = fetch_and_parse(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul = find_tag(sidebar, 'ul')
    a_tags = ul.find_all('a')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if not text_match:
            continue
        results.append(
            (
                a_tag['href'],
                text_match.group('version'),
                text_match.group('status')
            )
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = fetch_and_parse(session, downloads_url)
    download_documentation_table = find_tag(
        soup, 'table', {'class': 'docutils'}
    )
    find_a = find_tag(download_documentation_table, 'a')
    full_href = urljoin(downloads_url, find_a['href'])
    filename = full_href.split('/')[-1]
    DOWNLOADS_DIR = BASE_DIR / DOWNLOADS
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = session.get(full_href)
    with open(archive_path, 'wb') as file:
        file.write(response.content)


def pep(session):
    cant_connect = []
    unexpected_status = []
    soup = fetch_and_parse(session, PEP_DOC_URL)
    numerical_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    find_tr = numerical_index.find_all('tr')
    pep_status_count = defaultdict(int)
    for tr in tqdm(find_tr[1:]):
        status = find_tag(tr, 'abbr')['title'].split(', ')[1]
        CERTAIN_URL = urljoin(
            PEP_DOC_URL, find_tag(
                tr, 'a', {'class': 'pep reference internal'})['href']
        )
        try:
            certain_doc_soup = fetch_and_parse(session, CERTAIN_URL)
        except ConnectionError as e:
            cant_connect.append(CANT_CONNECT.format(e=e))
        certain_doc_status = find_tag(certain_doc_soup, 'abbr').text
        pep_status_count[certain_doc_status] += 1
        if certain_doc_status != status:
            unexpected_status.append(
                UNEXPECTED_STATUS.format(
                    CERTAIN_URL=CERTAIN_URL,
                    certain_doc_status=certain_doc_status,
                    status=status
                ))
    if cant_connect:
        logging.error(cant_connect)
    if unexpected_status:
        for status in unexpected_status:
            logging.warning(status)
    return [
        ('Статус', 'Количество'),
        *pep_status_count.items(),
        ('Всего', sum(pep_status_count.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    try:
        configure_logging()
        logging.info(PARSER_STARTED)
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(CMD_ARGUMENTS.format(args=args))
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
        logging.info(PARSER_ENDED)
    except Exception as e:
        logging.exception(ERROR_EXPECTED.format(e=e))


if __name__ == '__main__':
    main()
