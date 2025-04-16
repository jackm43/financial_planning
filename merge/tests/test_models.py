import pytest
from datetime import datetime
from financial_planning.models import Transaction, Account, Category

def test_transaction_creation():
    transaction = Transaction(
        source_file='test.csv',
        date=datetime(2023, 1, 1),
        amount=100.0,
        description='PAYMENT RECEIVED',
        account='debit',
        category='income',
        is_transfer=False,
        account_reference=None
    )
    
    assert transaction.source_file == 'test.csv'
    assert transaction.date == datetime(2023, 1, 1)
    assert transaction.amount == 100.0
    assert transaction.description == 'PAYMENT RECEIVED'
    assert transaction.account == 'debit'
    assert transaction.category == 'income'
    assert transaction.is_transfer == False
    assert transaction.account_reference == None

def test_account_creation():
    account = Account(
        name='Credit Card',
        account_type='LIABILITY',
        account_id='123',
        api_type='TRANSACTIONAL'
    )
    
    assert account.name == 'Credit Card'
    assert account.account_type == 'LIABILITY'
    assert account.account_id == '123'
    assert account.api_type == 'TRANSACTIONAL'

def test_category_creation():
    category = Category(
        name='income',
        keywords=['PAYMENT RECEIVED', 'SALARY', 'INCOME']
    )
    
    assert category.name == 'income'
    assert category.keywords == ['PAYMENT RECEIVED', 'SALARY', 'INCOME']
    
    # Test matching
    assert category.matches('PAYMENT RECEIVED') == True
    assert category.matches('SALARY') == True
    assert category.matches('UNKNOWN') == False 