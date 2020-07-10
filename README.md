# Ledger sandbox project

# Usage:

# Generating test transactions file

    python ledger.py --generate=1000 trx1000.txt

This will generate file with 1000 trasactions in following format:

    2020-7-6,mark,postoffice,77.00
    2020-7-1,marry,bank,58.00
    2020-7-25,issurance,marry,7.00
    2020-7-16,bank,postoffice,93.00
    2020-7-16,john,bank,17.00
    2020-7-3,john,allice,64.00
    2020-7-26,marry,allice,95.00
    2020-7-18,marry,allice,42.00
    2020-7-20,supermarket,mark,1.00

# printing all accounts names

    python ledger.py trx1000.txt --print_accounts

# printing account balance for given account name

    python ledger.py trx1000.txt --account_balance=mark

# printing account balance for given account name at given date

    python ledger.py trx1000.txt --account_balance=mark --date=2020-7-16

# printing all account entries for given account 

    python ledger.py trx1000.txt --account_entires=john


# requirements

    python 3.X is required to run the code, with pytest installed

# how to run tests

    pytest test.py -v
    


