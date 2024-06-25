import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, FILE_HAS_SAVED


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
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect=csv.get_dialect('excel'))
        writer.writerows(results)
    logging.info(FILE_HAS_SAVED.format(file_path=file_path))


output_functions = {
    'default': default_output,
    'pretty': pretty_output,
    'file': file_output,
}


def control_output(results, cli_args):
    output = cli_args.output
    output_func = output_functions.get(output, default_output)
    output_func(results, cli_args)
