import uuid
import datetime
import random

from decimal import Decimal
from collections import OrderedDict


class AccountEntry:
    '''
    a single entry defining the amount and date
    '''

    def __init__(self, amount, date):
        self.amount = amount
        self.date = date

    def __str__(self):
        return "{} {}".format(str(self.date), self.amount)
    
    def __repr__(self):
        return self.__str__()


class Trasaction:
    '''
    a set of 2 AccountEntries, sum of them has to be equal 0.
    '''
    def __init__(self, date, source_id, dest_id, amount):
        self.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        self.source_id = source_id
        self.dest_id = dest_id
        self.amount = Decimal(amount)

    @classmethod
    def parse(cls, line):
        return cls(*line.split(','))


class Account:
    '''
    a single account, a set of AccountEntries
    '''
    def __init__(self, name):
        self.name = name
        self.entries = []
        self.balances = {}

    def aggregate_balance(self, amount, date):
        '''
        For performace reasons balance is aggregated by date, 
        this drops a need to itertate over all entries in order to get balance
        '''
        self.balances.setdefault(date, Decimal('0.00'))
        if amount < 0:
            self.balances[date] -= abs(amount)
        else:
            self.balances[date] += abs(amount)
    
    def add_entry(self, amount, date, store=False):
        entry = AccountEntry(amount, date)
        self.aggregate_balance(entry.amount, entry.date)
        if store:
            self.entries.append(entry)
        return entry
        
    def get_balance(self, date=None):
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if date:
            return self.balances[date]
        return sum(self.balances.values())


class AccountManager:
    '''
    manages accounts - knows about what accounts are defined or creates them
    '''
    
    def __init__(self):
        self.accounts = OrderedDict()

    def create(self, account_name):
        self.accounts[account_name] = Account(account_name)
        return self.accounts[account_name]

    def get(self, account_name):
        try:
            return self.accounts[account_name]
        except KeyError:
            return None

    def parse_batch(self, batch):
        accounts = []
        for line in batch:
            date, source_id, dest_id, amount = line.split(',')
            accounts.append(source_id)
            accounts.append(dest_id)
        for name in set(accounts):
            if not self.get(name):
                self.create(name)

    def import_from_file(self, filename, batch_size=10):
        batch_process(filename, self.parse_batch, batch_size)


class TransactionProcessor:
    '''
    processes transactions, distributing among accounts
    '''
    def __init__(self, account_manager: AccountManager, store_entries=False):
        self.account_manager = account_manager
        self.store_entries = store_entries

    def parse_batch(self, batch):
        for line in batch:
            trx = Trasaction.parse(line)
            self.process(trx)
            
    def process(self, trx: Trasaction):
        debitor = self.account_manager.get(trx.source_id)
        creditor = self.account_manager.get(trx.dest_id)
        debitor_entry = debitor.add_entry(-trx.amount, trx.date, self.store_entries)
        creditor_entry = creditor.add_entry(trx.amount, trx.date, self.store_entries)
        if sum([creditor_entry.amount, debitor_entry.amount]) != Decimal('0.00'):
            raise RuntimeError('Sum of debitor_entry and creditor_entry has to be equal 0')
        
    def import_from_file(self, filename, batch_size=10):
        batch_process(filename, self.parse_batch, batch_size)


class TransactionGenerator:
    '''
    Allows to generate random transactions
    '''
    names = ['mark', 'john', 'marry', 'allice', 'supermarket', 'postoffice', 'issurance', 'bank']

    def generate(self, count=1000):
        today = datetime.date.today()
        for x in range(count):
            date = "{}-{}-{}".format(today.year, today.month, random.choice(range(1, 30)))
            source_id = random.choice(self.names)
            dest_id = random.choice([n for n in self.names if n != source_id])
            yield "{},{},{},{}.00".format(date, source_id, dest_id, random.choice(range(100)))
        
        
def import_accounts(filename, batch_size=100):
    manager = AccountManager()
    manager.import_from_file(filename, batch_size)
    return manager


def import_transactions(filename, manager, batch_size=100, store_entries=False):
    processor = TransactionProcessor(manager, store_entries=store_entries)
    processor.import_from_file(filename, batch_size)
    return processor


def batch_process(filename, process_func, batch_size = 100):
    with open(filename) as infile:
        batch=[]
        for line in infile:
            batch.append(line.strip())
            if len(batch)==batch_size:
                process_func(batch)
                batch = []
    process_func(batch)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group()
    group.add_argument("source", type=str,
                    help="transactions source file")
    group.add_argument("--print_accounts", help="prints all accounts from file provided as param",
                        action="store_true")
    group.add_argument("--account_balance", help="prints balance for selected account",
                        type=str)
    group.add_argument("--date", help="date for which balance will be printed",
                        type=str)
    group.add_argument("--account_entires", help="prints all entries for account",
                        type=str)
    parser.add_argument("--generate", help="generates test raw transaction strings",
                        type=int)

    options = parser.parse_args()
    if options.generate:
        lines = TransactionGenerator().generate(options.generate)
        fh = open(options.source, 'w')
        for line in lines:
            fh.write(line + '\n')
        fh.close()
        exit(0)
    if options.print_accounts:
        manager = import_accounts(options.source)
        for account in manager.accounts:
            print(account)
        exit(0)
    if options.account_balance:
        manager = import_accounts(options.source)
        processor = import_transactions(options.source, manager)
        account = manager.get(options.account_balance)
        if options.date:
            print(account.get_balance(options.date))
        else:
            print(account.get_balance())
        exit(0)
    if options.account_entires:
        manager = import_accounts(options.source)
        processor = import_transactions(options.source, manager, store_entries=True)
        account = manager.get(options.account_entires)
        for entry in account.entries:
            print(entry)
