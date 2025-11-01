"""
Comprehensive unit tests for the Modern Banking Client.

Demonstrates testing best practices:
- Mock external dependencies
- Test both success and failure scenarios
- Async testing
- Parametrized tests
- Proper test structure and organization
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import requests
import aiohttp

from banking_client import (
    ModernBankingClient,
    AsyncBankingClient,
    TransferRequest,
    TransferResponse,
    AuthToken,
    BankingClientError,
    AuthenticationError,
    TransferError,
    ValidationError
)


class TestTransferRequest:
    """Test TransferRequest data class validation."""
    
    def test_valid_transfer_request(self):
        """Test creating a valid transfer request."""
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        assert transfer.from_account == "ACC1000"
        assert transfer.to_account == "ACC1001"
        assert transfer.amount == 100.0
    
    def test_negative_amount_raises_error(self):
        """Test that negative amounts raise ValueError."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            TransferRequest("ACC1000", "ACC1001", -100.0)
    
    def test_zero_amount_raises_error(self):
        """Test that zero amount raises ValueError."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            TransferRequest("ACC1000", "ACC1001", 0.0)
    
    def test_empty_accounts_raise_error(self):
        """Test that empty account numbers raise ValueError."""
        with pytest.raises(ValueError, match="Account numbers cannot be empty"):
            TransferRequest("", "ACC1001", 100.0)
        
        with pytest.raises(ValueError, match="Account numbers cannot be empty"):
            TransferRequest("ACC1000", "", 100.0)
    
    def test_same_accounts_raise_error(self):
        """Test that same source and destination accounts raise ValueError."""
        with pytest.raises(ValueError, match="Source and destination accounts must be different"):
            TransferRequest("ACC1000", "ACC1000", 100.0)


class TestAuthToken:
    """Test AuthToken data class functionality."""
    
    def test_auth_token_creation(self):
        """Test creating an auth token."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = AuthToken("test-token", expires_at, "transfer")
        
        assert token.token == "test-token"
        assert token.expires_at == expires_at
        assert token.scope == "transfer"
    
    def test_token_not_expired(self):
        """Test that future expiration returns not expired."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = AuthToken("test-token", expires_at, "transfer")
        assert not token.is_expired
    
    def test_token_expired(self):
        """Test that past expiration returns expired."""
        expires_at = datetime.now() - timedelta(hours=1)
        token = AuthToken("test-token", expires_at, "transfer")
        assert token.is_expired
    
    def test_headers_property(self):
        """Test that headers property returns correct format."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = AuthToken("test-token", expires_at, "transfer")
        expected_headers = {"Authorization": "Bearer test-token"}
        assert token.headers == expected_headers


class TestModernBankingClient:
    """Test the modern banking client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a banking client for testing."""
        return ModernBankingClient("http://localhost:8123")
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        return response
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.base_url == "http://localhost:8123"
        assert client.timeout == 30
        assert client._auth_token is None
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with ModernBankingClient() as client:
            assert isinstance(client, ModernBankingClient)
            assert client.session is not None
    
    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post, client):
        """Test successful authentication."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"token": "test-jwt-token"}
        mock_post.return_value = mock_response
        
        # Test authentication
        token = client.authenticate("alice", "password", "transfer")
        
        # Verify results
        assert isinstance(token, AuthToken)
        assert token.token == "test-jwt-token"
        assert token.scope == "transfer"
        assert not token.is_expired
        assert client._auth_token == token
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json'] == {"username": "alice", "password": "password"}
        assert call_args[1]['params'] == {"claim": "transfer"}
    
    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post, client):
        """Test authentication failure."""
        # Setup mock to raise exception
        mock_post.side_effect = requests.RequestException("Auth failed")
        
        # Test authentication failure
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            client.authenticate("invalid", "credentials")
    
    @patch('requests.Session.post')
    def test_transfer_funds_success(self, mock_post, client):
        """Test successful fund transfer."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "transactionId": "txn-123",
            "status": "SUCCESS",
            "message": "Transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0
        }
        mock_post.return_value = mock_response
        
        # Create transfer request
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        
        # Execute transfer
        response = client.transfer_funds(transfer)
        
        # Verify results
        assert isinstance(response, TransferResponse)
        assert response.transaction_id == "txn-123"
        assert response.status == "SUCCESS"
        assert response.message == "Transfer completed"
        assert response.from_account == "ACC1000"
        assert response.to_account == "ACC1001"
        assert response.amount == 100.0
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        expected_payload = {
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0
        }
        assert call_args[1]['json'] == expected_payload
    
    @patch('requests.Session.post')
    def test_transfer_funds_with_auth(self, mock_post, client):
        """Test fund transfer with authentication."""
        # Setup auth token
        expires_at = datetime.now() + timedelta(hours=1)
        client._auth_token = AuthToken("test-token", expires_at, "transfer")
        
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "transactionId": "txn-456",
            "status": "SUCCESS",
            "message": "Authenticated transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0
        }
        mock_post.return_value = mock_response
        
        # Create transfer request
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        
        # Execute authenticated transfer
        response = client.transfer_funds(transfer, use_auth=True)
        
        # Verify auth header was included
        call_args = mock_post.call_args
        assert "Authorization" in call_args[1]['headers']
        assert call_args[1]['headers']["Authorization"] == "Bearer test-token"
    
    def test_transfer_funds_without_auth_token(self, client):
        """Test transfer with auth required but no token."""
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        
        with pytest.raises(AuthenticationError, match="Valid authentication token required"):
            client.transfer_funds(transfer, use_auth=True)
    
    def test_transfer_funds_with_expired_token(self, client):
        """Test transfer with expired auth token."""
        # Setup expired token
        expires_at = datetime.now() - timedelta(hours=1)
        client._auth_token = AuthToken("expired-token", expires_at, "transfer")
        
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        
        with pytest.raises(AuthenticationError, match="Valid authentication token required"):
            client.transfer_funds(transfer, use_auth=True)
    
    @patch('requests.Session.post')
    def test_transfer_funds_api_error(self, mock_post, client):
        """Test transfer failure due to API error."""
        # Setup mock to return error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        mock_response.json.return_value = {"error": "Invalid account"}
        mock_post.return_value = mock_response
        
        transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
        
        with pytest.raises(TransferError, match="Transfer failed"):
            client.transfer_funds(transfer)
    
    @patch('requests.Session.get')
    def test_validate_account_success(self, mock_get, client):
        """Test successful account validation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"valid": True}
        mock_get.return_value = mock_response
        
        # Test validation
        result = client.validate_account("ACC1000")
        
        # Verify results
        assert result is True
        mock_get.assert_called_once_with(
            "http://localhost:8123/accounts/validate/ACC1000",
            timeout=30
        )
    
    @patch('requests.Session.get')
    def test_validate_account_invalid(self, mock_get, client):
        """Test validation of invalid account."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"valid": False}
        mock_get.return_value = mock_response
        
        # Test validation
        result = client.validate_account("ACC2000")
        
        # Verify results
        assert result is False
    
    @patch('requests.Session.get')
    def test_validate_account_error(self, mock_get, client):
        """Test account validation error."""
        # Setup mock to raise exception
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Test validation failure
        with pytest.raises(ValidationError, match="Account validation failed"):
            client.validate_account("ACC1000")
    
    @patch('requests.Session.get')
    def test_get_accounts(self, mock_get, client):
        """Test getting accounts list."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = [
            {"id": "ACC1000", "balance": 1000.0},
            {"id": "ACC1001", "balance": 500.0}
        ]
        mock_get.return_value = mock_response
        
        # Test getting accounts
        accounts = client.get_accounts()
        
        # Verify results
        assert len(accounts) == 2
        assert accounts[0]["id"] == "ACC1000"
        assert accounts[1]["id"] == "ACC1001"
        
        mock_get.assert_called_once_with(
            "http://localhost:8123/accounts",
            headers={},
            timeout=30
        )
    
    @patch('requests.Session.get')
    def test_get_account_balance(self, mock_get, client):
        """Test getting account balance."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "accountId": "ACC1000",
            "balance": 1000.0,
            "currency": "USD"
        }
        mock_get.return_value = mock_response
        
        # Test getting balance
        balance = client.get_account_balance("ACC1000")
        
        # Verify results
        assert balance["accountId"] == "ACC1000"
        assert balance["balance"] == 1000.0
        assert balance["currency"] == "USD"
        
        mock_get.assert_called_once_with(
            "http://localhost:8123/accounts/balance/ACC1000",
            headers={},
            timeout=30
        )


class TestAsyncBankingClient:
    """Test the async banking client functionality."""
    
    @pytest.fixture
    def async_client(self):
        """Create an async banking client for testing."""
        return AsyncBankingClient("http://localhost:8123")
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, async_client):
        """Test async context manager functionality."""
        async with async_client as client:
            assert isinstance(client, AsyncBankingClient)
            assert hasattr(client, 'session')
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_async_transfer_funds_success(self, mock_post, async_client):
        """Test successful async fund transfer."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={
            "transactionId": "async-txn-123",
            "status": "SUCCESS",
            "message": "Async transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0
        })
        
        # Setup context manager for the response
        mock_post.return_value.__aenter__ = Mock(return_value=mock_response)
        mock_post.return_value.__aexit__ = Mock(return_value=None)
        
        async with async_client as client:
            # Create transfer request
            transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
            
            # Execute async transfer
            response = await client.transfer_funds_async(transfer)
            
            # Verify results
            assert isinstance(response, TransferResponse)
            assert response.transaction_id == "async-txn-123"
            assert response.status == "SUCCESS"
            assert response.message == "Async transfer completed"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_async_transfer_funds_error(self, mock_post, async_client):
        """Test async transfer failure."""
        # Setup mock to raise exception
        mock_post.side_effect = aiohttp.ClientError("Async transfer failed")
        
        async with async_client as client:
            transfer = TransferRequest("ACC1000", "ACC1001", 100.0)
            
            with pytest.raises(TransferError, match="Async transfer failed"):
                await client.transfer_funds_async(transfer)


@pytest.mark.parametrize("account_id,expected", [
    ("ACC1000", True),
    ("ACC1001", True),
    ("ACC2000", False),
    ("ACC9999", False),
])
@patch('requests.Session.get')
def test_account_validation_parametrized(mock_get, account_id, expected):
    """Parametrized test for account validation."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {"valid": expected}
    mock_get.return_value = mock_response
    
    client = ModernBankingClient()
    result = client.validate_account(account_id)
    
    assert result == expected


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require the actual server to be running."""
    
    @pytest.fixture
    def live_client(self):
        """Create a client for integration testing."""
        return ModernBankingClient("http://localhost:8123")
    
    @pytest.mark.skip(reason="Requires live server")
    def test_live_account_validation(self, live_client):
        """Test account validation against live server."""
        # This test would run against the actual server
        with live_client as client:
            assert client.validate_account("ACC1000") is True
            assert client.validate_account("ACC2000") is False
    
    @pytest.mark.skip(reason="Requires live server")
    def test_live_transfer(self, live_client):
        """Test transfer against live server."""
        # This test would run against the actual server
        with live_client as client:
            transfer = TransferRequest("ACC1000", "ACC1001", 10.0)
            response = client.transfer_funds(transfer)
            assert response.status == "SUCCESS"
            assert response.transaction_id is not None


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main(["-v", "--cov=banking_client", "--cov-report=html", __file__])
