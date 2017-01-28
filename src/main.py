from bs4 import BeautifulSoup
from collections import defaultdict
from cerberus import Validator
from datetime import datetime, date

import click
import csv
import yaml


def _parse_payee(raw_payee: str) -> str:
    return raw_payee


def _parse_amount(raw_amount: str) -> float:
    return raw_amount.replace('.', '').replace(',', '.')


def _parse_transaction_date(raw_transaction_date: str) -> date:
    return datetime.strptime(
        raw_transaction_date,
        '%d.%m.%Y',
    )


@click.command()
@click.option(
    '--source',
    default='example.html',
    prompt='Input file',
    help='Input source file.',
)
@click.option(
    '--output',
    default='output.csv',
    prompt='Output file',
    help='Output .csv file.',
)
def parse(source, output):
    """Parse skb tbody table to .csv which can be used to inport to MMEX."""
    with open('category_mapping.yaml', 'r') as stream:
        category_mapping = yaml.load(stream)
    with open(source, 'r') as fp:
        with open(output, 'w', newline='') as csvfile:
            csv_writer = csv.writer(
                csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)  # noqa
            # csv_writer.writerow(['payee', 'amount', 'notes', 'date'])

            soup = BeautifulSoup(fp.read(), 'html.parser')
            v = Validator()
            v.schema = {
                'payee': {'type': 'string'},
                'amount': {'type': 'number', 'coerce': float},
                'notes': {'type': 'string'},
                # NOTE: you can choose date format in MMEX.
                # 'transaction_date': {'type': 'date'},
                'transaction_date': {'type': 'string'},
            }
            for transaction in soup.find_all('tr'):
                transaction_info = transaction.find_all('td')
                v.validate({
                    'payee': _parse_payee(transaction_info[0].contents[0].strip()),  # noqa
                    'amount': _parse_amount(transaction_info[1].text.strip()),
                    'notes': transaction_info[3].contents[0].strip(),
                    'transaction_date': transaction_info[4].contents[0].strip(),
                })
                if v.errors:
                    raise Exception(v.errors)

                csv_writer.writerow([
                    v.document['payee'],
                    v.document['amount'],
                    v.document['notes'],
                    v.document['transaction_date'],
                    category_mapping.get(v.document['payee'], '')
                ])


@click.command()
@click.option(
    '--source',
    default='example.html',
    prompt='Input file',
    help='Input source file.',
)
def analyse(source):
    """Parse skb tbody table to .csv which can be used to inport to MMEX."""
    data = defaultdict(int)

    with open(source, 'r') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
        v = Validator()
        v.schema = {
            'payee': {'type': 'string'},
        }
        for transaction in soup.find_all('tr'):
            transaction_info = transaction.find_all('td')
            v.validate({
                'payee': _parse_payee(transaction_info[0].contents[0].strip()),  # noqa
            })
            if v.errors:
                raise Exception(v.errors)
            data[v.document['payee']] += 1
    with open('category_mapping.yaml', 'r') as stream:
        existing_data = yaml.load(stream)
    with open('category_mapping.yaml', 'w') as stream:
        for payee, times in data.items():
            if times >= 2:
                # category = click.prompt(
                #     '[*] Enter category for {}: '.format(payee),
                #     type=str,
                #     default=existing_data.get(payee),
                # )
                stream.write(
                    yaml.dump(
                        {payee: existing_data.get(payee, '<ENTER CATEGORY>')},
                        default_flow_style=False),
                    )


@click.command()
@click.option(
    '--mode',
    default='parse',
    prompt='mode',
    help='Program mode. It can be parse (default) or analyse.',
    type=click.Choice(['parse', 'analyse']),
)
def run(mode):
    if mode == 'parse':
        parse()
    elif mode == 'analyse':
        analyse()


if __name__ == '__main__':
    run()
