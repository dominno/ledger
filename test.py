from tempfile import NamedTemporaryFile
from unittest import TestCase

from ledger import *


class ManagerTestCase(TestCase):

    def setUp(self):
        self.manager = AccountManager()

    def test_should_be_able_to_create_account(self):
        account = self.manager.create('john')
        assert account.name == 'john'

    def test_should_be_able_to_get_account(self):
        self.manager.create('john')
        assert self.manager.get('john').name == 'john'

    def test_non_exist_account_should_return_none(self):
        assert self.manager.get('john') == None

    def test_should_should_be_able_to_create_unique_accounts_from_source_batch(self):
        self.manager.parse_batch(
            [
            "2015-01-16,john,mary,125.00",
            "2015-01-16,john,mary,125.00",
            "2015-01-17,mary,insurance,100.00"
            ]
        )
        self.manager.parse_batch(
            [
            "2015-01-16,john,mary,125.00",
            "2015-01-16,john,mary,125.00",
            "2015-01-17,mary,insurance,100.00"
            ]
        )
        assert sorted(list(self.manager.accounts.keys())) == ['insurance', 'john', 'mary']


class AccountTestCase(TestCase):

    def setUp(self):
        self.debitor = Account('john')
        self.creditor = Account('marry')

    def test_should_be_able_to_add_entry(self):
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 1), store=True)
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 1), store=True)
        assert self.debitor.entries[0].amount == Decimal('-20.00')
        assert self.creditor.entries[0].amount == Decimal('20.00')

    def test_balance_should_be_aggregated(self):
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 1))
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 1))
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 1))
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 1))
        assert self.debitor.get_balance() == Decimal('-40.00')
        assert self.creditor.get_balance() == Decimal('40.00')

    def test_should_be_able_to_get_balance_for_date(self):
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 1))
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 1))
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 1))
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 1))
        self.debitor.add_entry(-Decimal('20.00'), datetime.date(2015, 12, 2))
        self.creditor.add_entry(Decimal('20.00'), datetime.date(2015, 12, 2))
        self.debitor.add_entry(-Decimal('30.00'), datetime.date(2015, 12, 2))
        self.creditor.add_entry(Decimal('30.00'), datetime.date(2015, 12, 2))
        self.debitor.add_entry(Decimal('10.00'), datetime.date(2015, 12, 2))
        self.creditor.add_entry(-Decimal('10.00'), datetime.date(2015, 12, 2))
        assert self.debitor.get_balance(datetime.date(2015, 12, 2)) == Decimal('-40.00')
        assert self.creditor.get_balance(datetime.date(2015, 12, 2)) == Decimal('40.00')


class TransactionProcessorTestCase(TestCase):

    def setUp(self):
        self.manager = AccountManager()
        self.manager.parse_batch(
            [
            "2015-01-16,john,mary,125.00",
            "2015-01-16,john,mary,125.00",
            "2015-01-17,mary,insurance,100.00"
            ]
        )
        self.processor = TransactionProcessor(self.manager, store_entries=True)

    def test_should_be_able_to_process_batch_of_transactions_entries(self):
        self.processor.parse_batch(
            [
            "2015-01-16,john,mary,125.00",
            "2015-01-16,john,mary,125.00",
            "2015-01-17,mary,insurance,100.00"
            ]
        )
        debitor = self.manager.get('john')
        creditor = self.manager.get('mary')
        assert len(debitor.entries) == 2
        assert len(creditor.entries) == 3

    def test_should_be_able_to_not_store_entries(self):
        self.processor.store_entries = False
        self.processor.parse_batch(
            [
            "2015-01-16,john,mary,125.00",
            "2015-01-16,john,mary,125.00",
            "2015-01-17,mary,insurance,100.00"
            ]
        )
        debitor = self.manager.get('john')
        creditor = self.manager.get('mary')
        assert len(debitor.entries) == 0
        assert len(creditor.entries) == 0
        assert debitor.get_balance() == Decimal('-250.00')
        assert creditor.get_balance() == Decimal('150.00')

    def test_should_be_able_to_parse_transaction(self):
        trx = Trasaction.parse("2015-01-16,john,mary,125.00")
        assert trx.amount == Decimal("125.00")
        assert trx.date == datetime.date(2015, 1, 16)
        assert trx.source_id == "john"
        assert trx.dest_id == "mary"

    def test_should_be_able_to_process_transaction(self):
        self.processor.process(Trasaction.parse("2015-01-16,john,mary,125.00"))
        debitor = self.manager.get('john')
        creditor = self.manager.get('mary')
        assert debitor.get_balance() == Decimal('-125.00')
        assert creditor.get_balance() == Decimal('125.00')
        assert debitor.entries[0].amount == Decimal('-125.00')
        assert creditor.entries[0].amount == Decimal('125.00')
        assert str(debitor.entries[0].date) == "2015-01-16"
        assert str(creditor.entries[0].date) == "2015-01-16"


class TransactionGeneratorTestCase(TestCase):
    def setUp(self):
        self.generator = TransactionGenerator()

    def test_should_be_able_to_generate_test_transactions(self):
        transactions = self.generator.generate(count=10)
        assert len(list(transactions)) == 10

    def test_should_be_able_to_import_generated_transactions(self):
        fp = NamedTemporaryFile(delete=False, mode="w")
        fp.name
        for trx in self.generator.generate(count=100):
           fp.write(trx+'\n') 
        fp.close()
        manager = import_accounts(fp.name)
        processor = import_transactions(fp.name, manager, store_entries=True)
        assert len(manager.accounts) == 8
        assert len([entry for account in manager.accounts.values() for entry in account.entries]) == 200





    
    