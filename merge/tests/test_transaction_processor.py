import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import os
import json

# Import the modules we'll be testing
from financial_planning.transaction_processor import TransactionProcessor
from financial_planning.models import Transaction, Account, Category

@pytest.fixture
def sample_transaction_data():
    return {
        'date': '01/01/2023',
        'amount': '100.00',
        'description': 'PAYMENT RECEIVED',
        'balance': '1000.00'
    }

@pytest.fixture
def sample_accounts():
    return {
        'credit_card': {'name': 'Credit Card', 'type': 'LIABILITY', 'id': '123', 'api_type': 'TRANSACTIONAL'},
        'debit': {'name': 'Debit Account', 'type': 'ASSET', 'id': '456', 'api_type': 'TRANSACTIONAL'},
        'expense': {'name': 'Expenses', 'type': 'EXPENSE', 'id': None, 'api_type': None},
        'income': {'name': 'Income', 'type': 'INCOME', 'id': None, 'api_type': None},
    }

@pytest.fixture
def sample_categories():
    return {
        'income': ['PAYMENT RECEIVED', 'SALARY', 'INCOME'],
        'groceries': ['WOOLWORTHS', 'COLES', 'IGA'],
        'dining': ['MCDONALDS', 'SUBWAY', 'RESTAURANT'],
    }

def test_parse_date():
    processor = TransactionProcessor()
    assert processor.parse_date('01/01/2023') == datetime(2023, 1, 1)
    assert processor.parse_date('invalid') == 'invalid'

def test_parse_amount():
    processor = TransactionProcessor()
    assert processor.parse_amount('100.00') == 100.0
    assert processor.parse_amount('(100.00)') == -100.0
    assert processor.parse_amount('invalid') == 0

def test_clean_description():
    processor = TransactionProcessor()
    assert processor.clean_description('  TEST  ') == 'TEST'
    assert processor.clean_description('TEST') == 'TEST'
    assert processor.clean_description('') == ''

def test_categorize_transaction(sample_categories):
    processor = TransactionProcessor()
    processor.categories = sample_categories
    
    assert processor.categorize_transaction('PAYMENT RECEIVED') == 'income'
    assert processor.categorize_transaction('WOOLWORTHS') == 'groceries'
    assert processor.categorize_transaction('MCDONALDS') == 'dining'
    assert processor.categorize_transaction('UNKNOWN') == 'uncategorized'

def test_is_transfer():
    processor = TransactionProcessor()
    assert processor.is_transfer('TRANSFER TO') == True
    assert processor.is_transfer('TRANSFER FROM') == True
    assert processor.is_transfer('BPAY') == True
    assert processor.is_transfer('PAYMENT') == False

def test_extract_account_reference():
    processor = TransactionProcessor()
    assert processor.extract_account_reference('TRANSFER TO xx1234') == 'xx1234'
    assert processor.extract_account_reference('PAYMENT') == None

def test_find_account_by_reference(sample_accounts):
    processor = TransactionProcessor()
    processor.accounts = sample_accounts
    
    with patch('financial_planning.transaction_processor.TransactionProcessor.find_account_by_reference') as mock_find:
        mock_find.return_value = 'credit_card'
        assert processor.find_account_by_reference('xx1234') == 'credit_card'

def test_create_processed_transaction(sample_transaction_data, sample_accounts):
    processor = TransactionProcessor()
    processor.accounts = sample_accounts
    
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
    
    processed = processor._create_processed_transaction(transaction.to_dict())
    
    assert processed['id'] is not None
    assert processed['date'] == datetime(2023, 1, 1)
    assert processed['description'] == 'PAYMENT RECEIVED'
    assert processed['category'] == 'income'
    assert len(processed['entries']) > 0

def test_update_account_balances(sample_accounts):
    processor = TransactionProcessor()
    processor.accounts = sample_accounts
    
    # Add some processed transactions
    processor.processed_transactions = [
        {
            'id': '1',
            'date': datetime(2023, 1, 1),
            'description': 'Test',
            'category': 'income',
            'entries': [
                {'account': 'debit', 'amount': 100.0, 'type': 'DEBIT'},
                {'account': 'income', 'amount': 100.0, 'type': 'CREDIT'}
            ]
        }
    ]
    
    processor.update_account_balances()
    
    assert processor.account_balances['debit'] == 100.0
    assert processor.account_balances['income'] == 100.0

def test_verify_double_entry_accounting(sample_accounts):
    processor = TransactionProcessor()
    processor.accounts = sample_accounts
    
    # Set up balanced accounts
    processor.account_balances = {
        'debit': 100.0,  # ASSET
        'expense': 50.0,  # EXPENSE
        'credit_card': -100.0,  # LIABILITY
        'income': -50.0,  # INCOME
        'transfer': 0.0  # EQUITY
    }
    
    assert processor.verify_double_entry_accounting() == True
    
    # Set up unbalanced accounts
    processor.account_balances = {
        'debit': 100.0,  # ASSET
        'expense': 50.0,  # EXPENSE
        'credit_card': -100.0,  # LIABILITY
        'income': -40.0,  # INCOME
        'transfer': 0.0  # EQUITY
    }
    
    assert processor.verify_double_entry_accounting() == False

def test_prepare_for_up_bank_api(sample_accounts):
    processor = TransactionProcessor()
    processor.accounts = sample_accounts
    
    # Add a unified transaction
    processor.unified_transactions = [
        {
            'id': '1',
            'date': '2023-01-01',
            'description': 'Test',
            'category': 'income',
            'entries': [
                {'account': 'debit', 'account_name': 'Debit Account', 'amount': 100.0, 'type': 'DEBIT'},
                {'account': 'income', 'account_name': 'Income', 'amount': 100.0, 'type': 'CREDIT'}
            ],
            'balances': {'debit': 100.0, 'income': 100.0}
        }
    ]
    
    up_transactions = processor.prepare_for_up_bank_api()
    
    assert len(up_transactions) == 1
    assert up_transactions[0]['type'] == 'transactions'
    assert up_transactions[0]['id'] == '1'
    assert up_transactions[0]['attributes']['description'] == 'Test'
    assert up_transactions[0]['attributes']['category'] == 'income'
    assert up_transactions[0]['relationships']['account']['data']['id'] == '456' 