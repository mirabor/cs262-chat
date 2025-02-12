"""Benchmark tests for comparing JSON and Custom protocol performance."""

import time
import json
import pickle
import statistics
import random
import string
from typing import Dict, List, Any
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from protocol.protocol_factory import JsonProtocol
from protocol.custom_protocol import CustomProtocol

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_test_message(size: int) -> Dict[str, Any]:
    """Generate a test message of approximately specified size in bytes."""
    return {
        "action": "send_message",
        "chat_id": str(random.randint(1, 1000)),
        "sender": generate_random_string(10),
        "content": generate_random_string(size - 100),  # Approximate size adjustment
        "timestamp": "2025-02-12T04:45:08-05:00",
        "status": "unread"
    }

def measure_serialization(protocol, message: Dict[str, Any], iterations: int = 1000) -> List[float]:
    """Measure serialization time for a message."""
    times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        protocol.serialize(message)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    return times

def measure_deserialization(protocol, serialized_data: bytes, iterations: int = 1000) -> List[float]:
    """Measure deserialization time for a message."""
    times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        protocol.deserialize(serialized_data)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    return times

def format_stats(times: List[float]) -> Dict[str, float]:
    """Calculate statistics for timing data."""
    return {
        "mean": statistics.mean(times) * 1000,  # Convert to milliseconds
        "median": statistics.median(times) * 1000,
        "stdev": statistics.stdev(times) * 1000,
        "min": min(times) * 1000,
        "max": max(times) * 1000
    }

def run_benchmark(message_sizes: List[int], iterations: int = 1000):
    """Run benchmark comparing JSON and Custom protocols."""
    json_protocol = JsonProtocol()
    custom_protocol = CustomProtocol()
    
    results = []
    
    for size in message_sizes:
        print(f"\nBenchmarking with message size: {size} bytes")
        message = generate_test_message(size)
        
        # Measure JSON protocol
        json_ser_times = measure_serialization(json_protocol, message, iterations)
        json_serialized = json_protocol.serialize(message)
        json_deser_times = measure_deserialization(json_protocol, json_serialized, iterations)
        
        # Measure Custom protocol
        custom_ser_times = measure_serialization(custom_protocol, message, iterations)
        custom_serialized = custom_protocol.serialize(message)
        custom_deser_times = measure_deserialization(custom_protocol, custom_serialized, iterations)
        
        # Calculate size comparison
        json_size = len(json_serialized)
        custom_size = len(custom_serialized)
        
        result = {
            "message_size": size,
            "json": {
                "serialization": format_stats(json_ser_times),
                "deserialization": format_stats(json_deser_times),
                "serialized_size": json_size
            },
            "custom": {
                "serialization": format_stats(custom_ser_times),
                "deserialization": format_stats(custom_deser_times),
                "serialized_size": custom_size
            }
        }
        results.append(result)
        
        # Print results for this message size
        print(f"\nResults for {size} bytes message:")
        print("\nJSON Protocol:")
        print(f"Serialized size: {json_size} bytes")
        print("Serialization (ms):", {k: f"{v:.3f}" for k, v in result["json"]["serialization"].items()})
        print("Deserialization (ms):", {k: f"{v:.3f}" for k, v in result["json"]["deserialization"].items()})
        
        print("\nCustom Protocol:")
        print(f"Serialized size: {custom_size} bytes")
        print("Serialization (ms):", {k: f"{v:.3f}" for k, v in result["custom"]["serialization"].items()})
        print("Deserialization (ms):", {k: f"{v:.3f}" for k, v in result["custom"]["deserialization"].items()})
        
        # Calculate and print comparisons
        size_diff_percent = ((custom_size - json_size) / json_size) * 100
        ser_speedup = result["json"]["serialization"]["mean"] / result["custom"]["serialization"]["mean"]
        deser_speedup = result["json"]["deserialization"]["mean"] / result["custom"]["deserialization"]["mean"]
        
        print(f"\nComparisons:")
        print(f"Size difference: {size_diff_percent:.1f}% ({'-' if size_diff_percent < 0 else '+'})")
        print(f"Serialization speedup: {ser_speedup:.2f}x")
        print(f"Deserialization speedup: {deser_speedup:.2f}x")
    
    return results

if __name__ == "__main__":
    # Test with various message sizes
    message_sizes = [100, 1000, 10000, 100000]
    iterations = 1000
    
    print(f"Running benchmarks with {iterations} iterations per test...")
    results = run_benchmark(message_sizes, iterations)
