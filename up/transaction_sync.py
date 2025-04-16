import os
import json
import requests
from typing import Dict, List, Optional, Any
from up.loggerino import Loggerino
from up.up_client import UpBankClient
from dotenv import load_dotenv

logger = Loggerino()

class TransactionSync:
    """Handles syncing and storing Up Bank transactions"""

    def __init__(self, client: UpBankClient, storage_dir):
        """
        Initialize the transaction sync
        
        Args:
            client: Up Bank API client
            storage_dir: Directory to store transaction data
        """
        self.client = client
        self.storage_dir = storage_dir
        self.transactions_file = os.path.join(storage_dir, "transactions.json")
        self.accounts_file = os.path.join(storage_dir, "accounts.json")
        self.sync_state_file = os.path.join(storage_dir, "sync_state.json")
        self.enriched_transactions_file = os.path.join(storage_dir, "enriched_transactions.json")
        self.all_transactions_file = os.path.join(storage_dir, "all_transactions.json")
        
        self._ensure_storage_dir_exists()
    
    def _ensure_storage_dir_exists(self) -> None:
        """Ensure the storage directory exists"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"Created storage directory: {self.storage_dir}")
    
    def _load_json_file(self, filepath: str, default_value: Any = None) -> Any:
        """Load data from a JSON file or return default value if file doesn't exist"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {filepath}: {e}")
                return default_value if default_value is not None else {}
        return default_value if default_value is not None else {}
    
    def _save_json_file(self, filepath: str, data: Any) -> None:
        """Save data to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")
            raise
    
    def get_last_sync_datetime(self) -> Optional[str]:
        """Get the datetime of the last synced transaction"""
        sync_state = self._load_json_file(self.sync_state_file, {"last_synced": None})
        return sync_state.get("last_synced")
    
    def is_last_sync_valid(self) -> bool:
        """Check if the last sync has a valid entry"""
        last_sync = self.get_last_sync_datetime()
        if not last_sync:
            return False
            
        transactions_data = self._load_json_file(self.transactions_file, {"transactions": []})
        if not transactions_data.get("transactions"):
            return False
            
        return True
    
    def update_last_sync_datetime(self, datetime_str: str) -> None:
        """Update the last sync datetime"""
        sync_state = self._load_json_file(self.sync_state_file, {})
        sync_state["last_synced"] = datetime_str
        self._save_json_file(self.sync_state_file, sync_state)
    
    def sync_accounts(self) -> List[Dict]:
        """Sync and store all accounts"""
        logger.info("Syncing accounts...")
        try:
            accounts_data = self.client.list_accounts()
            accounts = accounts_data.get("data", [])

            self._save_json_file(self.accounts_file, {"accounts": accounts})
            logger.info(f"Synced {len(accounts)} accounts")
            
            return accounts
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing accounts: {e}")
            return []
    
    def sync_transactions(self, full_sync: bool = False) -> int:
        """
        Sync transactions and store them
        
        Args:
            full_sync: If True, performs a full sync regardless of last sync state
            
        Returns:
            Number of new transactions synced
        """
        existing_data = self._load_json_file(self.transactions_file, {"transactions": []})
        existing_transactions = existing_data.get("transactions", [])
        
        all_transactions_data = self._load_json_file(self.all_transactions_file, {"transactions": []})
        all_transactions = all_transactions_data.get("transactions", [])
        
        since = None if full_sync else self.get_last_sync_datetime()
        
        logger.info(f"Syncing transactions {'(full sync)' if full_sync else f'since {since}'}")
        try:
            new_transactions, _ = self.client.list_transactions(since=since)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing transactions: {e}")
            return 0
        
        if not new_transactions:
            logger.info("No new transactions to sync")
            return 0
        
        most_recent_date = max(
            transaction["attributes"].get("createdAt") 
            for transaction in new_transactions 
            if transaction["attributes"].get("createdAt")
        )
        
        if not full_sync:
            existing_ids = {tx["id"] for tx in existing_transactions}
            
            new_unique_transactions = [
                tx for tx in new_transactions 
                if tx["id"] not in existing_ids
            ]
            
            combined_transactions = existing_transactions + new_unique_transactions
            
            combined_transactions.sort(
                key=lambda tx: tx["attributes"].get("createdAt", ""), 
                reverse=True
            )
            
            transactions_to_save = combined_transactions
            new_count = len(new_unique_transactions)
        else:
            transactions_to_save = new_transactions
            new_count = len(new_transactions)
        
        self._save_json_file(
            self.transactions_file, 
            {"transactions": transactions_to_save}
        )
        
        all_transaction_ids = {tx["id"] for tx in all_transactions}
        
        for transaction in transactions_to_save:
            if transaction["id"] not in all_transaction_ids:
                all_transactions.append(transaction)
                all_transaction_ids.add(transaction["id"])
        
        all_transactions.sort(
            key=lambda tx: tx["attributes"].get("createdAt", ""), 
            reverse=True
        )
        
        self._save_json_file(
            self.all_transactions_file, 
            {"transactions": all_transactions}
        )
        
        self.update_last_sync_datetime(most_recent_date)
        
        logger.info(f"Synced {new_count} new transactions. Total: {len(transactions_to_save)}, All-time: {len(all_transactions)}")
        return new_count
    
    def is_enriched(self) -> bool:
        """Check if transactions are already enriched"""
        return os.path.exists(self.enriched_transactions_file)
    
    def enrich_transactions_with_account_data(self) -> None:
        """Enrich transactions with detailed account information"""
        logger.info("Enriching transactions with account data")
        
        accounts_data = self._load_json_file(self.accounts_file, {"accounts": []})
        transactions_data = self._load_json_file(self.transactions_file, {"transactions": []})
        
        accounts = accounts_data.get("accounts", [])
        transactions = transactions_data.get("transactions", [])
        
        if not accounts or not transactions:
            logger.warning("No accounts or transactions to enrich")
            return
        
        account_lookup = {
            account["id"]: {
                "displayName": account["attributes"].get("displayName"),
                "accountType": account["attributes"].get("accountType"),
                "ownershipType": account["attributes"].get("ownershipType")
            }
            for account in accounts
        }
        
        for transaction in transactions:
            account_relationship = transaction.get("relationships", {}).get("account", {}).get("data", {})
            if account_relationship and "id" in account_relationship:
                account_id = account_relationship["id"]
                if account_id in account_lookup:
                    transaction["accountDetails"] = account_lookup[account_id]
        
        self._save_json_file(self.enriched_transactions_file, {"transactions": transactions})
        logger.info("Transactions enriched with account data")
        
        all_transactions_data = self._load_json_file(self.all_transactions_file, {"transactions": []})
        all_transactions = all_transactions_data.get("transactions", [])
        
        if all_transactions:
            for transaction in all_transactions:
                account_relationship = transaction.get("relationships", {}).get("account", {}).get("data", {})
                if account_relationship and "id" in account_relationship:
                    account_id = account_relationship["id"]
                    if account_id in account_lookup:
                        transaction["accountDetails"] = account_lookup[account_id]
            
            self._save_json_file(
                os.path.join(self.storage_dir, "enriched_all_transactions.json"), 
                {"transactions": all_transactions}
            )
            logger.info("All transactions history enriched with account data")
    
    def run_sync(self) -> bool:
        """
        Run the complete sync process
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            full_sync = not self.is_last_sync_valid()
            if full_sync:
                logger.info("No valid last sync found, performing full sync")
            
            self.sync_accounts()
            
            self.sync_transactions(full_sync=full_sync)
            
            if not self.is_enriched():
                logger.info("Transactions not enriched, enriching now")
                self.enrich_transactions_with_account_data()
            
            return True
        except Exception as e:
            logger.error(f"Error during sync process: {e}")
            return False


def main():
    """Main function to run the Up Bank transaction sync"""
    load_dotenv()
    
    api_token = os.environ.get("UP_BANK_API_TOKEN")
    storage_dir = os.environ.get("STORAGE_DIR")

    if not api_token:
        logger.error("API token not provided. Set UP_BANK_API_TOKEN in .env file")
        return 1
    
    try:
        client = UpBankClient(api_token)
        sync = TransactionSync(client, storage_dir)
        
        success = sync.run_sync()
        
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())