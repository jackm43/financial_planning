import os
import pandas as pd
import csv
from datetime import datetime, timedelta
import json
import uuid
import re
from datetime import datetime
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
commbank_dir = os.path.join(project_root, 'commbank_csv')

commbank_dirs = [d for d in os.listdir(commbank_dir) if os.path.isdir(os.path.join(commbank_dir, d)) and re.match(r'\d{2}-\d{2}-\d{4}', d)]

if not commbank_dirs:
    raise ValueError(f"No date folders found in {commbank_dir}. Please ensure the directory contains folders with format DD-MM-YYYY.")

today = datetime.now()
commbank_dirs = sorted(commbank_dirs, 
                      key=lambda x: abs((datetime.strptime(x, '%d-%m-%Y') - today).days))

latest_dir = max(commbank_dirs, key=lambda x: datetime.strptime(x, '%d-%m-%Y'))
commbank_dir = os.path.join(commbank_dir, latest_dir)

print(f"Using CommBank data from: {commbank_dir}")

class EnhancedDoubleEntryAccountingSystem:
    def __init__(self):
        self.accounts = {
            'credit_card': {'name': 'Credit Card', 'type': 'LIABILITY', 'id': str(uuid.uuid4()), 'api_type': 'TRANSACTIONAL'},
            'debit': {'name': 'Debit Account', 'type': 'ASSET', 'id': str(uuid.uuid4()), 'api_type': 'TRANSACTIONAL'},
            'emergency_fund': {'name': 'Emergency Fund', 'type': 'ASSET', 'id': str(uuid.uuid4()), 'api_type': 'SAVER'},
            'old_credit_card': {'name': 'Old Credit Card', 'type': 'LIABILITY', 'id': str(uuid.uuid4()), 'api_type': 'TRANSACTIONAL'},
            'saver': {'name': 'Savings Account', 'type': 'ASSET', 'id': str(uuid.uuid4()), 'api_type': 'SAVER'},
            'expense': {'name': 'Expenses', 'type': 'EXPENSE', 'id': None, 'api_type': None},
            'income': {'name': 'Income', 'type': 'INCOME', 'id': None, 'api_type': None},
            'transfer': {'name': 'Internal Transfers', 'type': 'EQUITY', 'id': None, 'api_type': None},
        }
        
        self.raw_transactions = []
        self.processed_transactions = []
        self.unified_transactions = []
        
        self.account_balances = {account: 0 for account in self.accounts}
        
        self.categories = {
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
        
        self.pending_transfers = []
    
    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:

            return date_str
    
    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        if isinstance(amount_str, str):

            amount_str = amount_str.replace(',', '')
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            amount_str = amount_str.strip('"')
            
            try:
                return float(amount_str)
            except ValueError:
                return 0
        return amount_str
    
    def clean_description(self, description):
        """Clean and standardize description"""
        if isinstance(description, str):
            description = description.strip('"')
            description = ' '.join(description.split())
            return description
        return ""
    
    def categorize_transaction(self, description):
        """Categorize a transaction based on its description"""
        description_upper = description.upper()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.upper() in description_upper:
                    return category
        
        return 'uncategorized'
    
    def is_transfer(self, description):
        """Check if a transaction is likely a transfer between accounts"""
        description_upper = description.upper()
        
        transfer_keywords = [
            'TRANSFER TO', 'TRANSFER FROM', 'BPAY', 'NETBANK', 'COMMBANK APP'
        ]
        
        for keyword in transfer_keywords:
            if keyword.upper() in description_upper:
                return True
        
        return False
    
    def extract_account_reference(self, description):
        """Extract account reference from description"""
        account_match = re.search(r'xx(\d+)', description)
        if account_match:
            return account_match.group(0)
        return None
    
    def load_credit_card(self, filepath, account_type='credit_card'):
        """Load credit card transactions from CSV file"""
        try:
            with open(filepath, 'r') as file:
                reader = csv.reader(file)
                rows = list(reader)
            
            for row in rows:
                if len(row) >= 3:
                    date = self.parse_date(row[0])
                    amount = self.parse_amount(row[1])
                    description = self.clean_description(row[2])
                    
                    if amount != 0:
                        transaction = {
                            'source_file': filepath,
                            'date': date,
                            'amount': amount,
                            'description': description,
                            'account': account_type,
                            'category': self.categorize_transaction(description),
                            'is_transfer': self.is_transfer(description),
                            'account_reference': self.extract_account_reference(description)
                        }
                        
                        self.raw_transactions.append(transaction)
        except Exception as e:
            print(f"Error loading {filepath}: {str(e)}")
    
    def load_bank_account(self, filepath, account_type):
        """Load bank account transactions from CSV file"""
        try:
            with open(filepath, 'r') as file:
                reader = csv.reader(file)
                rows = list(reader)
            
            for row in rows:
                if len(row) >= 3:  
                    date = self.parse_date(row[0])
                    amount = self.parse_amount(row[1])
                    description = self.clean_description(row[2])
                    balance = self.parse_amount(row[3]) if len(row) > 3 and row[3] else None
                    
                    if amount != 0:
                        transaction = {
                            'source_file': filepath,
                            'date': date,
                            'amount': amount,
                            'description': description,
                            'balance': balance,
                            'account': account_type,
                            'category': self.categorize_transaction(description),
                            'is_transfer': self.is_transfer(description),
                            'account_reference': self.extract_account_reference(description)
                        }
                        
                        self.raw_transactions.append(transaction)
        except Exception as e:
            print(f"Error loading {filepath}: {str(e)}")
    
    def process_raw_transactions(self):
        """Process raw transactions into double-entry format"""
        sorted_transactions = sorted(self.raw_transactions, 
                                   key=lambda x: x['date'] if isinstance(x['date'], datetime) else datetime.now())
        
        for transaction in sorted_transactions:
            if 'processed' in transaction and transaction['processed']:
                continue
            
            processed_transaction = self._create_processed_transaction(transaction)
            
            transaction['processed'] = True
            
            self.processed_transactions.append(processed_transaction)
    
    def _create_processed_transaction(self, transaction):
        """Create a processed transaction with appropriate double entries"""
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
        
        if account_type == 'LIABILITY':
            self._process_liability_transaction(processed_transaction, transaction)
        elif account_type == 'ASSET':
            self._process_asset_transaction(processed_transaction, transaction)
        
        return processed_transaction
    
    def _process_liability_transaction(self, processed_transaction, transaction):
        """Process a liability (credit card) transaction"""
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
        """Process an asset (debit/savings) transaction"""
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
        """Handle the debit side of a transfer transaction"""
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
        """Handle the credit side of a transfer transaction"""
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
        """Add an entry to the processed transaction"""
        processed_transaction['entries'].append({
            'account': account,
            'amount': amount,
            'type': entry_type
        })
    
    def find_matching_transfer(self, transaction, amount):
        """Find a matching transfer transaction from another account"""
        # Transfers are usually within 1-2 days of each other
        if not isinstance(transaction['date'], datetime):
            return None
            
        date_range_start = transaction['date'] - timedelta(days=2)
        date_range_end = transaction['date'] + timedelta(days=2)
        
        for other_tx in self.raw_transactions:
            if 'processed' in other_tx and other_tx['processed']:
                continue
                
            if (other_tx['account'] != transaction['account'] and 
                isinstance(other_tx['date'], datetime) and
                date_range_start <= other_tx['date'] <= date_range_end and
                abs(other_tx['amount']) == abs(amount) and
                (other_tx['amount'] < 0) == (transaction['amount'] > 0)):
                
                return other_tx
        
        return None

    def find_account_by_reference(self, account_reference):
            """Find the account matching a reference in a transaction description"""
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
    
    def update_account_balances(self):
        """Update all account balances based on processed transactions"""
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
    
    def prepare_for_up_bank_api(self):
        """Convert transactions to Up Bank API format"""
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
    
    def export_to_json(self, output_file):
        """Export transactions to JSON in Up Bank API format"""
        up_bank_data = {
            "data": self.prepare_for_up_bank_api(),
            "links": {
                "prev": None,
                "next": None
            }
        }
        
        output_path = os.path.join(project_root, 'outputs', output_file)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(up_bank_data, f, indent=2)
            
        print(f"Exported {len(self.unified_transactions)} transactions to {output_file}")
        
    def export_accounts_to_json(self, output_file):
        """Export accounts to JSON in Up Bank API format"""
        account_data = []
        
        for account_key, account_info in self.accounts.items():
            if account_info['id']:  
                account_data.append({
                    "type": "accounts",
                    "id": account_info['id'],
                    "attributes": {
                        "displayName": account_info['name'],
                        "accountType": account_info['api_type'],
                        "ownershipType": "INDIVIDUAL",
                        "balance": {
                            "currencyCode": "AUD",
                            "value": f"{self.account_balances[account_key]:.2f}",
                            "valueInBaseUnits": int(self.account_balances[account_key] * 100)
                        },
                        "createdAt": "2023-01-01T00:00:00+10:00"
                    }
                })
            
        print(f"Exported {len(account_data)} accounts to {output_file}")
        
    def verify_double_entry_accounting(self):
        """Verify double-entry accounting principles are maintained"""
        total_debits = sum(balance for account, balance in self.account_balances.items() 
                         if account in self.accounts and self.accounts[account]['type'] in ['ASSET', 'EXPENSE'])
        
        total_credits = sum(balance for account, balance in self.account_balances.items() 
                          if account in self.accounts and self.accounts[account]['type'] in ['LIABILITY', 'EQUITY', 'INCOME'])
        
        print(f"\nDouble-Entry Verification:")
        print(f"Total Debits (Assets + Expenses): ${total_debits:.2f}")
        print(f"Total Credits (Liabilities + Equity + Income): ${total_credits:.2f}")
        print(f"Difference: ${total_debits - total_credits:.2f}")
        
        return abs(total_debits - total_credits) < 0.01  # Allow for small rounding errors
    
    def print_account_balances(self):
        """Print the current balance of all accounts"""
        print("\nAccount Balances:")
        for account, balance in self.account_balances.items():
            if account in self.accounts:
                print(f"{self.accounts[account]['name']}: ${balance:.2f}")

def process_bank_data():
    accounting_system = EnhancedDoubleEntryAccountingSystem()
    
    accounting_system.load_credit_card(os.path.join(commbank_dir, 'CBA_CC.csv'), 'credit_card')
    accounting_system.load_bank_account(os.path.join(commbank_dir, 'CBA_DEBIT.csv'), 'debit')
    accounting_system.load_bank_account(os.path.join(commbank_dir, 'CBA_EMERGENCY_FUND.csv'), 'emergency_fund')
    accounting_system.load_credit_card(os.path.join(commbank_dir, 'CBA_OLD_CC.csv'), 'old_credit_card')
    accounting_system.load_bank_account(os.path.join(commbank_dir, 'CBA_SAVER.csv'), 'saver')
    
    accounting_system.process_raw_transactions()
    accounting_system.update_account_balances()
    
    accounting_system.print_account_balances()
    accounting_system.verify_double_entry_accounting()
    
    accounting_system.export_to_json('combined_transactions.json')
    accounting_system.export_accounts_to_json('accounts.json')
    
    print(f"\nStatistics:")
    print(f"Total raw transactions: {len(accounting_system.raw_transactions)}")
    print(f"Total processed transactions: {len(accounting_system.processed_transactions)}")
    print(f"Total unified transactions: {len(accounting_system.unified_transactions)}")
    
    categories = {}
    for tx in accounting_system.unified_transactions:
        category = tx.get('category', 'uncategorized')
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    print("\nCategory Breakdown:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{category}: {count} transactions")

if __name__ == "__main__":
    process_bank_data()