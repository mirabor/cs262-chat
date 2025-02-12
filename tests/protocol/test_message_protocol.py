"""Test cases for message protocol handling."""

import pytest
import json
from src.protocol.json_protocol import JsonProtocol
from src.protocol.message_handler import MessageHandler

@pytest.fixture
def protocol():
    """Create a test protocol instance."""
    return JsonProtocol()

@pytest.fixture
def message_handler():
    """Create a test message handler instance."""
    return MessageHandler()

def test_message_serialization(protocol):
    """Test message serialization and deserialization."""
    # Test message data
    message = {
        "operation": "send_message",
        "sender": "user1",
        "receiver": "user2",
        "content": "Hello, World!",
        "timestamp": "2025-02-12T01:30:43-05:00"
    }
    
    # Serialize
    serialized = protocol.serialize(message)
    
    # Deserialize
    deserialized = protocol.deserialize(serialized)
    
    # Verify
    assert deserialized == message
    assert isinstance(serialized, bytes)

def test_message_validation(protocol):
    """Test message validation."""
    # Valid message
    valid_message = {
        "operation": "send_message",
        "sender": "user1",
        "receiver": "user2",
        "content": "Test message"
    }
    assert protocol.validate_message(valid_message) is True
    
    # Invalid message (missing required fields)
    invalid_message = {
        "operation": "send_message",
        "sender": "user1"
    }
    assert protocol.validate_message(invalid_message) is False
    
    # Invalid operation
    invalid_op_message = {
        "operation": "invalid_op",
        "sender": "user1",
        "receiver": "user2",
        "content": "Test"
    }
    assert protocol.validate_message(invalid_op_message) is False

def test_message_handling(message_handler):
    """Test message handling and queuing."""
    # Add messages to queue
    messages = [
        {"sender": "user1", "content": "Message 1", "timestamp": "2025-02-12T01:30:43-05:00"},
        {"sender": "user2", "content": "Message 2", "timestamp": "2025-02-12T01:30:44-05:00"},
        {"sender": "user1", "content": "Message 3", "timestamp": "2025-02-12T01:30:45-05:00"}
    ]
    
    for msg in messages:
        message_handler.queue_message(msg)
    
    # Check queue size
    assert message_handler.get_queue_size() == 3
    
    # Get messages respecting limit
    limit = 2
    retrieved = message_handler.get_messages(limit)
    assert len(retrieved) == limit
    
    # Verify order (FIFO)
    assert retrieved[0]["content"] == "Message 1"
    assert retrieved[1]["content"] == "Message 2"

def test_message_filtering(message_handler):
    """Test message filtering by sender."""
    # Add messages from different senders
    messages = [
        {"sender": "user1", "content": "From user1"},
        {"sender": "user2", "content": "From user2"},
        {"sender": "user1", "content": "Another from user1"}
    ]
    
    for msg in messages:
        message_handler.queue_message(msg)
    
    # Filter messages by sender
    user1_messages = message_handler.get_messages_by_sender("user1")
    assert len(user1_messages) == 2
    assert all(msg["sender"] == "user1" for msg in user1_messages)

def test_protocol_error_handling(protocol):
    """Test protocol error handling."""
    # Test invalid JSON
    invalid_json = b"invalid json data"
    with pytest.raises(json.JSONDecodeError):
        protocol.deserialize(invalid_json)
    
    # Test oversized message
    large_content = "x" * (protocol.MAX_MESSAGE_SIZE + 1)
    large_message = {
        "operation": "send_message",
        "content": large_content
    }
    with pytest.raises(ValueError):
        protocol.serialize(large_message)

def test_message_acknowledgment(protocol, message_handler):
    """Test message acknowledgment system."""
    # Send message
    message = {
        "operation": "send_message",
        "message_id": "msg123",
        "sender": "user1",
        "receiver": "user2",
        "content": "Test message"
    }
    
    # Create acknowledgment
    ack = protocol.create_acknowledgment(message["message_id"], "delivered")
    
    # Verify acknowledgment
    assert ack["type"] == "ack"
    assert ack["message_id"] == message["message_id"]
    assert ack["status"] == "delivered"
    
    # Test invalid acknowledgment
    with pytest.raises(ValueError):
        protocol.create_acknowledgment(message["message_id"], "invalid_status")

def test_message_ordering(message_handler):
    """Test message ordering and timestamp handling."""
    # Add messages with different timestamps
    messages = [
        {"sender": "user1", "content": "Message 1", "timestamp": "2025-02-12T01:30:43-05:00"},
        {"sender": "user1", "content": "Message 2", "timestamp": "2025-02-12T01:30:42-05:00"},  # Earlier
        {"sender": "user1", "content": "Message 3", "timestamp": "2025-02-12T01:30:44-05:00"}   # Later
    ]
    
    for msg in messages:
        message_handler.queue_message(msg)
    
    # Get ordered messages
    ordered = message_handler.get_ordered_messages()
    
    # Verify chronological order
    assert ordered[0]["content"] == "Message 2"  # Earliest
    assert ordered[1]["content"] == "Message 1"
    assert ordered[2]["content"] == "Message 3"  # Latest
