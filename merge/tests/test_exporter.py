import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open

from financial_planning.exporter import Exporter

@pytest.fixture
def sample_transactions():
    return [
        {
            'id': '1',
            'date': '2023-01-01',
            'description': 'Test Transaction',
            'category': 'income',
            'entries': [
                {'account': 'debit', 'account_name': 'Debit Account', 'amount': 100.0, 'type': 'DEBIT'},
                {'account': 'income', 'account_name': 'Income', 'amount': 100.0, 'type': 'CREDIT'}
            ],
            'balances': {'debit': 100.0, 'income': 100.0}
        }
    ]

@pytest.fixture
def sample_accounts():
    return {
        'credit_card': {'name': 'Credit Card', 'type': 'LIABILITY', 'id': '123', 'api_type': 'TRANSACTIONAL'},
        'debit': {'name': 'Debit Account', 'type': 'ASSET', 'id': '456', 'api_type': 'TRANSACTIONAL'},
        'expense': {'name': 'Expenses', 'type': 'EXPENSE', 'id': None, 'api_type': None},
        'income': {'name': 'Income', 'type': 'INCOME', 'id': None, 'api_type': None},
    }

@pytest.fixture
def sample_account_balances():
    return {
        'credit_card': -1000.0,
        'debit': 2000.0,
        'expense': 500.0,
        'income': -1500.0
    }

def test_prepare_transactions_for_up_bank(sample_transactions, sample_accounts):
    exporter = Exporter()
    exporter.accounts = sample_accounts
    
    up_transactions = exporter.prepare_transactions_for_up_bank(sample_transactions)
    
    assert len(up_transactions) == 1
    assert up_transactions[0]['type'] == 'transactions'
    assert up_transactions[0]['id'] == '1'
    assert up_transactions[0]['attributes']['description'] == 'Test Transaction'
    assert up_transactions[0]['attributes']['category'] == 'income'
    assert up_transactions[0]['relationships']['account']['data']['id'] == '456'

def test_prepare_accounts_for_up_bank(sample_accounts, sample_account_balances):
    exporter = Exporter()
    exporter.accounts = sample_accounts
    exporter.account_balances = sample_account_balances
    
    up_accounts = exporter.prepare_accounts_for_up_bank()
    
    assert len(up_accounts) == 2  # Only accounts with IDs
    assert up_accounts[0]['type'] == 'accounts'
    assert up_accounts[0]['id'] == '123'
    assert up_accounts[0]['attributes']['displayName'] == 'Credit Card'
    assert up_accounts[0]['attributes']['accountType'] == 'TRANSACTIONAL'
    assert up_accounts[0]['attributes']['balance']['value'] == '-1000.00'
    assert up_accounts[1]['id'] == '456'
    assert up_accounts[1]['attributes']['displayName'] == 'Debit Account'
    assert up_accounts[1]['attributes']['balance']['value'] == '2000.00'

def test_export_to_json(sample_transactions, sample_accounts, sample_account_balances):
    with patch('builtins.open', mock_open()) as mock_file:
        exporter = Exporter()
        exporter.accounts = sample_accounts
        exporter.account_balances = sample_account_balances
        
        exporter.export_to_json(sample_transactions, 'transactions.json', 'accounts.json')
        
        # Check that json.dump was called twice
        assert mock_file.call_count == 2
        
        # Check the first call (transactions)
        mock_file.assert_any_call('transactions.json', 'w')
        
        # Check the second call (accounts)
        mock_file.assert_any_call('accounts.json', 'w')

def test_export_account_balances(sample_accounts, sample_account_balances):
    with patch('builtins.print') as mock_print:
        exporter = Exporter()
        exporter.accounts = sample_accounts
        exporter.account_balances = sample_account_balances
        
        exporter.export_account_balances()
        
        assert mock_print.call_count == 5  # Header + 4 accounts
        mock_print.assert_any_call("\nAccount Balances:")
        mock_print.assert_any_call("Credit Card: $-1000.00")
        mock_print.assert_any_call("Debit Account: $2000.00")
        mock_print.assert_any_call("Expenses: $500.00")
        mock_print.assert_any_call("Income: $-1500.00")

def test_export_statistics(sample_transactions):
    with patch('builtins.print') as mock_print:
        exporter = Exporter()
        
        exporter.export_statistics(sample_transactions)
        
        assert mock_print.call_count == 4  # Header + total transactions + category breakdown header + category count
        mock_print.assert_any_call("\nStatistics:")
        mock_print.assert_any_call("Total transactions: 1")
        
        # Check category breakdown
        mock_print.assert_any_call("\nCategory Breakdown:")
        mock_print.assert_any_call("income: 1 transactions") 