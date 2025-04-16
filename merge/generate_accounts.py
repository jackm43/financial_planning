import json
import uuid
from collections import defaultdict

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

def generate_accounts(transactions_file):
    """Generate accounts data from transactions"""
    # Load transactions
    transactions = load_json_file(transactions_file)
    if not transactions:
        return None
    
    # Extract unique accounts
    accounts = {}
    account_balances = defaultdict(float)
    
    for tx in transactions.get('data', []):
        account_details = tx.get('accountDetails', {})
        if not account_details:
            continue
            
        account_name = account_details.get('displayName', '')
        if not account_name:
            continue
            
        # Create account if not exists
        if account_name not in accounts:
            accounts[account_name] = {
                "type": "accounts",
                "id": str(uuid.uuid4()),
                "attributes": {
                    "displayName": account_name,
                    "accountType": account_details.get('accountType', 'UNKNOWN'),
                    "ownershipType": account_details.get('ownershipType', 'INDIVIDUAL'),
                    "balance": {
                        "currencyCode": "AUD",
                        "value": "0.00",
                        "valueInBaseUnits": 0
                    }
                }
            }
        
        # Update balance
        amount = float(tx.get('attributes', {}).get('amount', {}).get('value', '0'))
        account_balances[account_name] += amount
    
    # Update balances in accounts
    for account_name, balance in account_balances.items():
        accounts[account_name]['attributes']['balance']['value'] = f"{balance:.2f}"
        accounts[account_name]['attributes']['balance']['valueInBaseUnits'] = int(balance * 100)
    
    return {
        "data": list(accounts.values()),
        "links": {
            "prev": None,
            "next": None
        }
    }

def main():
    # Generate accounts from transactions
    accounts = generate_accounts('combined_transactions.json')
    if accounts:
        save_json_file(accounts, 'combined_accounts.json')
        print(f"Generated {len(accounts['data'])} accounts")
    else:
        print("Failed to generate accounts")

if __name__ == "__main__":
    main() 