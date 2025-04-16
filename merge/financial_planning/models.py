from datetime import datetime
import uuid

class Transaction:
    """Represents a financial transaction from a bank statement."""
    
    def __init__(self, source_file, date, amount, description, account, category=None, 
                 is_transfer=False, account_reference=None, balance=None):
        """
        Initialize a transaction.
        
        Args:
            source_file (str): The source file of the transaction
            date (datetime): The date of the transaction
            amount (float): The amount of the transaction
            description (str): The description of the transaction
            account (str): The account the transaction belongs to
            category (str, optional): The category of the transaction. Defaults to None.
            is_transfer (bool, optional): Whether the transaction is a transfer. Defaults to False.
            account_reference (str, optional): Reference to another account. Defaults to None.
            balance (float, optional): The balance after the transaction. Defaults to None.
        """
        self.source_file = source_file
        self.date = date
        self.amount = amount
        self.description = description
        self.account = account
        self.category = category
        self.is_transfer = is_transfer
        self.account_reference = account_reference
        self.balance = balance
        
    def to_dict(self):
        """Convert the transaction to a dictionary."""
        return {
            'source_file': self.source_file,
            'date': self.date,
            'amount': self.amount,
            'description': self.description,
            'account': self.account,
            'category': self.category,
            'is_transfer': self.is_transfer,
            'account_reference': self.account_reference,
            'balance': self.balance
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a transaction from a dictionary."""
        return cls(
            source_file=data.get('source_file'),
            date=data.get('date'),
            amount=data.get('amount'),
            description=data.get('description'),
            account=data.get('account'),
            category=data.get('category'),
            is_transfer=data.get('is_transfer', False),
            account_reference=data.get('account_reference'),
            balance=data.get('balance')
        )


class Account:
    """Represents a financial account."""
    
    def __init__(self, name, account_type, account_id=None, api_type=None):
        """
        Initialize an account.
        
        Args:
            name (str): The name of the account
            account_type (str): The type of account (ASSET, LIABILITY, EXPENSE, INCOME, EQUITY)
            account_id (str, optional): The ID of the account. Defaults to None.
            api_type (str, optional): The API type of the account. Defaults to None.
        """
        self.name = name
        self.account_type = account_type
        self.account_id = account_id or str(uuid.uuid4())
        self.api_type = api_type
        
    def to_dict(self):
        """Convert the account to a dictionary."""
        return {
            'name': self.name,
            'type': self.account_type,
            'id': self.account_id,
            'api_type': self.api_type
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an account from a dictionary."""
        return cls(
            name=data.get('name'),
            account_type=data.get('type'),
            account_id=data.get('id'),
            api_type=data.get('api_type')
        )


class Category:
    """Represents a transaction category with keywords for matching."""
    
    def __init__(self, name, keywords):
        """
        Initialize a category.
        
        Args:
            name (str): The name of the category
            keywords (list): List of keywords to match transactions
        """
        self.name = name
        self.keywords = keywords
        
    def matches(self, description):
        """
        Check if a description matches this category.
        
        Args:
            description (str): The description to check
            
        Returns:
            bool: True if the description matches, False otherwise
        """
        description_upper = description.upper()
        return any(keyword.upper() in description_upper for keyword in self.keywords)
    
    def to_dict(self):
        """Convert the category to a dictionary."""
        return {
            'name': self.name,
            'keywords': self.keywords
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a category from a dictionary."""
        return cls(
            name=data.get('name'),
            keywords=data.get('keywords', [])
        ) 