import grpc
import logging
import time
from src.protocol.grpc import chat_pb2, chat_pb2_grpc
from src.protocol.grpc import replication_pb2, replication_pb2_grpc
from .utils import hash_password
from functools import wraps

# Configuration parameters
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

logger = logging.getLogger(__name__)


def with_retry_and_logging(method_name):
    """
    Decorator to standardize error handling, logging, and retries for gRPC methods.
    
    Args:
        method_name (str): The name of the gRPC method being called
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < MAX_RETRIES:
                try:
                    logger.debug(f"Executing {method_name} (attempt {attempt+1}/{MAX_RETRIES})")
                    result = func(self, *args, **kwargs)
                    logger.debug(f"Successfully executed {method_name}")
                    return result
                except grpc.RpcError as e:
                    last_exception = e
                    logger.warning(f"{method_name} failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    attempt += 1
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error in {method_name}: {e}", exc_info=True)
                    break
            
            # If we get here, all retries failed or an unexpected error occurred
            if isinstance(last_exception, grpc.RpcError):
                return self._handle_grpc_error(method_name, last_exception)
            else:
                return False, f"Failed to {method_name}: {str(last_exception)}"
        return wrapper
    return decorator


class ChatAppLogicGRPC:
    def __init__(self, host="localhost", port=50051):
        """
        Create a gRPC channel and stub.
        Replace host/port with your gRPC server address/port.
        """

        logger.info(f"Using gRPC server at {host}:{port}")
        self.primary_address = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.primary_address)
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        
        # For replication and failover
        self.known_replicas = {self.primary_address: True}  # Map of address -> is_available
        self.current_leader = None
        self.replication_stub = replication_pb2_grpc.ReplicationServiceStub(self.channel)
        
        # Try to get network state to discover other replicas
        self._discover_replicas()
        
        self.current_user = None
        self.chat_cache = {}  # mimic the old 'chat_cache' usage
        self.prev_metric_size = {
            "request_size": 0,
            "response_size": 0,
        }

    def _discover_replicas(self):
        """Discover other replicas in the network."""
        try:
            request = replication_pb2.NetworkStateRequest(server_id="client")
            response = self.replication_stub.GetNetworkState(request)
            
            # Update known replicas
            for server in response.servers:
                self.known_replicas[server.address] = True
                if server.role == "leader":
                    self.current_leader = server.address
                    
            logger.info(f"Discovered replicas: {list(self.known_replicas.keys())}")
            logger.info(f"Current leader: {self.current_leader}")
            
        except grpc.RpcError as e:
            logger.warning(f"Failed to discover replicas: {e}")
    
    def _execute_with_failover(self, method_name, request, retry_count=MAX_RETRIES):
        """Execute a gRPC call with failover to other replicas if the current one fails."""
        # Try the current connection first
        try:
            method = getattr(self.stub, method_name)
            return method(request)
        except grpc.RpcError as e:
            logger.warning(f"Request to {self.primary_address} failed: {e}")
            
            # Mark current server as unavailable
            self.known_replicas[self.primary_address] = False
            
            # Try other known replicas
            for address in list(self.known_replicas.keys()):
                if address == self.primary_address or not self.known_replicas[address]:
                    continue
                    
                logger.info(f"Trying failover to replica at {address}")
                try:
                    # Create a new channel and stub for this replica
                    with grpc.insecure_channel(address) as channel:
                        stub = chat_pb2_grpc.ChatServiceStub(channel)
                        method = getattr(stub, method_name)
                        response = method(request)
                        
                        # If successful, update our primary connection
                        self.primary_address = address
                        self.channel.close()
                        self.channel = grpc.insecure_channel(address)
                        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
                        self.replication_stub = replication_pb2_grpc.ReplicationServiceStub(self.channel)
                        
                        # Try to discover more replicas from this working node
                        self._discover_replicas()
                        
                        return response
                except grpc.RpcError as inner_e:
                    logger.warning(f"Failover to {address} failed: {inner_e}")
                    self.known_replicas[address] = False
            
            # If we get here, all known replicas failed
            raise Exception(f"All known replicas are unavailable. Last error: {e}")
    
    def _handle_grpc_error(self, operation, error):
        """Handle gRPC errors in a standardized way."""
        if error.code() == grpc.StatusCode.UNAVAILABLE:
            return False, f"Service unavailable: {error.details()}"
        elif error.code() == grpc.StatusCode.NOT_FOUND:
            return False, f"Resource not found"
        elif error.code() == grpc.StatusCode.PERMISSION_DENIED:
            return False, f"Permission denied"
        else:
            return False, f"Failed to {operation}: {error.details() or str(error)}"

    @with_retry_and_logging("signup")
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
        
        response = self._execute_with_failover("Signup", request)
        return response.success, response.error_message

    @with_retry_and_logging("login")
    def login(self, username, password):
        """Attempt to log the user in using gRPC."""
        if not username or not password:
            return False, "Username and password are required."

        hashed_password = hash_password(password)
        request = chat_pb2.LoginRequest(username=username, password=hashed_password)

        # Serialize the request to get the byte size
        serialized_request = request.SerializeToString()
        logger.debug(f"gRPC login request size: {len(serialized_request)} bytes")

        serialized_size = request.ByteSize()  # This gets the exact byte size when serialized
        logger.debug(f"gRPC login request ByteSize: {serialized_size} bytes")

        response = self._execute_with_failover("Login", request)

        if not response.success:
            return False, response.error_message or "Login failed"

        # Serialize the response to get its size
        serialized_response = response.SerializeToString()
        logger.debug(f"gRPC login response size: {len(serialized_response)} bytes")
        
        # Store current user
        self.current_user = username

        return True, ""

    @with_retry_and_logging("get_users")
    def get_users_to_display(self, current_user, search_pattern, current_page, users_per_page):
        """Retrieve a paginated list of users."""
        request = chat_pb2.GetUsersToDisplayRequest(
            exclude_username=current_user,
            search_pattern=search_pattern or "",
            current_page=current_page or 1,
            users_per_page=users_per_page or 10,
        )
        response = self._execute_with_failover("GetUsersToDisplay", request)
        return response.usernames, response.error_message

    @with_retry_and_logging("get_chats")
    def get_chats(self, user_id):
        """Retrieve all chats for a user."""
        logger.debug(f"GetChats called for user_id: {user_id} of type {type(user_id)}")
        request = chat_pb2.GetChatsRequest(user_id=user_id)
        
        response = self._execute_with_failover("GetChats", request)

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
            logger.debug(f"Added chat to cache: {chat_info}")

        return chats, ""

    def get_other_user_in_chat(self, chat_id):
        other_user = self.chat_cache.get(chat_id, {}).get("other_user")
        logger.debug(f"GetOtherUserInChat called for chat_id: {chat_id}, got other user: {other_user}")
        return other_user

    @with_retry_and_logging("get_messages")
    def get_messages(self, chat_id, current_user):
        """Retrieve messages for a given chat."""
        request = chat_pb2.GetMessagesRequest(
            chat_id=chat_id,
            current_user=current_user,
        )
        logger.debug(f"Get message request: id {request.chat_id} and user {request.current_user}")
        
        response = self._execute_with_failover("GetMessages", request)
        if response.error_message:
            return [], response.error_message

        logger.debug(f"Got messages response: {response}")
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

    @with_retry_and_logging("start_chat")
    def start_chat(self, current_user, other_user):
        """Initiate a new chat between two users."""
        request = chat_pb2.StartChatRequest(
            current_user=current_user,
            other_user=other_user,
        )
        response = self._execute_with_failover("StartChat", request)
        if not response.success:
            return None, response.error_message
        return response.chat.chat_id, ""

    @with_retry_and_logging("get_user_message_limit")
    def get_user_message_limit(self, current_user):
        """Get the user's message limit (for UI or logic checks)."""
        request = chat_pb2.GetUserMessageLimitRequest(username=current_user)
        response = self._execute_with_failover("GetUserMessageLimit", request)
        return response.limit, response.error_message

    @with_retry_and_logging("delete_messages")
    def delete_messages(self, chat_id, message_indices, current_user):
        """Send a request to delete specific messages in a chat."""
        request = chat_pb2.DeleteMessagesRequest(
            chat_id=chat_id,
            message_indices=message_indices,
            current_user=current_user,
        )
        response = self._execute_with_failover("DeleteMessages", request)
        return response.success, response.error_message

    @with_retry_and_logging("send_chat_message")
    def send_chat_message(self, chat_id, sender, content):
        """Send a new message in a chat."""
        request = chat_pb2.SendMessageRequest(
            chat_id=chat_id,
            sender=sender,
            content=content,
        )
        response = self._execute_with_failover("SendChatMessage", request)
        return response.success, response.error_message

    @with_retry_and_logging("save_settings")
    def save_settings(self, username, message_limit):
        """Update user settings (message limit, etc.)."""
        request = chat_pb2.SaveSettingsRequest(
            username=username,
            message_limit=message_limit,
        )
        response = self._execute_with_failover("SaveSettings", request)
        return response.success, response.error_message

    @with_retry_and_logging("delete_account")
    def delete_account(self, current_user):
        """Delete the current user's account."""
        request = chat_pb2.DeleteUserRequest(username=current_user)
        response = self._execute_with_failover("DeleteUser", request)
        return response.success, response.error_message