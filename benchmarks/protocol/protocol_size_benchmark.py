from typing import Dict, List
import matplotlib.pyplot as plt
import os
from src.protocol.grpc import chat_pb2
from src.protocol.protocol_factory import JsonProtocol, CustomProtocol


class ProtocolSizeBenchmark:
    """benchmark focusing on size comparisons between protocols."""

    def __init__(self):
        self.json_protocol = JsonProtocol()
        self.custom_protocol = CustomProtocol()

        # Test cases with proto message structures
        self.test_cases = self.prepare_test_messages()

    def prepare_test_messages(self):
        """Create test messages using proto message structures."""
        return [
            # 1. Small MessagesResponse with a few messages
            {
                "name": "small_messages_response",
                "description": "Chat history with 2 messages",
                "proto_class": chat_pb2.MessagesResponse,
                "json_data": {
                    "messages": [
                        {
                            "id": 1,
                            "sender": "user1",
                            "content": "Hello!",
                            "timestamp": "1644582794",
                            "read": 1,
                        },
                        {
                            "id": 2,
                            "sender": "user2",
                            "content": "Hi there!",
                            "timestamp": "1644582795",
                            "read": 0,
                        },
                    ],
                    "error_message": "",
                },
            },
            # 2. Medium MessagesResponse with ~10 messages
            {
                "name": "medium_messages_response",
                "description": "Chat history with 10 messages",
                "proto_class": chat_pb2.MessagesResponse,
                "json_data": {
                    "messages": [
                        {
                            "id": i,
                            "sender": f"user{i%3+1}",
                            "content": f"This is message {i} with some content.",
                            "timestamp": str(1644582794 + i),
                            "read": i % 2,
                        }
                        for i in range(1, 11)
                    ],
                    "error_message": "",
                },
            },
            # 3. Large MessagesResponse with ~50 messages (realistic chat history)
            {
                "name": "large_messages_response",
                "description": "Chat history with 50 messages of varying length",
                "proto_class": chat_pb2.MessagesResponse,
                "json_data": {
                    "messages": [
                        {
                            "id": i,
                            "sender": f"user{i%3+1}",
                            "content": f"Message {i}: "
                            + "Lorem ipsum dolor sit amet. " * (i % 5 + 1),
                            "timestamp": str(1644582794 + i),
                            "read": i % 2,
                        }
                        for i in range(1, 51)
                    ],
                    "error_message": "",
                },
            },
            # 4. ChatsResponse with many chats
            {
                "name": "chats_response",
                "description": "List of 30 chat conversations",
                "proto_class": chat_pb2.ChatsResponse,
                "json_data": {
                    "chats": [
                        {
                            "chat_id": f"chat_{i}",
                            "other_user": f"user_{i}",
                            "unread_count": i % 5,
                        }
                        for i in range(1, 31)
                    ],
                    "error_message": "",
                },
            },
            # 5. UsersDisplayResponse with many usernames
            {
                "name": "users_response",
                "description": "List of 100 usernames (string array)",
                "proto_class": chat_pb2.UsersDisplayResponse,
                "json_data": {
                    "usernames": [f"user_{i}" for i in range(1, 101)],
                    "total_pages": 10,
                    "error_message": "",
                },
            },
        ]

    def json_to_proto(self, json_data, proto_class):
        """Convert JSON data to protobuf message."""
        if proto_class == chat_pb2.MessagesResponse:
            proto_msg = chat_pb2.MessagesResponse(
                error_message=json_data.get("error_message", "")
            )

            for msg_data in json_data.get("messages", []):
                message = chat_pb2.Message(
                    id=msg_data.get("id", 0),
                    sender=msg_data.get("sender", ""),
                    content=msg_data.get("content", ""),
                    timestamp=msg_data.get("timestamp", ""),
                    read=msg_data.get("read", 0),
                )
                proto_msg.messages.append(message)

            return proto_msg

        elif proto_class == chat_pb2.ChatsResponse:
            proto_msg = chat_pb2.ChatsResponse(
                error_message=json_data.get("error_message", "")
            )

            for chat_data in json_data.get("chats", []):
                chat = chat_pb2.Chat(
                    chat_id=chat_data.get("chat_id", ""),
                    other_user=chat_data.get("other_user", ""),
                    unread_count=chat_data.get("unread_count", 0),
                )
                proto_msg.chats.append(chat)

            return proto_msg

        elif proto_class == chat_pb2.UsersDisplayResponse:
            proto_msg = chat_pb2.UsersDisplayResponse(
                total_pages=json_data.get("total_pages", 0),
                error_message=json_data.get("error_message", ""),
            )

            for username in json_data.get("usernames", []):
                proto_msg.usernames.append(username)

            return proto_msg

        else:
            raise ValueError(f"Unsupported proto class: {proto_class}")

    def measure_size(self, data: bytes) -> int:
        """Measure size of serialized data in bytes."""
        return len(data)

    def run_benchmarks(self):
        """Run size benchmarks for all protocols and message types."""
        results = {"json": [], "custom": [], "grpc": []}

        for test_case in self.test_cases:
            message_name = test_case["name"]
            json_data = test_case["json_data"]
            proto_class = test_case["proto_class"]

            print(f"Benchmarking {message_name}...")

            # JSON Protocol
            json_serialized = self.json_protocol.serialize(json_data)
            json_size = self.measure_size(json_serialized)

            # Custom Protocol
            custom_serialized = self.custom_protocol.serialize(json_data)
            custom_size = self.measure_size(custom_serialized)

            # gRPC Protocol
            proto_msg = self.json_to_proto(json_data, proto_class)
            grpc_serialized = proto_msg.SerializeToString()
            grpc_size = self.measure_size(grpc_serialized)

            # Store results
            results["json"].append(
                {
                    "message_type": message_name,
                    "description": test_case["description"],
                    "size": json_size,
                }
            )

            results["custom"].append(
                {
                    "message_type": message_name,
                    "description": test_case["description"],
                    "size": custom_size,
                }
            )

            results["grpc"].append(
                {
                    "message_type": message_name,
                    "description": test_case["description"],
                    "size": grpc_size,
                }
            )

        return results

    def plot_size_results(self, results, output_dir="benchmarks/protocol/results"):
        """Generate a plot comparing protocol sizes."""
        os.makedirs(output_dir, exist_ok=True)

        message_types = [r["message_type"] for r in results["json"]]
        message_descriptions = [r["description"] for r in results["json"]]
        x = range(len(message_types))

        # Plot message sizes
        plt.figure(figsize=(12, 7))
        bars1 = plt.bar(
            [i - 0.25 for i in x],
            [r["size"] for r in results["json"]],
            0.25,
            label="JSON",
        )
        bars2 = plt.bar(x, [r["size"] for r in results["custom"]], 0.25, label="Custom")
        bars3 = plt.bar(
            [i + 0.25 for i in x],
            [r["size"] for r in results["grpc"]],
            0.25,
            label="gRPC",
        )

        plt.xlabel("Message Type")
        plt.ylabel("Size (bytes)")
        plt.title("Message Size Comparison")

        # Use more descriptive x-tick labels
        descriptions = []
        for name, desc in zip(message_types, message_descriptions):
            descriptions.append(f"{name}\n({desc})")

        plt.xticks(x, descriptions, rotation=45, ha="right")
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Add size reduction percentages for gRPC
        for i in range(len(message_types)):
            json_size = results["json"][i]["size"]
            grpc_size = results["grpc"][i]["size"]
            reduction = (json_size - grpc_size) / json_size * 100

            # Add annotation regardless of reduction size
            plt.annotate(
                f"{reduction:.1f}% smaller",
                xy=(i + 0.25, grpc_size),
                xytext=(
                    i + 0.25,
                    grpc_size + (max([r["size"] for r in results["json"]]) * 0.05),
                ),
                ha="center",
                va="bottom",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
            )

        # Add a ratio comparison text in the top right
        avg_reduction = sum(
            [
                (results["json"][i]["size"] - results["grpc"][i]["size"])
                / results["json"][i]["size"]
                * 100
                for i in range(len(message_types))
            ]
        ) / len(message_types)

        plt.figtext(
            0.9,
            0.9,
            f"Average reduction: {avg_reduction:.1f}%",
            ha="right",
            fontsize=10,
            bbox=dict(
                boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.9
            ),
        )

        plt.tight_layout()
        plt.savefig(f"{output_dir}/all_protocols_size_comparison.png", dpi=300)
        plt.close()

    def print_size_summary(self, results):
        """Print a summary of the size benchmark results."""
        print("\nProtocol Size Comparison Summary:")
        print("================================")

        print(
            f"{'Message Type':<30} {'JSON':<10} {'Custom':<10} {'gRPC':<10} {'Reduction':<10} {'Ratio':<5}"
        )
        print("-" * 75)

        total_json = 0
        total_custom = 0
        total_grpc = 0

        for i in range(len(results["json"])):
            message_type = results["json"][i]["message_type"]
            description = results["json"][i]["description"]

            json_size = results["json"][i]["size"]
            custom_size = results["custom"][i]["size"]
            grpc_size = results["grpc"][i]["size"]

            reduction = (json_size - grpc_size) / json_size * 100
            ratio = json_size / max(1, grpc_size)

            print(
                f"{message_type:<30} {json_size:<10} {custom_size:<10} {grpc_size:<10} {reduction:>6.1f}% {ratio:>5.1f}x"
            )

            total_json += json_size
            total_custom += custom_size
            total_grpc += grpc_size

        # Print totals and averages
        print("-" * 75)
        total_reduction = (total_json - total_grpc) / total_json * 100
        total_ratio = total_json / max(1, total_grpc)
        print(
            f"{'TOTAL':<30} {total_json:<10} {total_custom:<10} {total_grpc:<10} {total_reduction:>6.1f}% {total_ratio:>5.1f}x"
        )

        print("\nSize Efficiency Analysis:")
        print("------------------------")

        # Find best and worst cases
        best_case_idx = max(
            range(len(results["json"])),
            key=lambda i: results["json"][i]["size"]
            / max(1, results["grpc"][i]["size"]),
        )
        worst_case_idx = min(
            range(len(results["json"])),
            key=lambda i: results["json"][i]["size"]
            / max(1, results["grpc"][i]["size"]),
        )

        best_case = results["json"][best_case_idx]["message_type"]
        best_reduction = (
            (
                results["json"][best_case_idx]["size"]
                - results["grpc"][best_case_idx]["size"]
            )
            / results["json"][best_case_idx]["size"]
            * 100
        )

        worst_case = results["json"][worst_case_idx]["message_type"]
        worst_reduction = (
            (
                results["json"][worst_case_idx]["size"]
                - results["grpc"][worst_case_idx]["size"]
            )
            / results["json"][worst_case_idx]["size"]
            * 100
        )

        print(f"- Most efficient for: {best_case} ({best_reduction:.1f}% reduction)")
        print(f"- Least efficient for: {worst_case} ({worst_reduction:.1f}% reduction)")

        # Categorize by message structure
        print("\nEfficiency by Message Structure:")

        # Repeated fields (arrays)
        array_types = ["users_response", "chats_response"]
        array_reductions = []

        for i, result in enumerate(results["json"]):
            if any(t in result["message_type"] for t in array_types):
                reduction = (
                    (result["size"] - results["grpc"][i]["size"]) / result["size"] * 100
                )
                array_reductions.append(reduction)

        if array_reductions:
            avg_array_reduction = sum(array_reductions) / len(array_reductions)
            print(
                f"- Repeated fields (arrays): {avg_array_reduction:.1f}% average reduction"
            )

        # Nested structures
        nested_types = ["messages_response"]
        nested_reductions = []

        for i, result in enumerate(results["json"]):
            if any(t in result["message_type"] for t in nested_types):
                reduction = (
                    (result["size"] - results["grpc"][i]["size"]) / result["size"] * 100
                )
                nested_reductions.append(reduction)

        if nested_reductions:
            avg_nested_reduction = sum(nested_reductions) / len(nested_reductions)
            print(f"- Nested structures: {avg_nested_reduction:.1f}% average reduction")

            print(
                f"For transferring 1GB of data, you would save approximately {total_reduction/100:.2f}GB using gRPC instead of JSON"
            )


def main():
    """Run size benchmarks and generate visualizations."""
    print("Starting protocol size benchmarks...")

    benchmark = ProtocolSizeBenchmark()
    results = benchmark.run_benchmarks()

    print("Generating size comparison visualizations...")
    benchmark.plot_size_results(results)

    # Print summary to console
    benchmark.print_size_summary(results)

    print("\nBenchmark complete. Results saved to benchmarks/protocol/results/")


if __name__ == "__main__":
    main()
