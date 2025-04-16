#!/usr/bin/env python3
from financial_planning.transaction_processor import TransactionProcessor
from financial_planning.models import Account, Category

def main():
    # Create sample accounts
    accounts = {
        'debit': Account('Checking Account', 'ASSET', 'debit-123', 'TRANSACTIONAL').to_dict(),
        'credit_card': Account('Credit Card', 'LIABILITY', 'credit-456', 'SAVER').to_dict()
    }
    
    # Create sample categories
    categories = {
        'Groceries': ['SUPERMARKET', 'GROCERY', 'WOOLWORTHS', 'COLES'],
        'Dining': ['RESTAURANT', 'CAFE', 'UBER EATS', 'DELIVEROO'],
    }
    
    # Initialize the transaction processor
    processor = TransactionProcessor(accounts, categories)
    
    # Add a sample transaction
    processor.raw_transactions.append({
        'account': 'debit',
        'date': processor.parse_date('01/05/2023'),
        'amount': processor.parse_amount('-50.25'),
        'description': processor.clean_description('WOOLWORTHS SUPERMARKET'),
        'category': 'Groceries',
        'is_transfer': False,
        'account_reference': None
    })
    
    # Process transactions
    processor.process_raw_transactions()
    processor.update_account_balances()
    
    # Verify double-entry accounting
    is_balanced = processor.verify_double_entry_accounting()
    print(f"Double-entry accounting is balanced: {is_balanced}")
    
    # Print processed transactions
    print("\nProcessed Transactions:")
    for tx in processor.processed_transactions:
        print(f"Date: {tx['date']}, Description: {tx['description']}")
        for entry in tx['entries']:
            print(f"  {entry['type']}: {entry['account']} ${entry['amount']:.2f}")
        print()

if __name__ == "__main__":
    main() 