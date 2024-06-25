import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_DOC_URL
from outputs import control_output
from utils import find_tag, get_response

RESPONSE_IS_NONE = 'response is None'
UNEXPECTED_STATUS = (
    '\nНесовпадающие статусы: \n'
    '{CERTAIN_URL} \n'
    'Статус в карточке: {certain_doc_status} \n'
    'Ожидаемый статус: {status} \n'
)
UNEXPECTED_STATUS_HAS_FOUND = 'Был найден неожиданный статус'
PARSER_STARTED = 'Парсер запущен!'
CMD_ARGUMENTS = 'Аргументы командной строки: {args}'
ERROR_EXPECTED = 'Произошла ошибка в процессе выполнения парсера: {e}'
PARSER_ENDED = 'Парсер успешно завершил свою работу'


def fetch_and_parse(session, url, encoding='utf-8'):
    response = get_response(session, url, encoding)
    if response is None:
        return None
    return BeautifulSoup(response.text, 'lxml')


def whats_new(session):
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
        soup = fetch_and_parse(session, version_link)
        results.append(
            (
                version_link,
                find_tag(soup, 'h1'),
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
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
        if text_match:
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
    DOWNLOADS_DIR = BASE_DIR / 'downloads'  # я не знаю что за прикол,
    # но из файла с константами просто не работает пайтест,
    # хотя по факту все создается
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = session.get(full_href)
    with open(archive_path, 'wb') as file:
        file.write(response.content)


def pep(session):
    soup = fetch_and_parse(session, PEP_DOC_URL)
    numerical_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    find_tr = numerical_index.find_all('tr')
    for tr in tqdm(find_tr[1:]):
        status = find_tag(tr, 'abbr')['title'].split(', ')[1]
        CERTAIN_URL = urljoin(PEP_DOC_URL, find_tag(
            tr, 'a', {'class': 'pep reference internal'})['href']
                              )
        certain_doc_soup = fetch_and_parse(session, CERTAIN_URL)
        certain_doc_status = find_tag(certain_doc_soup, 'abbr').text
        if certain_doc_status != status:
            logging.info(UNEXPECTED_STATUS_HAS_FOUND)
            return print(UNEXPECTED_STATUS.format(
                CERTAIN_URL=CERTAIN_URL,
                certain_doc_status=certain_doc_status,
                status=status
            ))


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
