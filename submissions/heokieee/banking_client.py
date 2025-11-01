"""
Modern Banking Client - Modernized from legacy Python 2.7 code

This module provides a modern, robust banking client that integrates with
the Core Banking API. It demonstrates modernization best practices:

- Python 3.x syntax and features
- Modern HTTP client (requests library)
- Type hints for better code documentation
- Async/await support for better performance
- Comprehensive error handling
- Structured logging
- JWT authentication support
- Clean architecture with separation of concerns
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

import requests
import aiohttp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('banking_client.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TransferRequest:
    """Data class for transfer requests with validation."""
    from_account: str
    to_account: str
    amount: float
    
    def __post_init__(self):
        """Validate transfer request data."""
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if not self.from_account or not self.to_account:
            raise ValueError("Account numbers cannot be empty")
        if self.from_account == self.to_account:
            raise ValueError("Source and destination accounts must be different")


@dataclass
class TransferResponse:
    """Data class for transfer responses."""
    transaction_id: str
    status: str
    message: str
    from_account: str
    to_account: str
    amount: float


@dataclass
class AuthToken:
    """Data class for JWT authentication tokens."""
    token: str
    expires_at: datetime
    scope: str
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() >= self.expires_at
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"}


class BankingClientError(Exception):
    """Base exception for banking client errors."""
    pass


class AuthenticationError(BankingClientError):
    """Raised when authentication fails."""
    pass


class TransferError(BankingClientError):
    """Raised when transfer operations fail."""
    pass


class ValidationError(BankingClientError):
    """Raised when validation fails."""
    pass


class ModernBankingClient:
    """
    Modern banking client with advanced features and best practices.
    
    This class demonstrates modernization from legacy Python 2.7 code:
    - Uses modern requests library instead of urllib2
    - Implements proper session management with connection pooling
    - Provides both sync and async interfaces
    - Includes comprehensive error handling
    - Supports JWT authentication
    - Uses type hints and modern Python features
    """
    
    def __init__(self, base_url: str = "http://localhost:8123", timeout: int = 30):
        """
        Initialize the banking client.
        
        Args:
            base_url: Base URL for the banking API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._auth_token: Optional[AuthToken] = None
        
        # Configure session with retry strategy and connection pooling
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # Updated parameter name
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"Banking client initialized with base URL: {self.base_url}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.session.close()
        logger.info("Banking client session closed")
    
    def authenticate(self, username: str, password: str, scope: str = "transfer") -> AuthToken:
        """
        Authenticate and obtain JWT token.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            scope: Token scope (enquiry, transfer)
            
        Returns:
            AuthToken object with token details
            
        Raises:
            AuthenticationError: If authentication fails
        """
        url = f"{self.base_url}/authToken"
        params = {"claim": scope}
        payload = {"username": username, "password": password}
        
        try:
            logger.info(f"Authenticating user: {username} with scope: {scope}")
            response = self.session.post(
                url,
                json=payload,
                params=params,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            # Assuming token expires in 1 hour (adjust based on actual API)
            expires_at = datetime.now() + timedelta(hours=1)
            
            auth_token = AuthToken(
                token=token_data.get("token", ""),
                expires_at=expires_at,
                scope=scope
            )
            
            self._auth_token = auth_token
            logger.info("Authentication successful")
            return auth_token
            
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def transfer_funds(self, transfer_request: TransferRequest, use_auth: bool = False) -> TransferResponse:
        """
        Transfer funds between accounts.
        
        Args:
            transfer_request: Transfer request details
            use_auth: Whether to use JWT authentication
            
        Returns:
            TransferResponse object with transfer details
            
        Raises:
            TransferError: If transfer fails
            AuthenticationError: If authentication is required but not available
        """
        url = f"{self.base_url}/transfer"
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if required
        if use_auth:
            if not self._auth_token or self._auth_token.is_expired:
                raise AuthenticationError("Valid authentication token required")
            headers.update(self._auth_token.headers)
        
        payload = {
            "fromAccount": transfer_request.from_account,
            "toAccount": transfer_request.to_account,
            "amount": transfer_request.amount
        }
        
        try:
            logger.info(f"Transferring {transfer_request.amount} from {transfer_request.from_account} to {transfer_request.to_account}")
            
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            transfer_response = TransferResponse(
                transaction_id=response_data.get("transactionId", ""),
                status=response_data.get("status", ""),
                message=response_data.get("message", ""),
                from_account=response_data.get("fromAccount", ""),
                to_account=response_data.get("toAccount", ""),
                amount=response_data.get("amount", 0.0)
            )
            
            logger.info(f"Transfer successful: {transfer_response.transaction_id}")
            return transfer_response
            
        except requests.RequestException as e:
            logger.error(f"Transfer failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    raise TransferError(f"Transfer failed: {error_details}")
                except json.JSONDecodeError:
                    raise TransferError(f"Transfer failed: {e.response.text}")
            raise TransferError(f"Transfer failed: {e}")
    
    def validate_account(self, account_id: str) -> bool:
        """
        Validate if an account exists and is valid.
        
        Args:
            account_id: Account ID to validate
            
        Returns:
            True if account is valid, False otherwise
            
        Raises:
            ValidationError: If validation request fails
        """
        url = f"{self.base_url}/accounts/validate/{account_id}"
        
        try:
            logger.info(f"Validating account: {account_id}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            is_valid = result.get("valid", False)
            logger.info(f"Account {account_id} validation result: {is_valid}")
            return is_valid
            
        except requests.RequestException as e:
            logger.error(f"Account validation failed: {e}")
            raise ValidationError(f"Account validation failed: {e}")
    
    def get_accounts(self, use_auth: bool = False) -> list:
        """
        Get list of all accounts.
        
        Args:
            use_auth: Whether to use JWT authentication
            
        Returns:
            List of account objects
            
        Raises:
            BankingClientError: If request fails
        """
        url = f"{self.base_url}/accounts"
        headers = {}
        
        if use_auth:
            if not self._auth_token or self._auth_token.is_expired:
                raise AuthenticationError("Valid authentication token required")
            headers.update(self._auth_token.headers)
        
        try:
            logger.info("Fetching accounts list")
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            accounts = response.json()
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch accounts: {e}")
            raise BankingClientError(f"Failed to fetch accounts: {e}")
    
    def get_account_balance(self, account_id: str, use_auth: bool = False) -> Dict[str, Any]:
        """
        Get account balance.
        
        Args:
            account_id: Account ID to check
            use_auth: Whether to use JWT authentication
            
        Returns:
            Dictionary with balance information
            
        Raises:
            BankingClientError: If request fails
        """
        url = f"{self.base_url}/accounts/balance/{account_id}"
        headers = {}
        
        if use_auth:
            if not self._auth_token or self._auth_token.is_expired:
                raise AuthenticationError("Valid authentication token required")
            headers.update(self._auth_token.headers)
        
        try:
            logger.info(f"Fetching balance for account: {account_id}")
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            balance_info = response.json()
            logger.info(f"Balance retrieved for account {account_id}")
            return balance_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise BankingClientError(f"Failed to fetch balance: {e}")


class AsyncBankingClient:
    """
    Async version of the banking client for better performance in concurrent scenarios.
    """
    
    def __init__(self, base_url: str = "http://localhost:8123", timeout: int = 30):
        """Initialize async banking client."""
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._auth_token: Optional[AuthToken] = None
        
        # Configure connector with connection pooling
        self.connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        logger.info(f"Async banking client initialized with base URL: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.close()
        await self.connector.close()
        logger.info("Async banking client session closed")
    
    async def transfer_funds_async(self, transfer_request: TransferRequest, use_auth: bool = False) -> TransferResponse:
        """
        Async version of transfer funds.
        
        Args:
            transfer_request: Transfer request details
            use_auth: Whether to use JWT authentication
            
        Returns:
            TransferResponse object with transfer details
        """
        url = f"{self.base_url}/transfer"
        headers = {"Content-Type": "application/json"}
        
        if use_auth:
            if not self._auth_token or self._auth_token.is_expired:
                raise AuthenticationError("Valid authentication token required")
            headers.update(self._auth_token.headers)
        
        payload = {
            "fromAccount": transfer_request.from_account,
            "toAccount": transfer_request.to_account,
            "amount": transfer_request.amount
        }
        
        try:
            logger.info(f"Async transferring {transfer_request.amount} from {transfer_request.from_account} to {transfer_request.to_account}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                response_data = await response.json()
                
                transfer_response = TransferResponse(
                    transaction_id=response_data.get("transactionId", ""),
                    status=response_data.get("status", ""),
                    message=response_data.get("message", ""),
                    from_account=response_data.get("fromAccount", ""),
                    to_account=response_data.get("toAccount", ""),
                    amount=response_data.get("amount", 0.0)
                )
                
                logger.info(f"Async transfer successful: {transfer_response.transaction_id}")
                return transfer_response
                
        except aiohttp.ClientError as e:
            logger.error(f"Async transfer failed: {e}")
            raise TransferError(f"Async transfer failed: {e}")


def main():
    """
    Demonstration of the modern banking client.
    
    This replaces the legacy Python 2.7 implementation with modern best practices.
    """
    print("Modern Banking Client Demo")
    print("=" * 50)
    
    # Example usage with context manager for proper resource cleanup
    with ModernBankingClient() as client:
        try:
            # Validate accounts first
            print("\n1. Validating accounts...")
            from_account = "ACC1000"
            to_account = "ACC1001"
            
            if client.validate_account(from_account):
                print(f"  ✓ {from_account} is valid")
            else:
                print(f"  ✗ {from_account} is invalid")
                return
            
            if client.validate_account(to_account):
                print(f"  ✓ {to_account} is valid")
            else:
                print(f"  ✗ {to_account} is invalid")
                return
            
            # Get account balances
            print("\n2. Checking account balances...")
            try:
                from_balance = client.get_account_balance(from_account)
                print(f"  {from_account} balance: {from_balance}")
            except BankingClientError as e:
                print(f"  Could not get balance for {from_account}: {e}")
            
            # Create and execute transfer
            print("\n3. Executing transfer...")
            transfer = TransferRequest(
                from_account=from_account,
                to_account=to_account,
                amount=100.00
            )
            
            response = client.transfer_funds(transfer)
            print(f"  ✓ Transfer successful!")
            print(f"    Transaction ID: {response.transaction_id}")
            print(f"    Status: {response.status}")
            print(f"    Message: {response.message}")
            print(f"    Amount: ${response.amount}")
            
            # Demo with authentication (if server supports it)
            print("\n4. Testing with authentication...")
            try:
                auth_token = client.authenticate("alice", "password", "transfer")
                print(f"  ✓ Authentication successful (scope: {auth_token.scope})")
                
                # Execute authenticated transfer
                auth_response = client.transfer_funds(transfer, use_auth=True)
                print(f"  ✓ Authenticated transfer successful: {auth_response.transaction_id}")
                
            except AuthenticationError as e:
                print(f"  Authentication not supported or failed: {e}")
            
        except BankingClientError as e:
            print(f"Banking operation failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.exception("Unexpected error in main demo")


async def async_demo():
    """Demonstration of async banking client."""
    print("\nAsync Banking Client Demo")
    print("=" * 50)
    
    async with AsyncBankingClient() as client:
        try:
            # Execute multiple transfers concurrently
            transfers = [
                TransferRequest("ACC1000", "ACC1001", 50.00),
                TransferRequest("ACC1001", "ACC1002", 25.00),
                TransferRequest("ACC1002", "ACC1000", 75.00)
            ]
            
            print("Executing multiple transfers concurrently...")
            tasks = [
                client.transfer_funds_async(transfer)
                for transfer in transfers
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, TransferResponse):
                    print(f"  Transfer {i+1}: ✓ {result.transaction_id}")
                else:
                    print(f"  Transfer {i+1}: ✗ {result}")
                    
        except Exception as e:
            print(f"Async demo failed: {e}")
            logger.exception("Async demo error")


if __name__ == "__main__":
    # Run synchronous demo
    main()
    
    # Run async demo
    try:
        asyncio.run(async_demo())
    except Exception as e:
        print(f"Async demo could not be executed: {e}")
