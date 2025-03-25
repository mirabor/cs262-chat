import grpc
import time
import random
import logging
from protocol.grpc import chat_pb2, chat_pb2_grpc
from .utils import hash_password
from .config import MAX_RETRIES, RETRY_DELAY

# Set up logger
logger = logging.getLogger(__name__)


class ChatAppLogicGRPC:
    def __init__(self, host="localhost", port=50051):
        """
        Create a gRPC channel and stub.
        Replace host/port with your gRPC server address/port.
        """

        print(f"INFO: grpcLogic, Using gRPC server at {host}:{port}")
        self.primary_address = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.primary_address)
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.current_user = None
        self.chat_cache = {}  # mimic the old 'chat_cache' usage
        self.prev_metric_size = {
            "request_size": 0,
            "response_size": 0,
        }
        
        # Replica management
        self.known_replicas = [self.primary_address]  # Start with the primary server
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY

    def _extract_metadata(self, response_metadata):
        """
        Extract replica information from response metadata.
        Assumes metadata contains replica addresses.
        """
        replicas = []
        
        logger.debug(f"Extracting metadata from response: {response_metadata}")
        
        # TODO: fix so it parse actual metadata from the gRPC response
        for key, value in response_metadata:
            if key == 'replicas':
                replicas = value.split(',')
                logger.debug(f"Found replicas in metadata: {replicas}")
                
        return replicas
    
    def _update_replicas(self, response_metadata):
        """
        Update known replicas information from the server metadata
        """
        replicas = self._extract_metadata(response_metadata)
        
        logger.debug(f"Extracted replicas from metadata: {replicas}")
        
        if replicas:
            old_replicas = self.known_replicas.copy()
            # Update our list of known replicas
            self.known_replicas = list(set(self.known_replicas + replicas))
            
            # Log changes to replica list
            new_replicas = [r for r in self.known_replicas if r not in old_replicas]
            if new_replicas:
                logger.info(f"Added new replicas: {new_replicas}")
            logger.debug(f"Updated known_replicas: {self.known_replicas}")
    
    def _execute_with_retry(self, rpc_method, request):
        retries = 0
        tried_addresses = set()
        current_delay = self.retry_delay
        method_name = rpc_method.__name__ if hasattr(rpc_method, '__name__') else 'unknown_method'
        
        logger.info(f"Starting RPC call to {method_name} with retry mechanism")
        logger.debug(f"Known replicas: {self.known_replicas}")
        
        while retries <= self.max_retries:
            # Choose server to try
            if retries == 0:
                server_address = self.primary_address
                logger.info(f"Using primary server: {server_address}")
            else:
                # Get available replicas we haven't tried yet
                available_replicas = [r for r in self.known_replicas if r not in tried_addresses]
                logger.debug(f"Available replicas not yet tried: {available_replicas}")
                
                if not available_replicas:
                    # If we've tried all, reset and try again
                    logger.warning("All known replicas have been tried, resetting tried_addresses")
                    tried_addresses = set()
                    available_replicas = self.known_replicas
                
                server_address = random.choice(available_replicas)
                logger.info(f"Selected replica for retry {retries}: {server_address}")
            
            tried_addresses.add(server_address)
            logger.debug(f"Updated tried_addresses: {tried_addresses}")
            
            # Always create new channel when switching servers
            if not hasattr(self, 'current_server') or server_address != self.current_server:
                logger.info(f"Creating new channel to server: {server_address}")
                self.channel = grpc.insecure_channel(server_address)
                self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
                self.current_server = server_address
                
            try:
                logger.info(f"Attempting RPC call to {method_name} on {server_address}")
                response = rpc_method(request)
                logger.info(f"RPC call to {method_name} successful")
                return response
            except grpc.RpcError as e:
                retries += 1
                status_code = e.code() if hasattr(e, 'code') else 'unknown'
                details = e.details() if hasattr(e, 'details') else str(e)
                
                logger.error(f"RPC failed: status={status_code}, details='{details}'. Retry {retries}/{self.max_retries}")
                
                if retries <= self.max_retries:  # Only sleep if we'll retry again
                    jitter = random.uniform(0, 0.1 * current_delay)
                    sleep_time = current_delay + jitter
                    logger.debug(f"Sleeping for {sleep_time:.2f}s before retry {retries}")
                    time.sleep(sleep_time)
                    current_delay = min(current_delay * 2, 5)
        
        logger.critical(f"Failed to complete request after {self.max_retries} retries")
        raise Exception(f"Failed to complete request after {self.max_retries} retries")

    def signup(self, username, nickname, password):
        """Sign up a new user."""
        if not username or not nickname or not password:
            return False, "All fields are required."

        hashed_password = hash_password(password)
        request = chat_pb2.SignupRequest(
            username=username,
            nickname=nickname,
            password=hashed_password,
        )
        
        try:
            response = self._execute_with_retry(self.stub.Signup, request)
            return response.success, response.error_message
        except Exception as e:
            return False, f"Failed to sign up: {str(e)}"

    def login(self, username, password):
        """Attempt to log the user in using gRPC."""
        if not username or not password:
            return False, "Username and password are required."

        hashed_password = hash_password(password)
        request = chat_pb2.LoginRequest(username=username, password=hashed_password)

        try:
            response = self._execute_with_retry(self.stub.Login, request)
            return response.success, response.error_message or ""
        except Exception as e:
            return False, f"Failed to login: {str(e)}"

    def get_users_to_display(
        self, current_user, search_pattern, current_page, users_per_page
    ):
        """Retrieve a paginated list of users."""
        request = chat_pb2.GetUsersToDisplayRequest(
            exclude_username=current_user,
            search_pattern=search_pattern or "",
            current_page=current_page or 1,
            users_per_page=users_per_page or 10,
        )
        try:
            response = self._execute_with_retry(self.stub.GetUsersToDisplay, request)
            return response.usernames, response.error_message
        except Exception as e:
            return [], f"Failed to get users: {str(e)}"

    def get_chats(self, user_id):
        """Retrieve all chats for a user."""

        print(f"GetChats called for user_id: {user_id} of type {type(user_id)}")
        request = chat_pb2.GetChatsRequest(user_id=user_id)
        
        try:
            response = self._execute_with_retry(self.stub.GetChats, request)
    
            if response.error_message:
                return [], response.error_message
    
            chats = []
            for chat in response.chats:
                chat_info = {
                    "chat_id": chat.chat_id,
                    "other_user": chat.other_user,
                    "unread_count": chat.unread_count,
                }
                chats.append(chat_info)
                self.chat_cache[chat.chat_id] = chat_info
                print(f"Added chat to cache: {chat_info}")
    
            return chats, ""
        except Exception as e:
            return [], f"Failed to get chats: {str(e)}"

    def get_other_user_in_chat(self, chat_id):
        other_user = self.chat_cache.get(chat_id, {}).get("other_user")
        print(
            f"GetOtherUserInChat called for chat_id: {chat_id}, got other user: {other_user}"
        )
        return other_user

    def get_messages(self, chat_id, current_user):
        """Retrieve messages for a given chat."""
        request = chat_pb2.GetMessagesRequest(
            chat_id=chat_id,
            current_user=current_user,
        )
        print(
            f"INFO: grpc_logic get message request: id {request.chat_id} and user {request.current_user}"
        )
        
        try:
            response = self._execute_with_retry(self.stub.GetMessages, request)
            
            if response.error_message:
                return [], response.error_message
    
            print(f"INFO: grpc_logic got response: {response}")
            messages_list = []
            for msg in response.messages:
                messages_list.append(
                    {
                        "sender": msg.sender,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                    }
                )
            return messages_list, ""
        except Exception as e:
            return [], f"Failed to get messages: {str(e)}"

    def start_chat(self, current_user, other_user):
        """Initiate a new chat between two users."""
        request = chat_pb2.StartChatRequest(
            current_user=current_user,
            other_user=other_user,
        )
        
        try:
            response = self._execute_with_retry(self.stub.StartChat, request)
            
            if not response.success:
                return None, response.error_message
            return response.chat.chat_id, ""
        except Exception as e:
            return None, f"Failed to start chat: {str(e)}"

    def get_user_message_limit(self, current_user):
        """Get the user's message limit (for UI or logic checks)."""
        request = chat_pb2.GetUserMessageLimitRequest(username=current_user)
        
        try:
            response = self._execute_with_retry(self.stub.GetUserMessageLimit, request)
            return response.limit, response.error_message
        except Exception as e:
            return "", f"Failed to get message limit: {str(e)}"

    def delete_messages(self, chat_id, message_indices, current_user):
        """Send a request to delete specific messages in a chat."""
        request = chat_pb2.DeleteMessagesRequest(
            chat_id=chat_id,
            message_indices=message_indices,
            current_user=current_user,
        )
        
        try:
            response = self._execute_with_retry(self.stub.DeleteMessages, request)
            return response.success, response.error_message
        except Exception as e:
            return False, f"Failed to delete messages: {str(e)}"

    def send_chat_message(self, chat_id, sender, content):
        """Send a new message in a chat."""
        request = chat_pb2.SendMessageRequest(
            chat_id=chat_id,
            sender=sender,
            content=content,
        )
        
        try:
            response = self._execute_with_retry(self.stub.SendChatMessage, request)
            return response.success, response.error_message
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"

    def save_settings(self, username, message_limit):
        """Update user settings (message limit, etc.)."""
        request = chat_pb2.SaveSettingsRequest(
            username=username,
            message_limit=message_limit,
        )
        
        try:
            response = self._execute_with_retry(self.stub.SaveSettings, request)
            return response.success, response.error_message
        except Exception as e:
            return False, f"Failed to save settings: {str(e)}"

    def delete_account(self, current_user):
        """Delete the current user's account."""
        request = chat_pb2.DeleteUserRequest(username=current_user)
        
        try:
            response = self._execute_with_retry(self.stub.DeleteUser, request)
            return response.success, response.error_message
        except Exception as e:
            return False, f"Failed to delete account: {str(e)}"
