import uuid
from datetime import datetime, timedelta
import re

from models import Transaction, Account, Category

class TransactionProcessor:
    """Processes transactions for double-entry accounting."""
    
    def __init__(self, accounts=None, categories=None):
        """
        Initialize the transaction processor.
        
        Args:
            accounts (dict, optional): Dictionary of accounts. Defaults to None.
            categories (dict, optional): Dictionary of categories. Defaults to None.
        """
        self.accounts = accounts or {}
        self.categories = categories or {}
        self.raw_transactions = []
        self.processed_transactions = []
        self.unified_transactions = []
        self.account_balances = {account: 0 for account in self.accounts}
        self.pending_transfers = []
    
    def parse_date(self, date_str):
        """
        Parse date string to datetime object.
        
        Args:
            date_str (str): Date string in DD/MM/YYYY format
            
        Returns:
            datetime or str: Parsed datetime object or original string if parsing fails
        """
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            # If date parsing fails, return the original string
            return date_str
    
    def parse_amount(self, amount_str):
        """
        Parse amount string to float.
        
        Args:
            amount_str (str): Amount string
            
        Returns:
            float: Parsed amount
        """
        if isinstance(amount_str, str):
            # Remove commas and handle negative values with parentheses
            amount_str = amount_str.replace(',', '')
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            # Remove quotes if present
            amount_str = amount_str.strip('"')
            
            try:
                return float(amount_str)
            except ValueError:
                return 0
        return amount_str
    
    def clean_description(self, description):
        """
        Clean and standardize description.
        
        Args:
            description (str): Description to clean
            
        Returns:
            str: Cleaned description
        """
        if isinstance(description, str):
            # Remove quotes
            description = description.strip('"')
            # Remove excess whitespace
            description = ' '.join(description.split())
            return description
        return ""
    
    def categorize_transaction(self, description):
        """
        Categorize a transaction based on its description.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str: Category name
        """
        description_upper = description.upper()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.upper() in description_upper:
                    return category
        
        return 'uncategorized'
    
    def is_transfer(self, description):
        """
        Check if a transaction is likely a transfer between accounts.
        
        Args:
            description (str): Transaction description
            
        Returns:
            bool: True if likely a transfer, False otherwise
        """
        description_upper = description.upper()
        
        transfer_keywords = [
            'TRANSFER TO', 'TRANSFER FROM', 'BPAY', 'NETBANK', 'COMMBANK APP'
        ]
        
        for keyword in transfer_keywords:
            if keyword.upper() in description_upper:
                return True
        
        return False
    
    def extract_account_reference(self, description):
        """
        Extract account reference from description.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str or None: Account reference or None if not found
        """
        # Extract account numbers like xx1234
        account_match = re.search(r'xx(\d+)', description)
        if account_match:
            return account_match.group(0)
        return None
    
    def find_account_by_reference(self, account_reference):
        """
        Find the account matching a reference in a transaction description.
        
        Args:
            account_reference (str): Account reference
            
        Returns:
            str or None: Account name or None if not found
        """
        # This would typically require a mapping of account references to account names
        # For now, we'll use a simple heuristic based on the last digits
        if account_reference:
            if account_reference == 'xx5784':
                return 'credit_card'
            elif account_reference == 'xx9070':
                return 'debit'
            elif account_reference == 'xx1893':
                return 'emergency_fund'
            elif account_reference == 'xx1212':
                return 'old_credit_card'
            elif account_reference == 'xx2467':
                return 'saver'
        
        return None
    
    def find_matching_transfer(self, transaction, amount):
        """
        Find a matching transfer transaction from another account.
        
        Args:
            transaction (dict): Transaction to find a match for
            amount (float): Transaction amount
            
        Returns:
            dict or None: Matching transaction or None if not found
        """
        # Transfers are usually within 1-2 days of each other
        if not isinstance(transaction['date'], datetime):
            return None
            
        date_range_start = transaction['date'] - timedelta(days=2)
        date_range_end = transaction['date'] + timedelta(days=2)
        
        print(f"\nLooking for matching transfer:")
        print(f"  Date: {transaction['date']}")
        print(f"  Amount: ${abs(amount):.2f}")
        print(f"  Description: {transaction['description']}")
        
        for other_tx in self.raw_transactions:
            if 'processed' in other_tx and other_tx['processed']:
                continue
                
            if (other_tx['account'] != transaction['account'] and 
                isinstance(other_tx['date'], datetime) and
                date_range_start <= other_tx['date'] <= date_range_end and
                abs(other_tx['amount']) == abs(amount) and
                (other_tx['amount'] < 0) == (transaction['amount'] > 0)):
                
                print(f"  Found match:")
                print(f"    Date: {other_tx['date']}")
                print(f"    Amount: ${abs(other_tx['amount']):.2f}")
                print(f"    Description: {other_tx['description']}")
                return other_tx
        
        print("  No match found")
        return None
    
    def _create_processed_transaction(self, transaction):
        """
        Create a processed transaction with appropriate double entries.
        
        Args:
            transaction (dict): Raw transaction
            
        Returns:
            dict: Processed transaction
        """
        # Create base transaction record
        processed_transaction = {
            'id': str(uuid.uuid4()),
            'date': transaction['date'],
            'description': transaction['description'],
            'category': transaction['category'],
            'entries': []
        }
        
        account = transaction['account']
        amount = transaction['amount']
        is_transfer = transaction['is_transfer']
        account_reference = transaction['account_reference']
        account_type = self.accounts[account]['type']
        
        # Process based on account type
        if account_type == 'LIABILITY':
            self._process_liability_transaction(processed_transaction, transaction)
        elif account_type == 'ASSET':
            self._process_asset_transaction(processed_transaction, transaction)
        
        # Validate that debits equal credits
        total_debits = sum(entry['amount'] for entry in processed_transaction['entries'] if entry['type'] == 'DEBIT')
        total_credits = sum(entry['amount'] for entry in processed_transaction['entries'] if entry['type'] == 'CREDIT')
        
        if abs(total_debits - total_credits) > 0.01:
            print(f"Warning: Transaction {processed_transaction['id']} is not balanced:")
            print(f"  Description: {processed_transaction['description']}")
            print(f"  Total Debits: ${total_debits:.2f}")
            print(f"  Total Credits: ${total_credits:.2f}")
            print(f"  Difference: ${abs(total_debits - total_credits):.2f}")
            for entry in processed_transaction['entries']:
                print(f"  {entry['type']}: {entry['account']} ${entry['amount']:.2f}")
        
        return processed_transaction
    
    def _process_liability_transaction(self, processed_transaction, transaction):
        """
        Process a liability (credit card) transaction.
        
        Args:
            processed_transaction (dict): Processed transaction to add entries to
            transaction (dict): Raw transaction
        """
        account = transaction['account']
        amount = transaction['amount']
        is_transfer = transaction['is_transfer']
        
        if amount < 0:  # Expense on credit card
            self._add_entry(processed_transaction, 'expense', abs(amount), 'DEBIT')
            self._add_entry(processed_transaction, account, abs(amount), 'CREDIT')
        else:  # Payment to credit card
            self._add_entry(processed_transaction, account, amount, 'DEBIT')
            
            # Handle the credit side of the transaction
            if is_transfer:
                self._handle_transfer_credit(processed_transaction, transaction)
            else:
                # External payment source
                self._add_entry(processed_transaction, 'transfer', amount, 'CREDIT')
    
    def _process_asset_transaction(self, processed_transaction, transaction):
        """
        Process an asset (debit/savings) transaction.
        
        Args:
            processed_transaction (dict): Processed transaction to add entries to
            transaction (dict): Raw transaction
        """
        account = transaction['account']
        amount = transaction['amount']
        is_transfer = transaction['is_transfer']
        account_reference = transaction['account_reference']
        
        if amount < 0:  # Money going out
            # Handle the debit side of the transaction
            if is_transfer:
                self._handle_transfer_debit(processed_transaction, transaction)
            else:
                self._add_entry(processed_transaction, 'expense', abs(amount), 'DEBIT')
            
            # Credit the source account
            self._add_entry(processed_transaction, account, abs(amount), 'CREDIT')
        else:  # Money coming in
            # Debit the destination account
            self._add_entry(processed_transaction, account, amount, 'DEBIT')
            
            # Handle the credit side of the transaction
            if is_transfer:
                self._handle_transfer_credit(processed_transaction, transaction)
            else:
                # All incoming money is treated as income
                self._add_entry(processed_transaction, 'income', amount, 'CREDIT')
    
    def _handle_transfer_debit(self, processed_transaction, transaction):
        """
        Handle the debit side of a transfer transaction.
        
        Args:
            processed_transaction (dict): Processed transaction to add entries to
            transaction (dict): Raw transaction
        """
        amount = transaction['amount']
        account_reference = transaction['account_reference']
        
        if account_reference:
            # Try to identify destination account
            dest_account = self.find_account_by_reference(account_reference)
            if dest_account:
                self._add_entry(processed_transaction, dest_account, abs(amount), 'DEBIT')
                return
        
        # Default to transfer account if no specific destination found
        self._add_entry(processed_transaction, 'transfer', abs(amount), 'DEBIT')
    
    def _handle_transfer_credit(self, processed_transaction, transaction):
        """
        Handle the credit side of a transfer transaction.
        
        Args:
            processed_transaction (dict): Processed transaction to add entries to
            transaction (dict): Raw transaction
        """
        account = transaction['account']
        amount = transaction['amount']
        account_reference = transaction['account_reference']
        
        # For liability accounts, try to find matching transfer
        if self.accounts[account]['type'] == 'LIABILITY':
            matching_transfer = self.find_matching_transfer(transaction, amount)
            if matching_transfer:
                self._add_entry(processed_transaction, matching_transfer['account'], amount, 'CREDIT')
                matching_transfer['processed'] = True
                return
        
        # For asset accounts with reference, try to identify source account
        if account_reference:
            source_account = self.find_account_by_reference(account_reference)
            if source_account:
                self._add_entry(processed_transaction, source_account, amount, 'CREDIT')
                return
        
        # Default to transfer account if no specific source found
        self._add_entry(processed_transaction, 'transfer', amount, 'CREDIT')
    
    def _add_entry(self, processed_transaction, account, amount, entry_type):
        """
        Add an entry to the processed transaction.
        
        Args:
            processed_transaction (dict): Processed transaction to add entry to
            account (str): Account name
            amount (float): Entry amount
            entry_type (str): Entry type (DEBIT or CREDIT)
        """
        processed_transaction['entries'].append({
            'account': account,
            'amount': amount,
            'type': entry_type
        })
    
    def process_raw_transactions(self):
        """Process raw transactions into double-entry format."""
        # Sort transactions by date
        sorted_transactions = sorted(self.raw_transactions, 
                                   key=lambda x: x['date'] if isinstance(x['date'], datetime) else datetime.now())
        
        for transaction in sorted_transactions:
            # Skip already processed transactions
            if 'processed' in transaction and transaction['processed']:
                continue
            
            # Process the transaction
            processed_transaction = self._create_processed_transaction(transaction)
            
            # Mark transaction as processed
            transaction['processed'] = True
            
            # Add to processed transactions
            self.processed_transactions.append(processed_transaction)
    
    def update_account_balances(self):
        """Update all account balances based on processed transactions."""
        # Reset balances
        self.account_balances = {account: 0 for account in self.accounts}
        
        # Sort transactions by date
        sorted_transactions = sorted(self.processed_transactions, 
                                   key=lambda x: x['date'] if isinstance(x['date'], datetime) else datetime.now())
        
        # Process each transaction
        for transaction in sorted_transactions:
            # Create a unified transaction record
            unified_transaction = {
                'id': transaction['id'],
                'date': transaction['date'].strftime('%Y-%m-%d') if isinstance(transaction['date'], datetime) else str(transaction['date']),
                'description': transaction['description'],
                'category': transaction['category'],
                'entries': [],
                'balances': {}
            }
            
            # Process each entry in the transaction
            for entry in transaction['entries']:
                account = entry['account']
                amount = entry['amount']
                entry_type = entry['type']
                
                # Update account balance based on entry type and account type
                if account in self.accounts:
                    account_type = self.accounts[account]['type']
                    
                    if entry_type == 'DEBIT':
                        if account_type in ['ASSET', 'EXPENSE']:
                            self.account_balances[account] += amount
                        else:  # LIABILITY, EQUITY, INCOME
                            self.account_balances[account] -= amount
                    else:  # CREDIT
                        if account_type in ['ASSET', 'EXPENSE']:
                            self.account_balances[account] -= amount
                        else:  # LIABILITY, EQUITY, INCOME
                            self.account_balances[account] += amount
                
                # Add entry to unified transaction
                unified_transaction['entries'].append({
                    'account': account,
                    'account_name': self.accounts[account]['name'] if account in self.accounts else "Unknown",
                    'amount': amount,
                    'type': entry_type
                })
            
            # Add the current balances to the transaction
            unified_transaction['balances'] = self.account_balances.copy()
            
            # Add the unified transaction to the list
            self.unified_transactions.append(unified_transaction)
    
    def verify_double_entry_accounting(self, transactions):
        """
        Verify that transactions follow double-entry accounting principles.
        
        Args:
            transactions (list): List of transactions to verify
            
        Returns:
            bool: True if transactions are balanced, False otherwise
        """
        # Initialize account balances
        account_balances = {}
        account_types = {
            'credit_card': 'LIABILITY',
            'debit': 'ASSET',
            'emergency_fund': 'ASSET',
            'old_credit_card': 'LIABILITY',
            'saver': 'ASSET'
        }
        
        print("\nVerifying double-entry accounting...")
        print("Processing transactions chronologically:")
        
        # Process all transactions
        for transaction in transactions:
            amount = transaction['amount']
            account_id = transaction['account_id']
            account_type = account_types.get(account_id)
            
            if account_id not in account_balances:
                account_balances[account_id] = 0.0
            
            # For all transactions:
            # - ASSET accounts: positive = debit (increase), negative = credit (decrease)
            # - LIABILITY accounts: positive = credit (increase), negative = debit (decrease)
            if account_type == 'LIABILITY':
                # For liabilities, we invert the sign to match double-entry principles
                amount = -amount
            
            account_balances[account_id] += amount
            
            print(f"\nTransaction: {transaction.get('description', 'Unknown')}")
            print(f"  Date: {transaction.get('date', 'Unknown')}")
            print(f"  Account: {account_id} ({account_type})")
            print(f"  Amount: ${abs(amount):.2f}")
            print(f"  Current balance: ${account_balances[account_id]:.2f}")
        
        # Calculate total debits and credits
        total_debits = sum(balance for balance in account_balances.values() if balance > 0)
        total_credits = abs(sum(balance for balance in account_balances.values() if balance < 0))
        
        # Print balances for debugging
        print("\nFinal Account Balances:")
        for account, balance in sorted(account_balances.items()):
            account_type = account_types.get(account)
            if account_type == 'LIABILITY':
                # For display, show liability balances as negative
                balance = -balance
            print(f"{account} ({account_type}): ${balance:.2f}")
        
        print(f"\nSummary:")
        print(f"Total Debits: ${total_debits:.2f}")
        print(f"Total Credits: ${total_credits:.2f}")
        print(f"Difference: ${abs(total_debits - total_credits):.2f}")
        
        # Check if debits equal credits (allowing for small floating point differences)
        is_balanced = abs(total_debits - total_credits) < 0.01
        print(f"\nDouble-entry accounting is {'balanced' if is_balanced else 'NOT balanced'}")
        
        return is_balanced
    
    def prepare_for_up_bank_api(self):
        """
        Convert transactions to Up Bank API format.
        
        Returns:
            list: Transactions in Up Bank API format
        """
        up_bank_transactions = []
        
        for transaction in self.unified_transactions:
            # Get the main entry details - prioritize real accounts over transfer/expense/income
            main_entry = next((entry for entry in transaction['entries'] 
                             if entry['account'] in ['credit_card', 'debit', 'emergency_fund', 'saver', 'old_credit_card']), None)
            
            if not main_entry:
                main_entry = next((entry for entry in transaction['entries']), None)
                
            if not main_entry:
                continue
                
            # Determine transaction amount - positive for income, negative for expense
            amount = 0
            source_account = None
            
            # Find the affected real account
            for entry in transaction['entries']:
                if entry['account'] in ['credit_card', 'debit', 'emergency_fund', 'saver', 'old_credit_card']:
                    source_account = entry['account']
                    # For assets, debits increase (+), credits decrease (-)
                    # For liabilities, debits decrease (+), credits increase (-)
                    account_type = self.accounts[entry['account']]['type']
                    
                    if account_type == 'ASSET':
                        amount = entry['amount'] if entry['type'] == 'DEBIT' else -entry['amount']
                    else:  # LIABILITY
                        amount = -entry['amount'] if entry['type'] == 'DEBIT' else entry['amount']
                    
                    break
            
            # If no real account found, skip
            if not source_account:
                continue
                
            account_id = self.accounts[source_account]['id']
            account_name = self.accounts[source_account]['name']
            account_type = self.accounts[source_account]['api_type']
            
            tx_date = transaction['date']
            if isinstance(tx_date, datetime):
                tx_date = tx_date.strftime('%Y-%m-%d')
            
            up_transaction = {
                "type": "transactions",
                "id": transaction['id'],
                "attributes": {
                    "status": "SETTLED",
                    "rawText": transaction['description'],
                    "description": transaction['description'],
                    "message": None,
                    "isCategorizable": True,
                    "amount": {
                        "currencyCode": "AUD",
                        "value": f"{abs(amount):.2f}",
                        "valueInBaseUnits": int(abs(amount) * 100)
                    },
                    "foreignAmount": None,
                    "settledAt": f"{tx_date}T00:00:00+10:00",
                    "createdAt": f"{tx_date}T00:00:00+10:00",
                    "category": transaction['category']
                },
                "relationships": {
                    "account": {
                        "data": {
                            "type": "accounts",
                            "id": account_id
                        }
                    }
                },
                "accountDetails": {
                    "displayName": account_name,
                    "accountType": account_type,
                    "ownershipType": "INDIVIDUAL"
                }
            }
            
            is_transfer = any(entry['account'] == 'transfer' for entry in transaction['entries'])
            if is_transfer:
                account_entries = [entry for entry in transaction['entries'] 
                                  if entry['account'] in ['credit_card', 'debit', 'emergency_fund', 'saver', 'old_credit_card'] 
                                  and entry['account'] != source_account]
                
                if account_entries:
                    transfer_account = account_entries[0]['account']
                    up_transaction["relationships"]["transferAccount"] = {
                        "data": {
                            "type": "accounts",
                            "id": self.accounts[transfer_account]['id']
                        }
                    }
            
            up_bank_transactions.append(up_transaction)
            
        return up_bank_transactions 