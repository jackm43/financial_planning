import os
import csv
import re
from datetime import datetime

class FileLoader:
    """Loads transaction data from CSV files."""
    
    def __init__(self, transaction_processor=None):
        """
        Initialize the file loader.
        
        Args:
            transaction_processor (TransactionProcessor, optional): Transaction processor. Defaults to None.
        """
        self.transaction_processor = transaction_processor
    
    def find_latest_commbank_dir(self, commbank_dir):
        """
        Find the latest CommBank data directory.
        
        Args:
            commbank_dir (str): Path to CommBank data directory
            
        Returns:
            str: Latest directory name
        """
        commbank_dirs = [d for d in os.listdir(commbank_dir) 
                        if os.path.isdir(os.path.join(commbank_dir, d)) 
                        and re.match(r'\d{2}-\d{2}-\d{4}', d)]
        
        if not commbank_dirs:
            raise ValueError(f"No date folders found in {commbank_dir}. Please ensure the directory contains folders with format DD-MM-YYYY.")
        
        today = datetime.now()
        commbank_dirs = sorted(commbank_dirs, 
                             key=lambda x: abs((datetime.strptime(x, '%d-%m-%Y') - today).days))
        
        latest_dir = max(commbank_dirs, key=lambda x: datetime.strptime(x, '%d-%m-%Y'))
        
        print(f"Using CommBank data from: {os.path.join(commbank_dir, latest_dir)}")
        
        return latest_dir
    
    def load_credit_card(self, file_path, account_id):
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                transactions = []
                for row in reader:
                    date = self.transaction_processor.parse_date(row[0])
                    amount = self.transaction_processor.parse_amount(row[1])
                    description = row[2]
                    if amount != 0:
                        transactions.append({
                            'date': date,
                            'amount': amount,
                            'description': description,
                            'account_id': account_id
                        })
                return transactions
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return []
    
    def load_bank_account(self, file_path, account_id):
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                transactions = []
                for row in reader:
                    date = self.transaction_processor.parse_date(row[0])
                    amount = self.transaction_processor.parse_amount(row[1])
                    description = row[2]
                    if amount != 0:
                        transactions.append({
                            'date': date,
                            'amount': amount,
                            'description': description,
                            'account_id': account_id
                        })
                return transactions
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return []
    
    def load_all_accounts(self, commbank_dir):
        """
        Load all account transactions from CommBank data directory.
        
        Args:
            commbank_dir (str): Path to CommBank data directory
            
        Returns:
            list: List of all transactions
        """
        all_transactions = []
        
        # Load credit card transactions
        credit_card_transactions = self.load_credit_card(
            os.path.join(commbank_dir, 'CBA_CC.csv'), 'credit_card'
        )
        all_transactions.extend(credit_card_transactions)
        
        # Load debit account transactions
        debit_transactions = self.load_bank_account(
            os.path.join(commbank_dir, 'CBA_DEBIT.csv'), 'debit'
        )
        all_transactions.extend(debit_transactions)
        
        # Load emergency fund transactions
        emergency_fund_transactions = self.load_bank_account(
            os.path.join(commbank_dir, 'CBA_EMERGENCY_FUND.csv'), 'emergency_fund'
        )
        all_transactions.extend(emergency_fund_transactions)
        
        # Load old credit card transactions
        old_credit_card_transactions = self.load_credit_card(
            os.path.join(commbank_dir, 'CBA_OLD_CC.csv'), 'old_credit_card'
        )
        all_transactions.extend(old_credit_card_transactions)
        
        # Load saver account transactions
        saver_transactions = self.load_bank_account(
            os.path.join(commbank_dir, 'CBA_SAVER.csv'), 'saver'
        )
        all_transactions.extend(saver_transactions)
        
        return all_transactions 