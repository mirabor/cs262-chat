"""Performance tests comparing JSON and Custom protocols."""

import time
import statistics
from typing import Dict, List, Tuple
from memory_profiler import profile
import matplotlib.pyplot as plt

from src.protocol.protocol_factory import JsonProtocol, CustomProtocol

class ProtocolBenchmark:
    """Benchmark JSON vs Custom protocol performance."""

    def __init__(self):
        self.json_protocol = JsonProtocol()
        self.custom_protocol = CustomProtocol()

        # Test messages of increasing complexity
        self.test_messages = [
            # Simple message
            {
                "type": "simple_message",
                "content": "Hello, world!"
            },

            # Typical chat message
            {
                "type": "typical_chat_message",
                "id": "msg_123",
                "timestamp": 1644582794.123,
                "sender": "user1",
                "recipient": "user2",
                "content": "Hey, how are you?",
                "is_read": False,
            },

            # Complex message with arrays
            {
                "type": "complex_message",
                "id": "msg_456",
                "timestamp": 1644582794.123,
                "sender": "user1",
                "recipients": ["user2", "user3", "user4"],
                "content": "Meeting at 3pm",
                "attachments": [
                    {"type": "image", "url": "http://example.com/image1.jpg", "size": 1024576},
                    {"type": "document", "url": "http://example.com/doc.pdf", "size": 2048576}
                ],
                "reactions": [
                    {"user": "user2", "emoji": "👍", "timestamp": 1644582795.123},
                    {"user": "user3", "emoji": "❤️", "timestamp": 1644582796.123}
                ],
                "metadata": {
                    "client": "desktop",
                    "version": "2.0.0",
                    "device": {
                        "os": "macOS",
                        "version": "15.0",
                        "model": "MacBook Air"
                    }
                }
            },

            # Large message with repeated data
            {
                "type": "large_message",
                "channel": "general",
                "messages": [
                    {
                        "id": f"msg_{i}",
                        "sender": f"user{i % 10}",
                        "content": f"Message {i}",
                        "timestamp": 1644582794.0 + i
                    } for i in range(100)
                ],
                "metadata": {
                    "total_messages": 100,
                    "start_time": 1644582794.0,
                    "end_time": 1644582894.0
                }
            }
        ]

    def measure_size(self, data: bytes) -> int:
        """Measure size of serialized data in bytes."""
        return len(data)

    def measure_time(self, func, *args, iterations: int = 1000) -> float:
        """Measure average execution time of a function."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args)
            end = time.perf_counter()
            times.append(end - start)
        return statistics.mean(times)

    @profile
    def run_benchmarks(self) -> Dict[str, List[Dict]]:
        """Run all benchmarks and return results."""
        results = {
            "json": [],
            "custom": []
        }

        for i, message in enumerate(self.test_messages):
            # JSON Protocol
            json_serialized = self.json_protocol.serialize(message)
            json_size = self.measure_size(json_serialized)
            json_serialize_time = self.measure_time(self.json_protocol.serialize, message)
            json_deserialize_time = self.measure_time(self.json_protocol.deserialize, json_serialized)

            # Custom Protocol
            custom_serialized = self.custom_protocol.serialize(message)
            custom_size = self.measure_size(custom_serialized)
            custom_serialize_time = self.measure_time(self.custom_protocol.serialize, message)
            custom_deserialize_time = self.measure_time(self.custom_protocol.deserialize, custom_serialized)

            # Store results
            results["json"].append({
                "message_type": self.test_messages[i]["type"],
                "size": json_size,
                "serialize_time": json_serialize_time,
                "deserialize_time": json_deserialize_time
            })

            results["custom"].append({
                "message_type": self.test_messages[i]["type"],
                "size": custom_size,
                "serialize_time": custom_serialize_time,
                "deserialize_time": custom_deserialize_time
            })

        return results

    def plot_results(self, results: Dict[str, List[Dict]]):
        """Generate plots comparing protocol performance."""
        message_types = [r["message_type"] for r in results["json"]]
        x = range(len(message_types))

        # Plot message sizes
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.2 for i in x], [r["size"] for r in results["json"]], 0.4, label="JSON")
        plt.bar([i + 0.2 for i in x], [r["size"] for r in results["custom"]], 0.4, label="Custom")
        plt.xlabel("Message Type")
        plt.ylabel("Size (bytes)")
        plt.title("Message Size Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/json_vs_custom_size_comparison.png")
        plt.close()

        # Plot serialization times
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.2 for i in x], [r["serialize_time"] for r in results["json"]], 0.4, label="JSON")
        plt.bar([i + 0.2 for i in x], [r["serialize_time"] for r in results["custom"]], 0.4, label="Custom")
        plt.xlabel("Message Type")
        plt.ylabel("Time (seconds)")
        plt.title("Serialization Time Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/serialize_time_comparison.png")
        plt.close()

        # Plot deserialization times
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.2 for i in x], [r["deserialize_time"] for r in results["json"]], 0.4, label="JSON")
        plt.bar([i + 0.2 for i in x], [r["deserialize_time"] for r in results["custom"]], 0.4, label="Custom")
        plt.xlabel("Message Type")
        plt.ylabel("Time (seconds)")
        plt.title("Deserialization Time Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/deserialize_time_comparison.png")
        plt.close()

def main():
    """Run benchmarks and generate report."""
    benchmark = ProtocolBenchmark()
    results = benchmark.run_benchmarks()
    benchmark.plot_results(results)

    # Print summary
    print("\nProtocol Performance Comparison")
    print("==============================")

    for msg_type in range(len(benchmark.test_messages)):
        json_results = results["json"][msg_type]
        custom_results = results["custom"][msg_type]

        size_diff = (json_results["size"] - custom_results["size"]) / json_results["size"] * 100
        serialize_speedup = json_results["serialize_time"] / custom_results["serialize_time"]
        deserialize_speedup = json_results["deserialize_time"] / custom_results["deserialize_time"]

        print(f"\nMessage Type: {json_results['message_type']}")
        print(f"Size Reduction: {size_diff:.1f}%")
        print(f"Serialization Speedup: {serialize_speedup:.1f}x")
        print(f"Deserialization Speedup: {deserialize_speedup:.1f}x")

if __name__ == "__main__":
    main()
