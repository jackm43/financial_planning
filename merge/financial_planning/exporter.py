import json
from datetime import datetime

class Exporter:
    """Exports transactions and accounts to various formats."""
    
    def __init__(self, accounts=None, account_balances=None):
        """
        Initialize the exporter.
        
        Args:
            accounts (dict, optional): Dictionary of accounts. Defaults to None.
            account_balances (dict, optional): Dictionary of account balances. Defaults to None.
        """
        self.accounts = accounts or {}
        self.account_balances = account_balances or {}
    
    def prepare_transactions_for_up_bank(self, transactions):
        """
        Prepare transactions for Up Bank API format.
        
        Args:
            transactions (list): List of transactions
            
        Returns:
            list: Transactions in Up Bank API format
        """
        up_bank_transactions = []
        
        for transaction in transactions:
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
    
    def prepare_accounts_for_up_bank(self):
        """
        Prepare accounts for Up Bank API format.
        
        Returns:
            list: Accounts in Up Bank API format
        """
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
        
        return account_data
    
    def export_to_json(self, transactions, transactions_file, accounts_file):
        """
        Export transactions and accounts to JSON files.
        
        Args:
            transactions (list): List of transactions
            transactions_file (str): Path to transactions JSON file
            accounts_file (str): Path to accounts JSON file
        """
        # Export transactions
        up_bank_data = {
            "data": self.prepare_transactions_for_up_bank(transactions),
            "links": {
                "prev": None,
                "next": None
            }
        }
        
        with open(transactions_file, 'w') as f:
            json.dump(up_bank_data, f, indent=2)
            
        print(f"Exported {len(transactions)} transactions to {transactions_file}")
        
        # Export accounts
        account_data = {
            "data": self.prepare_accounts_for_up_bank(),
            "links": {
                "prev": None,
                "next": None
            }
        }
        
        with open(accounts_file, 'w') as f:
            json.dump(account_data, f, indent=2)
            
        print(f"Exported {len(self.prepare_accounts_for_up_bank())} accounts to {accounts_file}")
    
    def export_account_balances(self):
        """Export account balances to console."""
        print("\nAccount Balances:")
        for account, balance in self.account_balances.items():
            if account in self.accounts:
                print(f"{self.accounts[account]['name']}: ${balance:.2f}")
    
    def export_statistics(self, transactions):
        """
        Export transaction statistics to console.
        
        Args:
            transactions (list): List of transactions
        """
        print(f"\nStatistics:")
        print(f"Total transactions: {len(transactions)}")
        
        # Category breakdown
        categories = {}
        for tx in transactions:
            category = tx.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        print("\nCategory Breakdown:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"{category}: {count} transactions") 