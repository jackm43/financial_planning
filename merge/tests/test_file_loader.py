import pytest
import os
import csv
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

from financial_planning.file_loader import FileLoader

@pytest.fixture
def sample_csv_data():
    return """Date,Amount,Description,Balance
01/01/2023,100.00,PAYMENT RECEIVED,1000.00
02/01/2023,-50.00,WOOLWORTHS,950.00
03/01/2023,-30.00,MCDONALDS,920.00"""

@pytest.fixture
def sample_transaction_processor():
    processor = MagicMock()
    processor.parse_date.return_value = datetime(2023, 1, 1)
    processor.parse_amount.return_value = 100.0
    processor.clean_description.return_value = "PAYMENT RECEIVED"
    processor.categorize_transaction.return_value = "income"
    processor.is_transfer.return_value = False
    processor.extract_account_reference.return_value = None
    return processor

def test_find_latest_commbank_dir():
    with patch('os.listdir') as mock_listdir, \
         patch('os.path.isdir') as mock_isdir, \
         patch('os.path.join') as mock_join:
        
        # Mock directory structure
        mock_listdir.return_value = ['14-03-2025', '13-03-2025', '12-03-2025']
        mock_isdir.return_value = True
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        loader = FileLoader()
        latest_dir = loader.find_latest_commbank_dir('/path/to/commbank_csv')
        
        assert latest_dir == '14-03-2025'
        mock_listdir.assert_called_once_with('/path/to/commbank_csv')
        assert mock_isdir.call_count == 3

def test_load_credit_card(sample_csv_data, sample_transaction_processor):
    with patch('builtins.open', mock_open(read_data=sample_csv_data)), \
         patch('csv.reader') as mock_csv_reader:
        
        # Mock CSV reader
        mock_csv_reader.return_value = [
            ['Date', 'Amount', 'Description', 'Balance'],
            ['01/01/2023', '100.00', 'PAYMENT RECEIVED', '1000.00'],
            ['02/01/2023', '-50.00', 'WOOLWORTHS', '950.00'],
            ['03/01/2023', '-30.00', 'MCDONALDS', '920.00']
        ]
        
        loader = FileLoader()
        loader.transaction_processor = sample_transaction_processor
        
        transactions = loader.load_credit_card('test.csv', 'credit_card')
        
        assert len(transactions) == 3
        assert sample_transaction_processor.parse_date.call_count == 3
        assert sample_transaction_processor.parse_amount.call_count == 3
        assert sample_transaction_processor.clean_description.call_count == 3
        assert sample_transaction_processor.categorize_transaction.call_count == 3
        assert sample_transaction_processor.is_transfer.call_count == 3
        assert sample_transaction_processor.extract_account_reference.call_count == 3

def test_load_bank_account(sample_csv_data, sample_transaction_processor):
    with patch('builtins.open', mock_open(read_data=sample_csv_data)), \
         patch('csv.reader') as mock_csv_reader:
        
        # Mock CSV reader
        mock_csv_reader.return_value = [
            ['Date', 'Amount', 'Description', 'Balance'],
            ['01/01/2023', '100.00', 'PAYMENT RECEIVED', '1000.00'],
            ['02/01/2023', '-50.00', 'WOOLWORTHS', '950.00'],
            ['03/01/2023', '-30.00', 'MCDONALDS', '920.00']
        ]
        
        loader = FileLoader()
        loader.transaction_processor = sample_transaction_processor
        
        transactions = loader.load_bank_account('test.csv', 'debit')
        
        assert len(transactions) == 3
        assert sample_transaction_processor.parse_date.call_count == 3
        assert sample_transaction_processor.parse_amount.call_count == 3
        assert sample_transaction_processor.clean_description.call_count == 3
        assert sample_transaction_processor.categorize_transaction.call_count == 3
        assert sample_transaction_processor.is_transfer.call_count == 3
        assert sample_transaction_processor.extract_account_reference.call_count == 3

def test_load_all_accounts():
    with patch('financial_planning.file_loader.FileLoader.load_credit_card') as mock_load_cc, \
         patch('financial_planning.file_loader.FileLoader.load_bank_account') as mock_load_bank, \
         patch('os.listdir') as mock_listdir, \
         patch('os.path.isdir') as mock_isdir, \
         patch('os.path.join') as mock_join:
        
        # Mock directory structure
        mock_listdir.return_value = ['14-03-2025']
        mock_isdir.return_value = True
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        mock_load_cc.return_value = [{'id': '1'}, {'id': '2'}]
        mock_load_bank.return_value = [{'id': '3'}, {'id': '4'}]
        
        loader = FileLoader()
        loader.transaction_processor = MagicMock()
        
        transactions = loader.load_all_accounts('/path/to/data')
        
        assert len(transactions) == 10  # 2 credit cards * 2 transactions + 3 bank accounts * 2 transactions
        assert mock_load_cc.call_count == 2  # Called for both credit cards
        assert mock_load_bank.call_count == 3  # Called for debit, emergency fund, and saver 