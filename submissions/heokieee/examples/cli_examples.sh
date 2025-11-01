#!/bin/bash

# CLI Examples for Modern Banking Client
# Demonstrates the modern CLI interface capabilities

echo "Modern Banking CLI - Usage Examples"
echo "=================================="
echo "Note: Ensure the banking server is running on localhost:8123"
echo ""

# Make CLI executable
chmod +x ../banking_cli.py

echo "1. Account Validation Examples"
echo "-----------------------------"
echo "Validating valid accounts..."
../banking_cli.py validate ACC1000
../banking_cli.py validate ACC1001

echo ""
echo "Validating invalid accounts..."
../banking_cli.py validate ACC2000
../banking_cli.py validate ACC9999

echo ""
echo "JSON output format:"
../banking_cli.py validate ACC1000 --format json

echo ""
echo "2. Basic Transfer Examples"
echo "-------------------------"
echo "Basic transfer without authentication:"
../banking_cli.py transfer ACC1000 ACC1001 100.00

echo ""
echo "Transfer with account validation:"
../banking_cli.py transfer ACC1000 ACC1001 75.00 --validate

echo ""
echo "Transfer with JSON output:"
../banking_cli.py transfer ACC1000 ACC1001 50.00 --format json

echo ""
echo "3. Authenticated Transfer Examples"
echo "---------------------------------"
echo "Transfer with authentication (may fail if auth not supported):"
../banking_cli.py transfer ACC1000 ACC1001 25.00 --username alice --password secret

echo ""
echo "Transfer with authentication and validation:"
../banking_cli.py transfer ACC1000 ACC1001 125.00 --username alice --password secret --validate

echo ""
echo "Transfer ignoring auth errors:"
../banking_cli.py transfer ACC1000 ACC1001 30.00 --username invalid --password invalid --ignore-auth-errors

echo ""
echo "4. Account Information Examples"
echo "------------------------------"
echo "List all accounts:"
../banking_cli.py accounts

echo ""
echo "List accounts with JSON output:"
../banking_cli.py accounts --format json

echo ""
echo "Check account balance:"
../banking_cli.py balance ACC1000

echo ""
echo "Check balance with authentication:"
../banking_cli.py balance ACC1000 --username alice --password secret

echo ""
echo "5. Error Handling Examples"
echo "--------------------------"
echo "Invalid transfer (negative amount):"
../banking_cli.py transfer ACC1000 ACC1001 -50.00

echo ""
echo "Invalid transfer (same accounts):"
../banking_cli.py transfer ACC1000 ACC1000 50.00

echo ""
echo "Transfer to invalid account:"
../banking_cli.py transfer ACC1000 INVALID 50.00

echo ""
echo "6. Help and Usage Examples"
echo "--------------------------"
echo "General help:"
../banking_cli.py --help

echo ""
echo "Transfer command help:"
../banking_cli.py transfer --help

echo ""
echo "7. Advanced Examples"
echo "-------------------"
echo "Custom server URL:"
../banking_cli.py transfer ACC1000 ACC1001 40.00 --base-url http://localhost:8080

echo ""
echo "Multiple operations in sequence:"
echo "Validate → Transfer → Check Balance"
../banking_cli.py validate ACC1000 && \
../banking_cli.py transfer ACC1000 ACC1001 60.00 && \
../banking_cli.py balance ACC1000

echo ""
echo "8. Scripting Examples"
echo "--------------------"
echo "Check exit codes:"

echo "Valid account (should return 0):"
../banking_cli.py validate ACC1000
echo "Exit code: $?"

echo ""
echo "Invalid account (should return 1):"
../banking_cli.py validate ACC2000
echo "Exit code: $?"

echo ""
echo "Successful transfer (should return 0):"
../banking_cli.py transfer ACC1000 ACC1001 15.00
echo "Exit code: $?"

echo ""
echo "=================================="
echo "All CLI examples completed!"
echo ""
echo "Exit Codes Reference:"
echo "  0  - Success"
echo "  1  - Invalid account or failed validation"
echo "  2  - Validation error"
echo "  3  - General banking error"
echo "  4  - Authentication failed"
echo "  5  - Transfer failed"
echo "  6  - Transfer error"
echo "  7  - Invalid input"
echo "  8  - Banking client error"
echo "  9  - Balance inquiry error"
echo "  10 - Accounts list error"
