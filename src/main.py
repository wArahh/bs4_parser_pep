import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging

from constants import BASE_DIR, MAIN_DOC_URL, PEP_DOC_URL
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    all_notes = soup.find_all('li', attrs={'class': 'toctree-l1'})
    tags = []
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    for note in all_notes:
        tags.append(find_tag(note, 'a'))
    for tag in tqdm(tags):
        href = tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul = find_tag(sidebar, 'ul')
    a_tags = ul.find_all('a')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match:
            link = a_tag['href']
            version = text_match.group('version')
            status = text_match.group('status')
            results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    download_documentation_table = find_tag(soup, 'table', {'class': 'docutils'})
    find_a = find_tag(download_documentation_table, 'a')
    full_href = urljoin(downloads_url, find_a['href'])
    filename = full_href.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(full_href)

    with open(archive_path, 'wb') as file:
        file.write(response.content)


def pep(session):
    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    numerical_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    find_tr = numerical_index.find_all('tr')
    for tr in tqdm(find_tr[1:]):
        status = find_tag(tr, 'abbr')['title'].split(', ')[1]
        CERTAIN_URL = urljoin(PEP_DOC_URL, find_tag(tr, 'a', {'class': 'pep reference internal'})['href'])
        certain_pep_response = get_response(session, CERTAIN_URL)
        certain_pep_response.encoding = 'utf-8'
        certain_doc_soup = BeautifulSoup(certain_pep_response.text, 'lxml')
        certain_doc_status = find_tag(certain_doc_soup, 'abbr').text
        if certain_doc_status != status:
            print(status)


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
