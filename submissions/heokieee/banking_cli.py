#!/usr/bin/env python3
"""
Modern Banking CLI - Command Line Interface for the Banking Client

This demonstrates modern CLI development practices:
- Uses argparse for robust command line parsing
- Supports multiple output formats (JSON, table)
- Includes comprehensive help and error handling
- Demonstrates clean separation of CLI and business logic
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from banking_client import (
    ModernBankingClient,
    TransferRequest,
    BankingClientError,
    AuthenticationError,
    TransferError,
    ValidationError
)


def format_table(data: dict, title: str = "") -> str:
    """Format data as a simple table."""
    if title:
        output = f"\n{title}\n{'=' * len(title)}\n"
    else:
        output = "\n"
    
    for key, value in data.items():
        output += f"{key:20}: {value}\n"
    
    return output


def format_json(data: dict) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2)


def handle_validate_command(args) -> int:
    """Handle account validation command."""
    try:
        with ModernBankingClient(args.base_url) as client:
            is_valid = client.validate_account(args.account_id)
            
            result = {
                "account_id": args.account_id,
                "valid": is_valid,
                "status": "VALID" if is_valid else "INVALID"
            }
            
            if args.format == "json":
                print(format_json(result))
            else:
                print(format_table(result, f"Account Validation: {args.account_id}"))
            
            return 0 if is_valid else 1
            
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2
    except BankingClientError as e:
        print(f"Banking error: {e}", file=sys.stderr)
        return 3


def handle_transfer_command(args) -> int:
    """Handle money transfer command."""
    try:
        with ModernBankingClient(args.base_url) as client:
            # Validate accounts first if requested
            if args.validate_accounts:
                print("Validating accounts...")
                if not client.validate_account(args.from_account):
                    print(f"Error: Source account {args.from_account} is invalid", file=sys.stderr)
                    return 1
                if not client.validate_account(args.to_account):
                    print(f"Error: Destination account {args.to_account} is invalid", file=sys.stderr)
                    return 1
                print("✓ All accounts validated")
            
            # Authenticate if credentials provided
            auth_token = None
            if args.username and args.password:
                try:
                    auth_token = client.authenticate(args.username, args.password, "transfer")
                    print("✓ Authentication successful")
                except AuthenticationError as e:
                    print(f"Authentication failed: {e}", file=sys.stderr)
                    if not args.ignore_auth_errors:
                        return 4
            
            # Create and execute transfer
            transfer = TransferRequest(
                from_account=args.from_account,
                to_account=args.to_account,
                amount=args.amount
            )
            
            response = client.transfer_funds(transfer, use_auth=auth_token is not None)
            
            result = {
                "transaction_id": response.transaction_id,
                "status": response.status,
                "message": response.message,
                "from_account": response.from_account,
                "to_account": response.to_account,
                "amount": response.amount,
                "authenticated": auth_token is not None
            }
            
            if args.format == "json":
                print(format_json(result))
            else:
                print(format_table(result, "Transfer Result"))
            
            return 0 if response.status == "SUCCESS" else 5
            
    except TransferError as e:
        print(f"Transfer error: {e}", file=sys.stderr)
        return 6
    except ValueError as e:
        print(f"Invalid input: {e}", file=sys.stderr)
        return 7
    except BankingClientError as e:
        print(f"Banking error: {e}", file=sys.stderr)
        return 8


def handle_balance_command(args) -> int:
    """Handle balance inquiry command."""
    try:
        with ModernBankingClient(args.base_url) as client:
            # Authenticate if credentials provided
            use_auth = False
            if args.username and args.password:
                try:
                    client.authenticate(args.username, args.password, "enquiry")
                    use_auth = True
                    print("✓ Authentication successful")
                except AuthenticationError as e:
                    print(f"Authentication failed: {e}", file=sys.stderr)
                    if not args.ignore_auth_errors:
                        return 4
            
            balance = client.get_account_balance(args.account_id, use_auth=use_auth)
            
            if args.format == "json":
                print(format_json(balance))
            else:
                print(format_table(balance, f"Account Balance: {args.account_id}"))
            
            return 0
            
    except BankingClientError as e:
        print(f"Balance inquiry error: {e}", file=sys.stderr)
        return 9


def handle_accounts_command(args) -> int:
    """Handle list accounts command."""
    try:
        with ModernBankingClient(args.base_url) as client:
            # Authenticate if credentials provided
            use_auth = False
            if args.username and args.password:
                try:
                    client.authenticate(args.username, args.password, "enquiry")
                    use_auth = True
                    print("✓ Authentication successful")
                except AuthenticationError as e:
                    print(f"Authentication failed: {e}", file=sys.stderr)
                    if not args.ignore_auth_errors:
                        return 4
            
            accounts = client.get_accounts(use_auth=use_auth)
            
            if args.format == "json":
                print(format_json({"accounts": accounts}))
            else:
                print(f"\nAccounts List ({len(accounts)} accounts)")
                print("=" * 40)
                for i, account in enumerate(accounts, 1):
                    print(f"{i}. {account}")
            
            return 0
            
    except BankingClientError as e:
        print(f"Accounts list error: {e}", file=sys.stderr)
        return 10


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Modern Banking CLI - Interact with the Core Banking API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate an account
  %(prog)s validate ACC1000
  
  # Transfer money (basic)
  %(prog)s transfer ACC1000 ACC1001 100.00
  
  # Transfer money with authentication
  %(prog)s transfer ACC1000 ACC1001 100.00 --username alice --password secret
  
  # Transfer with validation and JSON output
  %(prog)s transfer ACC1000 ACC1001 100.00 --validate --format json
  
  # Check account balance
  %(prog)s balance ACC1000
  
  # List all accounts
  %(prog)s accounts

Exit codes:
  0  - Success
  1  - Invalid account or failed validation
  2  - Validation error
  3  - General banking error
  4  - Authentication failed
  5  - Transfer failed
  6  - Transfer error
  7  - Invalid input
  8  - Banking client error
  9  - Balance inquiry error
  10 - Accounts list error
        """
    )
    
    # Global options
    parser.add_argument(
        "--base-url",
        default="http://localhost:8123",
        help="Base URL for the banking API (default: http://localhost:8123)"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--username",
        help="Username for authentication (optional)"
    )
    parser.add_argument(
        "--password",
        help="Password for authentication (optional)"
    )
    parser.add_argument(
        "--ignore-auth-errors",
        action="store_true",
        help="Continue operation even if authentication fails"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an account"
    )
    validate_parser.add_argument(
        "account_id",
        help="Account ID to validate (e.g., ACC1000)"
    )
    
    # Transfer command
    transfer_parser = subparsers.add_parser(
        "transfer",
        help="Transfer money between accounts"
    )
    transfer_parser.add_argument(
        "from_account",
        help="Source account ID (e.g., ACC1000)"
    )
    transfer_parser.add_argument(
        "to_account",
        help="Destination account ID (e.g., ACC1001)"
    )
    transfer_parser.add_argument(
        "amount",
        type=float,
        help="Amount to transfer (e.g., 100.00)"
    )
    transfer_parser.add_argument(
        "--validate",
        dest="validate_accounts",
        action="store_true",
        help="Validate accounts before transfer"
    )
    
    # Balance command
    balance_parser = subparsers.add_parser(
        "balance",
        help="Check account balance"
    )
    balance_parser.add_argument(
        "account_id",
        help="Account ID to check (e.g., ACC1000)"
    )
    
    # Accounts command
    accounts_parser = subparsers.add_parser(
        "accounts",
        help="List all accounts"
    )
    
    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    try:
        if args.command == "validate":
            return handle_validate_command(args)
        elif args.command == "transfer":
            return handle_transfer_command(args)
        elif args.command == "balance":
            return handle_balance_command(args)
        elif args.command == "accounts":
            return handle_accounts_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 255


if __name__ == "__main__":
    sys.exit(main())
