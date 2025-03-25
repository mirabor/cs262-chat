"""
Configuration settings for the client application.
"""

# Replica management settings
KNOWN_REPLICAS_INITIAL = []  # Will be populated with the primary address in the client
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Base delay in seconds
