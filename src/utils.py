from bs4 import BeautifulSoup
from exceptions import ParserFindTagException

ERROR_LOADING_PAGE = 'Возникла ошибка при загрузке страницы {url}: {e}'
ERROR_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except Exception as e:
        ConnectionError(ERROR_LOADING_PAGE.format(url=url, e=e))


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            ERROR_MESSAGE.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def fetch_and_parse(session, url, encoding='utf-8', features='lxml'):
    return BeautifulSoup(get_response(session, url, encoding).text, features)
