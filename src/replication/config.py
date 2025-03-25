# config.py
"""
Configuration constants for the fault-tolerant server.
"""

# Timing constants
HEARTBEAT_INTERVAL = 1  # seconds - How often leader sends heartbeats
ELECTION_TIMEOUT_MIN = 3  # seconds - Minimum time before starting election
ELECTION_TIMEOUT_MAX = 6  # seconds - Maximum time before starting election
MAX_MISSED_HEARTBEATS = (
    3  # Number of missed heartbeats before considering a server failed
)
