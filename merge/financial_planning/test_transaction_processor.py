import pytest
import os
from financial_planning.transaction_processor import TransactionProcessor
from financial_planning.file_loader import FileLoader

@pytest.fixture
def processor():
    return TransactionProcessor()

@pytest.fixture
def file_loader(processor):
    return FileLoader(processor)

def test_verify_double_entry_accounting(processor):
    """Test double-entry accounting verification"""
    # Create test transactions that follow double-entry principles
    transactions = [
        {
            'date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test transaction 1',
            'account_id': 'ASSET_1'
        },
        {
            'date': '2024-01-01',
            'amount': -100.00,
            'description': 'Test transaction 1',
            'account_id': 'LIABILITY_1'
        }
    ]
    
    # Verify that balanced transactions pass
    assert processor.verify_double_entry_accounting(transactions) is True
    
    # Create unbalanced transactions
    unbalanced_transactions = [
        {
            'date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test transaction 2',
            'account_id': 'ASSET_1'
        },
        {
            'date': '2024-01-01',
            'amount': -50.00,  # Different amount
            'description': 'Test transaction 2',
            'account_id': 'LIABILITY_1'
        }
    ]
    
    # Verify that unbalanced transactions fail
    assert processor.verify_double_entry_accounting(unbalanced_transactions) is False

def test_verify_real_transactions(processor, file_loader):
    """Test double-entry accounting verification with real CSV data"""
    # Get the latest CommBank data directory
    commbank_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'commbank_csv')
    latest_dir = file_loader.find_latest_commbank_dir(commbank_dir)
    commbank_dir = os.path.join(commbank_dir, latest_dir)
    
    # Load transactions from all accounts
    all_transactions = file_loader.load_all_accounts(commbank_dir)
    
    # Verify that all transactions follow double-entry principles
    assert processor.verify_double_entry_accounting(all_transactions) is True, \
        "Real transactions from CSV files should follow double-entry accounting principles"
    
    # Print some statistics about the transactions
    print(f"\nLoaded {len(all_transactions)} transactions from {latest_dir}")
    
    # Group transactions by account
    account_transactions = {}
    for transaction in all_transactions:
        account_id = transaction['account_id']
        if account_id not in account_transactions:
            account_transactions[account_id] = []
        account_transactions[account_id].append(transaction)
    
    # Print transaction counts by account
    print("\nTransactions by account:")
    for account_id, transactions in account_transactions.items():
        print(f"{account_id}: {len(transactions)} transactions") 