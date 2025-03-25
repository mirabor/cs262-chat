import grpc
import time
import random
from protocol.grpc import chat_pb2, chat_pb2_grpc
from .utils import hash_password


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
        self.current_leader = None  # Will be updated when we get leader info
        self.max_retries = 3
        self.retry_delay = 1.0  # Base delay in seconds

    def _extract_metadata(self, response_metadata):
        """
        Extract replica information from response metadata.
        Assumes metadata contains replica addresses.
        """
        replicas = []
        leader = None
        
        # TODO: fix so it parse actual metadata from the gRPC response
        for key, value in response_metadata:
            if key == 'replicas':
                replicas = value.split(',')
            elif key == 'leader':
                leader = value
                
        return replicas, leader
    
    def _update_replicas(self, response_metadata):
        """
        Update known replicas and leader information from the server metadata
        """
        replicas, leader = self._extract_metadata(response_metadata)
        
        if replicas:
            # Update our list of known replicas
            for replica in replicas:
                if replica not in self.known_replicas:
                    self.known_replicas.append(replica)
        
        if leader:
            self.current_leader = leader
            # If we know the leader, prioritize it by putting it first in our list
            if leader in self.known_replicas:
                self.known_replicas.remove(leader)
                self.known_replicas.insert(0, leader)
    
    def _execute_with_retry(self, rpc_method, request):
        retries = 0
        tried_addresses = set()
        current_delay = self.retry_delay
        
        while retries <= self.max_retries:
        # Choose server, prioritize leader if known and not tried
            if retries == 0:
                server_address = self.primary_address
            elif self.current_leader and self.current_leader not in tried_addresses:
                server_address = self.current_leader
            else:
                # Get available replicas we haven't tried yet
                available_replicas = [r for r in self.known_replicas if r not in tried_addresses]
                if not available_replicas:
                    # If we've tried all, reset and try again
                    tried_addresses = set()
                    available_replicas = self.known_replicas
                server_address = random.choice(available_replicas)
            
            tried_addresses.add(server_address)
            
            # Always create new channel when switching servers
            if not hasattr(self, 'current_server') or server_address != self.current_server:
                self.channel = grpc.insecure_channel(server_address)
                self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
                self.current_server = server_address
                
                
            try:
                response = rpc_method(request)
                return response
            except grpc.RpcError as e:
                retries += 1
                print(f"RPC failed: {e}. Retry {retries}/{self.max_retries}")
                
                if e.code() == grpc.StatusCode.FAILED_PRECONDITION:
                    details = e.details()
                    if "leader is" in details.lower():
                        leader_info = details.split("leader is")[1].strip()
                        self.current_leader = leader_info
                        print(f"Discovered leader: {self.current_leader}")
                        continue  # Skip sleep for leader discovery
                
                if retries <= self.max_retries:  # Only sleep if we'll retry again
                    jitter = random.uniform(0, 0.1 * current_delay)
                    sleep_time = current_delay + jitter
                    time.sleep(sleep_time)
                    current_delay = min(current_delay * 2, 5)
        
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
