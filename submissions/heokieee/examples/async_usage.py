#!/usr/bin/env python3
"""
Async usage examples for the Modern Banking Client.

This file demonstrates async/await patterns and concurrent operations.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from banking_client import (
    AsyncBankingClient,
    TransferRequest,
    BankingClientError,
    TransferError
)


async def example_async_transfer():
    """Demonstrate basic async transfer."""
    print("=== Async Transfer Example ===")
    
    try:
        async with AsyncBankingClient() as client:
            transfer = TransferRequest("ACC1000", "ACC1001", 75.00)
            
            start_time = time.time()
            response = await client.transfer_funds_async(transfer)
            end_time = time.time()
            
            print(f"✓ Async transfer completed in {end_time - start_time:.2f}s")
            print(f"  Transaction ID: {response.transaction_id}")
            print(f"  Status: {response.status}")
            
    except TransferError as e:
        print(f"Async transfer failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def example_concurrent_transfers():
    """Demonstrate concurrent transfers using async."""
    print("\n=== Concurrent Transfers Example ===")
    
    try:
        async with AsyncBankingClient() as client:
            # Create multiple transfer requests
            transfers = [
                TransferRequest("ACC1000", "ACC1001", 25.00),
                TransferRequest("ACC1001", "ACC1002", 35.00),
                TransferRequest("ACC1002", "ACC1000", 45.00),
                TransferRequest("ACC1000", "ACC1003", 55.00),
                TransferRequest("ACC1003", "ACC1001", 65.00)
            ]
            
            print(f"Executing {len(transfers)} transfers concurrently...")
            
            start_time = time.time()
            
            # Execute all transfers concurrently
            tasks = [
                client.transfer_funds_async(transfer) 
                for transfer in transfers
            ]
            
            # Wait for all transfers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            # Process results
            successful = 0
            failed = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"  Transfer {i+1}: ✗ Failed - {result}")
                    failed += 1
                else:
                    print(f"  Transfer {i+1}: ✓ {result.transaction_id}")
                    successful += 1
            
            print(f"\nConcurrent execution completed in {end_time - start_time:.2f}s")
            print(f"Success: {successful}, Failed: {failed}")
            
    except Exception as e:
        print(f"Concurrent transfers error: {e}")


async def example_sequential_vs_concurrent():
    """Compare sequential vs concurrent execution."""
    print("\n=== Sequential vs Concurrent Comparison ===")
    
    # Create test transfers
    transfers = [
        TransferRequest("ACC1000", "ACC1001", 10.00),
        TransferRequest("ACC1001", "ACC1002", 20.00),
        TransferRequest("ACC1002", "ACC1000", 30.00)
    ]
    
    async with AsyncBankingClient() as client:
        # Sequential execution
        print("Sequential execution:")
        start_time = time.time()
        
        for i, transfer in enumerate(transfers):
            try:
                result = await client.transfer_funds_async(transfer)
                print(f"  Transfer {i+1}: ✓ {result.transaction_id}")
            except Exception as e:
                print(f"  Transfer {i+1}: ✗ {e}")
        
        sequential_time = time.time() - start_time
        print(f"Sequential time: {sequential_time:.2f}s")
        
        # Concurrent execution
        print("\nConcurrent execution:")
        start_time = time.time()
        
        # Recreate transfers for concurrent test
        concurrent_transfers = [
            TransferRequest("ACC1003", "ACC1004", 10.00),
            TransferRequest("ACC1004", "ACC1005", 20.00),
            TransferRequest("ACC1005", "ACC1003", 30.00)
        ]
        
        tasks = [
            client.transfer_funds_async(transfer) 
            for transfer in concurrent_transfers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Transfer {i+1}: ✗ {result}")
            else:
                print(f"  Transfer {i+1}: ✓ {result.transaction_id}")
        
        concurrent_time = time.time() - start_time
        print(f"Concurrent time: {concurrent_time:.2f}s")
        
        # Show improvement
        if sequential_time > 0 and concurrent_time > 0:
            improvement = ((sequential_time - concurrent_time) / sequential_time) * 100
            print(f"\nPerformance improvement: {improvement:.1f}% faster")


async def example_async_error_handling():
    """Demonstrate error handling in async context."""
    print("\n=== Async Error Handling Example ===")
    
    try:
        async with AsyncBankingClient() as client:
            # Create some transfers (including invalid ones)
            transfers = [
                TransferRequest("ACC1000", "ACC1001", 50.00),  # Valid
                TransferRequest("INVALID", "ACC1001", 25.00),  # Invalid from account
                TransferRequest("ACC1000", "INVALID", 25.00),  # Invalid to account
                TransferRequest("ACC1001", "ACC1002", 75.00),  # Valid
            ]
            
            print("Testing error handling with mixed valid/invalid transfers...")
            
            # Execute with error handling
            tasks = []
            for transfer in transfers:
                task = client.transfer_funds_async(transfer)
                tasks.append(task)
            
            # Use return_exceptions=True to get both results and exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                transfer = transfers[i]
                if isinstance(result, Exception):
                    print(f"  Transfer {i+1} ({transfer.from_account}→{transfer.to_account}): ✗ {type(result).__name__}")
                else:
                    print(f"  Transfer {i+1} ({transfer.from_account}→{transfer.to_account}): ✓ {result.transaction_id}")
            
    except Exception as e:
        print(f"Async error handling example failed: {e}")


async def example_timeout_handling():
    """Demonstrate timeout handling in async operations."""
    print("\n=== Timeout Handling Example ===")
    
    try:
        # Create client with short timeout for demonstration
        async with AsyncBankingClient(timeout=1) as client:
            transfer = TransferRequest("ACC1000", "ACC1001", 100.00)
            
            try:
                # This might timeout if server is slow
                result = await asyncio.wait_for(
                    client.transfer_funds_async(transfer), 
                    timeout=2.0
                )
                print(f"✓ Transfer completed within timeout: {result.transaction_id}")
                
            except asyncio.TimeoutError:
                print("✗ Transfer timed out")
            except Exception as e:
                print(f"✗ Transfer failed: {e}")
                
    except Exception as e:
        print(f"Timeout handling example failed: {e}")


async def main():
    """Run all async examples."""
    print("Modern Banking Client - Async Usage Examples")
    print("=" * 50)
    print("Note: Ensure the banking server is running on localhost:8123")
    print()
    
    # Run async examples
    await example_async_transfer()
    await example_concurrent_transfers()
    await example_sequential_vs_concurrent()
    await example_async_error_handling()
    await example_timeout_handling()
    
    print("\n" + "=" * 50)
    print("All async examples completed!")


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Examples failed: {e}")
