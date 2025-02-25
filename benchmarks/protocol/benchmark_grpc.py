import time
import statistics
from typing import Dict, List
import matplotlib.pyplot as plt
import grpc
from src.protocol.grpc import chat_pb2, chat_pb2_grpc
from src.protocol.protocol_factory import JsonProtocol, CustomProtocol

class GRPCBenchmark:
    """Benchmark gRPC performance against JSON and Custom protocols."""

    def __init__(self):
        self.json_protocol = JsonProtocol()
        self.custom_protocol = CustomProtocol()

        # Test messages of increasing complexity aligned with proto definition
        self.test_messages = [
            # Simple message
            {
                "type": "simple_message",
                "id": 1,
                "sender": "user1",
                "content": "Hello, world!",
                "timestamp": "1644582794",
                "read": 0
            },

            # Typical chat message
            {
                "type": "typical_chat_message",
                "id": 2,
                "sender": "user1",
                "content": "Hey, how are you?",
                "timestamp": "1644582795",
                "read": 1
            },

            # Complex message
            {
                "type": "complex_message",
                "id": 3,
                "sender": "user1",
                "content": "Meeting at 3pm",
                "timestamp": "1644582796",
                "read": 0
            },

            # Large message
            {
                "type": "large_message",
                "id": 4,
                "sender": "user1",
                "content": "This is a large message with lots of content " * 100,
                "timestamp": "1644582797",
                "read": 1
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

    def run_benchmarks(self) -> Dict[str, List[Dict]]:
        """Run all benchmarks and return results."""
        results = {
            "json": [],
            "custom": [],
            "grpc": []
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

            # gRPC Protocol
            grpc_message = chat_pb2.Message(
                id=message.get("id", 0),
                sender=message.get("sender", ""),
                content=message.get("content", ""),
                timestamp=message.get("timestamp", "0"),
                read=message.get("read", 0)
            )
            grpc_serialized = grpc_message.SerializeToString()
            grpc_size = self.measure_size(grpc_serialized)
            grpc_serialize_time = self.measure_time(grpc_message.SerializeToString)
            grpc_deserialize_time = self.measure_time(chat_pb2.Message.FromString, grpc_serialized)

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

            results["grpc"].append({
                "message_type": self.test_messages[i]["type"],
                "size": grpc_size,
                "serialize_time": grpc_serialize_time,
                "deserialize_time": grpc_deserialize_time
            })

        return results

    def plot_results(self, results: Dict[str, List[Dict]]):
        """Generate plots comparing protocol performance."""
        message_types = [r["message_type"] for r in results["json"]]
        x = range(len(message_types))

        # Plot message sizes
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.3 for i in x], [r["size"] for r in results["json"]], 0.3, label="JSON")
        plt.bar([i for i in x], [r["size"] for r in results["custom"]], 0.3, label="Custom")
        plt.bar([i + 0.3 for i in x], [r["size"] for r in results["grpc"]], 0.3, label="gRPC")
        plt.xlabel("Message Type")
        plt.ylabel("Size (bytes)")
        plt.title("Message Size Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/size_comparison.png")
        plt.close()

        # Plot serialization times
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.3 for i in x], [r["serialize_time"] for r in results["json"]], 0.3, label="JSON")
        plt.bar([i for i in x], [r["serialize_time"] for r in results["custom"]], 0.3, label="Custom")
        plt.bar([i + 0.3 for i in x], [r["serialize_time"] for r in results["grpc"]], 0.3, label="gRPC")
        plt.xlabel("Message Type")
        plt.ylabel("Time (seconds)")
        plt.title("Serialization Time Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/serialize_time_comparison.png")
        plt.close()

        # Plot deserialization times
        plt.figure(figsize=(10, 5))
        plt.bar([i - 0.3 for i in x], [r["deserialize_time"] for r in results["json"]], 0.3, label="JSON")
        plt.bar([i for i in x], [r["deserialize_time"] for r in results["custom"]], 0.3, label="Custom")
        plt.bar([i + 0.3 for i in x], [r["deserialize_time"] for r in results["grpc"]], 0.3, label="gRPC")
        plt.xlabel("Message Type")
        plt.ylabel("Time (seconds)")
        plt.title("Deserialization Time Comparison")
        plt.xticks(x, message_types)
        plt.legend()
        plt.savefig("benchmarks/protocol/results/deserialize_time_comparison.png")
        plt.close()

def main():
    """Run benchmarks and generate report."""
    benchmark = GRPCBenchmark()
    results = benchmark.run_benchmarks()
    benchmark.plot_results(results)

    # Print summary
    print("\nProtocol Performance Comparison")
    print("==============================")

    for msg_type in range(len(benchmark.test_messages)):
        json_results = results["json"][msg_type]
        custom_results = results["custom"][msg_type]
        grpc_results = results["grpc"][msg_type]

        size_diff_json_grpc = (json_results["size"] - grpc_results["size"]) / json_results["size"] * 100
        size_diff_custom_grpc = (custom_results["size"] - grpc_results["size"]) / custom_results["size"] * 100
        serialize_speedup_json_grpc = json_results["serialize_time"] / grpc_results["serialize_time"]
        serialize_speedup_custom_grpc = custom_results["serialize_time"] / grpc_results["serialize_time"]
        deserialize_speedup_json_grpc = json_results["deserialize_time"] / grpc_results["deserialize_time"]
        deserialize_speedup_custom_grpc = custom_results["deserialize_time"] / grpc_results["deserialize_time"]

        print(f"\nMessage Type: {json_results['message_type']}")
        print(f"Size Reduction (JSON vs gRPC): {size_diff_json_grpc:.1f}%")
        print(f"Size Reduction (Custom vs gRPC): {size_diff_custom_grpc:.1f}%")
        print(f"Serialization Speedup (JSON vs gRPC): {serialize_speedup_json_grpc:.1f}x")
        print(f"Serialization Speedup (Custom vs gRPC): {serialize_speedup_custom_grpc:.1f}x")
        print(f"Deserialization Speedup (JSON vs gRPC): {deserialize_speedup_json_grpc:.1f}x")
        print(f"Deserialization Speedup (Custom vs gRPC): {deserialize_speedup_custom_grpc:.1f}x")

if __name__ == "__main__":
    main()