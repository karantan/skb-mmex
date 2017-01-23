from bs4 import BeautifulSoup
from cerberus import Validator
from datetime import datetime, date

import click
import csv


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
                # 'transaction_date': {'type': 'date'},
                'transaction_date': {'type': 'string'},
            }
            for transaction in soup.find_all('tr'):
                transaction_info = transaction.find_all('td')
                v.validate({
                    'payee': _parse_payee(transaction_info[0].contents[0].strip()),  # noqa
                    'amount': _parse_amount(transaction_info[1].text.strip()),
                    'notes': transaction_info[3].contents[0].strip(),
                    # 'transaction_date': _parse_transaction_date(
                    #     transaction_info[4].contents[0].strip()
                    # ),
                    'transaction_date': transaction_info[4].contents[0].strip(),
                })
                if v.errors:
                    raise Exception(v.errors)

                csv_writer.writerow([
                    v.document['payee'],
                    v.document['amount'],
                    v.document['notes'],
                    v.document['transaction_date'],
                ])


if __name__ == '__main__':
    parse()
