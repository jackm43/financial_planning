import pytest
import os
from datetime import datetime

@pytest.fixture
def sample_accounts():
    return {
        'credit_card': {'name': 'Credit Card', 'type': 'LIABILITY', 'id': '123', 'api_type': 'TRANSACTIONAL'},
        'debit': {'name': 'Debit Account', 'type': 'ASSET', 'id': '456', 'api_type': 'TRANSACTIONAL'},
        'emergency_fund': {'name': 'Emergency Fund', 'type': 'ASSET', 'id': '789', 'api_type': 'SAVER'},
        'old_credit_card': {'name': 'Old Credit Card', 'type': 'LIABILITY', 'id': '101', 'api_type': 'TRANSACTIONAL'},
        'saver': {'name': 'Savings Account', 'type': 'ASSET', 'id': '102', 'api_type': 'SAVER'},
        'expense': {'name': 'Expenses', 'type': 'EXPENSE', 'id': None, 'api_type': None},
        'income': {'name': 'Income', 'type': 'INCOME', 'id': None, 'api_type': None},
        'transfer': {'name': 'Internal Transfers', 'type': 'EQUITY', 'id': None, 'api_type': None},
    }

@pytest.fixture
def sample_categories():
    return {
        'groceries': [
            'WOOLWORTHS', 'COLES', 'IGA', 'ALDI', 'SPUDSHED', 'WA GROWERS', 'COSTCO'
        ],
        'dining': [
            'MCDONALDS', 'SUBWAY', 'HUNGRY JACKS', 'NANDOS', 'GUZMAN Y GOMEZ', 'KFC', 
            'ZAMBRERO', 'BOOST JUICE', 'MUFFIN BREAK', 'CHICKEN TREAT', 'CAFE', 
            'RESTAURANT', 'FOOD', 'MUZZ BUZZ', 'BASKIN', 'BAKERY', 'PIZZ'
        ],
        'shopping': [
            'KMART', 'TARGET', 'MYER', 'DAVID JONES', 'BIG W', 'BUNNINGS', 'OFFICEWORKS',
            'JB HI-FI', 'HARVEY NORMAN', 'IKEA', 'RED DOT', 'PETBARN', 'PET CIRCLE'
        ],
        'transport': [
            'FUEL', 'PETROL', 'BP ', 'CALTEX', 'SHELL', 'UBER', 'TRANSPORT', 'TAXI',
            'PARKING', 'CAR', 'AUTO', 'DEPARTMENT OF TRANSPOR'
        ],
        'utilities': [
            'ORIGIN ENERGY', 'SYNERGY', 'WATER CORPORATION', 'INTERNET', 'PHONE',
            'OPTUS', 'TELSTRA', 'VODAFONE', 'NBN', 'Aussie Broadband', 'Superloop'
        ],
        'health': [
            'CHEMIST', 'PHARMACY', 'DOCTOR', 'MEDICAL', 'DENTAL', 'HEALTH', 'HOSPITAL'
        ],
        'entertainment': [
            'CINEMA', 'MOVIE', 'THEATRE', 'NETFLIX', 'SPOTIFY', 'APPLE.COM', 'GOOGLE PLAY',
            'AMAZON', 'STEAM', 'PATREON', 'DISCORD', 'APPLE MUSIC', 'DISNEY+'
        ],
        'fitness': [
            'GYM', 'FITNESS', 'SPORT', 'SWIM', 'GOLDSGYM'
        ],
        'income': [
            'PAYMENT RECEIVED', 'SALARY', 'INCOME', 'DIVIDEND', 'INTEREST', 'REFUND',
            'TAX RETURN', 'CASH DEPOSIT', 'DIRECT CREDIT'
        ],
        'transfers': [
            'TRANSFER', 'BPAY', 'PAY ANYONE', 'NETBANK'
        ]
    }

@pytest.fixture
def sample_transaction():
    return {
        'source_file': 'test.csv',
        'date': datetime(2023, 1, 1),
        'amount': 100.0,
        'description': 'PAYMENT RECEIVED',
        'account': 'debit',
        'category': 'income',
        'is_transfer': False,
        'account_reference': None
    }

@pytest.fixture
def sample_processed_transaction():
    return {
        'id': '1',
        'date': datetime(2023, 1, 1),
        'description': 'PAYMENT RECEIVED',
        'category': 'income',
        'entries': [
            {'account': 'debit', 'amount': 100.0, 'type': 'DEBIT'},
            {'account': 'income', 'amount': 100.0, 'type': 'CREDIT'}
        ]
    }

@pytest.fixture
def sample_unified_transaction():
    return {
        'id': '1',
        'date': '2023-01-01',
        'description': 'PAYMENT RECEIVED',
        'category': 'income',
        'entries': [
            {'account': 'debit', 'account_name': 'Debit Account', 'amount': 100.0, 'type': 'DEBIT'},
            {'account': 'income', 'account_name': 'Income', 'amount': 100.0, 'type': 'CREDIT'}
        ],
        'balances': {'debit': 100.0, 'income': 100.0}
    }

@pytest.fixture
def sample_account_balances():
    return {
        'credit_card': -1000.0,
        'debit': 2000.0,
        'emergency_fund': 5000.0,
        'old_credit_card': -500.0,
        'saver': 10000.0,
        'expense': 500.0,
        'income': -1500.0,
        'transfer': -200.0
    }

@pytest.fixture
def temp_csv_file(tmp_path):
    csv_content = """Date,Amount,Description,Balance
01/01/2023,100.00,PAYMENT RECEIVED,1000.00
02/01/2023,-50.00,WOOLWORTHS,950.00
03/01/2023,-30.00,MCDONALDS,920.00"""
    
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    return csv_file 