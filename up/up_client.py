import requests
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class UpBankClient:
    """Client for interacting with the Up Bank API"""
    
    BASE_URL = "https://api.up.com.au/api/v1"
    
    def __init__(self, api_token: str):
        """Initialize with API token"""
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
    
    def list_accounts(self, account_type: Optional[str] = None, ownership_type: Optional[str] = None) -> Dict:
        """
        Retrieve accounts from Up Bank
        
        Args:
            account_type: Filter by account type (SAVER, TRANSACTIONAL)
            ownership_type: Filter by ownership type (INDIVIDUAL, JOINT)
        
        Returns:
            Response data containing accounts
        """
        params = {}
        if account_type:
            params["filter[accountType]"] = account_type
        if ownership_type:
            params["filter[ownershipType]"] = ownership_type
            
        response = requests.get(
            f"{self.BASE_URL}/accounts", 
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_account(self, account_id: str) -> Dict:
        """
        Retrieve a specific account by ID
        
        Args:
            account_id: The unique identifier for the account
            
        Returns:
            Account data
        """
        response = requests.get(
            f"{self.BASE_URL}/accounts/{account_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_transactions(self, 
                         since: Optional[str] = None, 
                         until: Optional[str] = None,
                         page_size: int = 100,
                         status: Optional[str] = None,
                         category: Optional[str] = None,
                         tag: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
        """
        Retrieve transactions from Up Bank with pagination
        
        Args:
            since: Filter transactions since this RFC-3339 datetime YYYY-MM-DDTHH:MM:SS±HH:MM
            until: Filter transactions until this RFC-3339 datetime YYYY-MM-DDTHH:MM:SS±HH:MM
            page_size: Number of records per page
            status: Filter by status (HELD, SETTLED)
            category: Filter by category identifier
            tag: Filter by transaction tag
            
        Returns:
            Tuple of (transactions list, next page URL)
        """
        transactions = []
        params = {"page[size]": page_size}
        
        if since:
            params["filter[since]"] = since
        if until:
            params["filter[until]"] = until
        if status:
            params["filter[status]"] = status
        if category:
            params["filter[category]"] = category
        if tag:
            params["filter[tag]"] = tag
        
        url = f"{self.BASE_URL}/transactions"
        next_page = True
        
        while next_page:
            logger.debug(f"Fetching transactions from {url} with params {params}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            transactions.extend(data.get("data", []))
            
            next_url = data.get("links", {}).get("next")
            if next_url:
                url = next_url
                params = {}
            else:
                next_page = False
        
        return transactions, data.get("links", {}).get("next")