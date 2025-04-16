import json
import argparse
from datetime import datetime
import uuid

def load_json_file(filepath):
    """Load JSON data from a file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return None

def save_json_file(data, filepath):
    """Save JSON data to a file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved data to {filepath}")

def merge_transactions(our_transactions, upbank_transactions):
    """Merge our transaction data with Up Bank transaction data"""
    upbank_lookup = {}
    upbank_data = upbank_transactions.get('transactions', []) if isinstance(upbank_transactions, dict) else []
    for tx in upbank_data:
        settled_at = tx.get('attributes', {}).get('settledAt', '')
        if not settled_at:
            continue
        tx_date = settled_at.split('T')[0]
        tx_amount = tx.get('attributes', {}).get('amount', {}).get('value', '0')
        
        key = f"{tx_date}_{tx_amount}"
        if key not in upbank_lookup:
            upbank_lookup[key] = []
        upbank_lookup[key].append(tx)
    

    merged_transactions = []
    unmatched_transactions = []
    
    for our_tx in our_transactions.get('data', []):
        settled_at = our_tx.get('attributes', {}).get('settledAt', '')
        if not settled_at:
            unmatched_transactions.append(our_tx)
            continue
        tx_date = settled_at.split('T')[0]
        tx_amount = our_tx.get('attributes', {}).get('amount', {}).get('value', '0')
        
        key = f"{tx_date}_{tx_amount}"
        
        if key in upbank_lookup and upbank_lookup[key]:

            up_tx = upbank_lookup[key].pop(0)
            

            merged_tx = up_tx.copy()
            
            if 'accountDetails' in our_tx:
                merged_tx['accountDetails'] = our_tx['accountDetails']
            
            if 'category' in our_tx.get('attributes', {}) and 'category' not in up_tx.get('attributes', {}):
                merged_tx['attributes']['category'] = our_tx['attributes']['category']
            
            merged_transactions.append(merged_tx)
        else:
            unmatched_transactions.append(our_tx)
    
    for tx_list in upbank_lookup.values():
        for tx in tx_list:
            merged_transactions.append(tx)
    
    print(f"Merged transactions: {len(merged_transactions)}")
    print(f"Unmatched transactions from our data: {len(unmatched_transactions)}")
    
    all_transactions = merged_transactions + unmatched_transactions
    
    all_transactions.sort(key=lambda x: x.get('attributes', {}).get('settledAt', ''), reverse=True)
    
    return {
        "data": all_transactions,
        "links": {
            "prev": None,
            "next": None
        }
    }

def merge_accounts(our_accounts, upbank_accounts):
    """Merge our account data with Up Bank account data"""
    upbank_lookup = {}
    upbank_data = upbank_accounts.get('accounts', []) if isinstance(upbank_accounts, dict) else []
    for account in upbank_data:
        account_name = account.get('attributes', {}).get('displayName', '')
        upbank_lookup[account_name] = account
    
    merged_accounts = []
    
    for our_account in our_accounts.get('data', []):
        account_name = our_account.get('attributes', {}).get('displayName', '')
        
        if account_name in upbank_lookup:
            up_account = upbank_lookup.pop(account_name)
            
            merged_account = up_account.copy()
            merged_account['attributes']['balance'] = our_account['attributes']['balance']
            
            merged_accounts.append(merged_account)
        else:
            merged_accounts.append(our_account)
    
    for account in upbank_lookup.values():
        merged_accounts.append(account)
    
    print(f"Merged accounts: {len(merged_accounts)}")
    
    return {
        "data": merged_accounts,
        "links": {
            "prev": None,
            "next": None
        }
    }

def main():
    our_transactions_path = 'combined_transactions.json'
    our_accounts_path = 'combined_accounts.json'
    upbank_transactions_path = '../outputs/enriched_all_transactions.json'
    upbank_accounts_path = '../outputs/accounts.json'
    output_transactions_path = 'merged_transactions.json'
    output_accounts_path = 'merged_accounts.json'
    
    our_transactions = load_json_file(our_transactions_path)
    our_accounts = load_json_file(our_accounts_path)
    
    if not our_transactions:
        print(f"Warning: {our_transactions_path} not found. Creating empty transactions data.")
        our_transactions = {"data": [], "links": {"prev": None, "next": None}}
    
    if not our_accounts:
        print(f"Warning: {our_accounts_path} not found. Creating empty accounts data.")
        our_accounts = {"data": [], "links": {"prev": None, "next": None}}
    
    upbank_transactions = load_json_file(upbank_transactions_path)
    if not upbank_transactions:
        print(f"Warning: {upbank_transactions_path} not found. Creating empty transactions data.")
        upbank_transactions = {"data": [], "links": {"prev": None, "next": None}}
    
    upbank_accounts = load_json_file(upbank_accounts_path)
    if not upbank_accounts:
        print(f"Warning: {upbank_accounts_path} not found. Creating empty accounts data.")
        upbank_accounts = {"data": [], "links": {"prev": None, "next": None}}
    
    merged_transactions = merge_transactions(our_transactions, upbank_transactions)
    
    merged_accounts = merge_accounts(our_accounts, upbank_accounts)
    
    save_json_file(merged_transactions, output_transactions_path)
    save_json_file(merged_accounts, output_accounts_path)

if __name__ == "__main__":
    main()