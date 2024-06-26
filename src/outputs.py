import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, FILE_OUTPUT,
                       PRETTY_FILEDATA, RESULTS)

FILE_HAS_SAVED = 'Файл с результатами был сохранён: {file_path}'


def default_output(results, cli_args=None):
    for row in results:
        print(*row)


def pretty_output(results, cli_args=None):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / RESULTS
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    file_path = (
            results_dir /
            f'{parser_mode}_'
            f'{dt.datetime.now().strftime(DATETIME_FORMAT)}'
            f'.csv'
    )
    with open(file_path, 'w', encoding='utf-8') as f:
        csv.writer(f).writerows(results)
    logging.info(FILE_HAS_SAVED.format(file_path=file_path))


OUTPUT_FUNCTIONS = {
    None: default_output,
    PRETTY_FILEDATA: pretty_output,
    FILE_OUTPUT: file_output,
}


def control_output(results, cli_args):
    OUTPUT_FUNCTIONS[cli_args.output](results, cli_args)
