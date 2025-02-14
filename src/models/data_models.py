from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class User:
    username: str
    nickname: str
    message_limit: int = 50
    user_id: Optional[int] = None

@dataclass
class Message:
    content: str
    sender: str
    timestamp: datetime
    message_id: Optional[int] = None
    
@dataclass
class Chat:
    chat_id: int
    participants: List[str]
    created_at: datetime
    messages: List[Message] = None
    
@dataclass
class ChatResponse:
    chat_id: int
    messages: List[Message]
    error_message: Optional[str] = None
