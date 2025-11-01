#!/usr/bin/env python3
"""
Basic usage examples for the Modern Banking Client.

This file demonstrates the core functionality and basic usage patterns.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from banking_client import (
    ModernBankingClient,
    TransferRequest,
    BankingClientError,
    AuthenticationError,
    TransferError
)


def example_basic_transfer():
    """Demonstrate basic transfer functionality."""
    print("=== Basic Transfer Example ===")
    
    try:
        # Use context manager for proper resource cleanup
        with ModernBankingClient() as client:
            # Create transfer request with validation
            transfer = TransferRequest(
                from_account="ACC1000",
                to_account="ACC1001", 
                amount=100.00
            )
            
            # Execute transfer
            response = client.transfer_funds(transfer)
            
            # Display results
            print(f"Transfer successful!")
            print(f"  Transaction ID: {response.transaction_id}")
            print(f"  Status: {response.status}")
            print(f"  Message: {response.message}")
            print(f"  Amount: ${response.amount}")
            
    except TransferError as e:
        print(f"Transfer failed: {e}")
    except BankingClientError as e:
        print(f"Banking error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def example_account_validation():
    """Demonstrate account validation."""
    print("\n=== Account Validation Example ===")
    
    accounts_to_test = ["ACC1000", "ACC1001", "ACC2000", "ACC9999"]
    
    try:
        with ModernBankingClient() as client:
            for account in accounts_to_test:
                is_valid = client.validate_account(account)
                status = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"  {account}: {status}")
                
    except BankingClientError as e:
        print(f"Validation error: {e}")


def example_with_authentication():
    """Demonstrate authentication and authenticated operations."""
    print("\n=== Authentication Example ===")
    
    try:
        with ModernBankingClient() as client:
            # Authenticate
            print("Authenticating...")
            try:
                token = client.authenticate("alice", "password", "transfer")
                print(f"✓ Authentication successful (scope: {token.scope})")
                print(f"  Token expires at: {token.expires_at}")
                
                # Execute authenticated transfer
                transfer = TransferRequest("ACC1000", "ACC1001", 50.00)
                response = client.transfer_funds(transfer, use_auth=True)
                
                print(f"✓ Authenticated transfer successful!")
                print(f"  Transaction ID: {response.transaction_id}")
                
            except AuthenticationError as e:
                print(f"Authentication failed: {e}")
                print("Proceeding with unauthenticated transfer...")
                
                # Fall back to unauthenticated transfer
                transfer = TransferRequest("ACC1000", "ACC1001", 50.00)
                response = client.transfer_funds(transfer, use_auth=False)
                print(f"✓ Unauthenticated transfer successful: {response.transaction_id}")
                
    except BankingClientError as e:
        print(f"Banking error: {e}")


def example_account_operations():
    """Demonstrate various account operations."""
    print("\n=== Account Operations Example ===")
    
    try:
        with ModernBankingClient() as client:
            # Get all accounts
            print("Fetching all accounts...")
            try:
                accounts = client.get_accounts()
                print(f"✓ Found {len(accounts)} accounts:")
                for i, account in enumerate(accounts[:3], 1):  # Show first 3
                    print(f"  {i}. {account}")
                if len(accounts) > 3:
                    print(f"  ... and {len(accounts) - 3} more")
                    
            except BankingClientError as e:
                print(f"Could not fetch accounts: {e}")
            
            # Get account balance
            print("\nChecking account balance...")
            try:
                balance = client.get_account_balance("ACC1000")
                print(f"✓ Account ACC1000 balance: {balance}")
                
            except BankingClientError as e:
                print(f"Could not get balance: {e}")
                
    except BankingClientError as e:
        print(f"Account operations error: {e}")


def example_error_handling():
    """Demonstrate comprehensive error handling."""
    print("\n=== Error Handling Example ===")
    
    try:
        with ModernBankingClient() as client:
            # Test invalid transfer (same account)
            print("Testing invalid transfer (same accounts)...")
            try:
                invalid_transfer = TransferRequest("ACC1000", "ACC1000", 100.00)
                print("This should not execute due to validation")
            except ValueError as e:
                print(f"✓ Input validation caught error: {e}")
            
            # Test transfer with invalid account
            print("\nTesting transfer with invalid account...")
            try:
                invalid_transfer = TransferRequest("INVALID", "ACC1001", 100.00)
                response = client.transfer_funds(invalid_transfer)
                print(f"Unexpected success: {response.transaction_id}")
            except TransferError as e:
                print(f"✓ Transfer error caught: {e}")
            
            # Test negative amount
            print("\nTesting negative amount...")
            try:
                negative_transfer = TransferRequest("ACC1000", "ACC1001", -100.00)
                print("This should not execute due to validation")
            except ValueError as e:
                print(f"✓ Negative amount validation: {e}")
                
    except Exception as e:
        print(f"Error handling example failed: {e}")


def main():
    """Run all examples."""
    print("Modern Banking Client - Basic Usage Examples")
    print("=" * 50)
    print("Note: Ensure the banking server is running on localhost:8123")
    print()
    
    # Run examples
    example_basic_transfer()
    example_account_validation() 
    example_with_authentication()
    example_account_operations()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("Check the logs in 'banking_client.log' for detailed information.")


if __name__ == "__main__":
    main()
