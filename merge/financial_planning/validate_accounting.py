#!/usr/bin/env python3
"""
Validate double-entry accounting using real CSV files.
This script loads transactions from the latest CommBank CSV files and verifies
that they follow double-entry accounting principles.
"""

import os
import sys
from transaction_processor import TransactionProcessor
from file_loader import FileLoader

def main():
    """Main function to validate double-entry accounting."""
    # Initialize processor and file loader
    processor = TransactionProcessor()
    file_loader = FileLoader(processor)
    
    # Get the latest CommBank data directory
    commbank_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'commbank_csv')
    
    try:
        # The CSV files are directly in the commbank_csv/14-03-2025 directory
        commbank_dir = os.path.join(commbank_dir, '14-03-2025')
        
        print(f"Using CommBank data from: {commbank_dir}")
        
        # Load transactions from all accounts
        all_transactions = file_loader.load_all_accounts(commbank_dir)
        
        # Verify that all transactions follow double-entry principles
        is_valid = processor.verify_double_entry_accounting(all_transactions)
        
        if is_valid:
            print("\n✅ Double-entry accounting validation PASSED")
        else:
            print("\n❌ Double-entry accounting validation FAILED")
            sys.exit(1)
        
        # Print some statistics about the transactions
        print(f"\nLoaded {len(all_transactions)} transactions")
        
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
            
    except Exception as e:
        print(f"Error validating double-entry accounting: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 