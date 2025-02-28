import grpc
from protocol.grpc import chat_pb2, chat_pb2_grpc
from .utils import hash_password


class ChatAppLogicGRPC:
    def __init__(self, host="localhost", port=50051):
        """
        Create a gRPC channel and stub.
        Replace host/port with your gRPC server address/port.
        """

        print(f"INFO: grpcLogic, Using gRPC server at {host}:{port}")
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.current_user = None
        self.chat_cache = {}  # mimic the old 'chat_cache' usage
        self.prev_metric_size = {
            "request_size": 0,
            "response_size": 0,
        }

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
        response = self.stub.Signup(request)
        return response.success, response.error_message

    def login(self, username, password):
        """Attempt to log the user in using gRPC."""
        if not username or not password:
            return False, "Username and password are required."

        hashed_password = hash_password(password)
        request = chat_pb2.LoginRequest(username=username, password=hashed_password)

        # Serialize the request to get the byte size
        serialized_request = request.SerializeToString()
        print(
            f"METRIC SerTString: grpc_logic login request size: {len(serialized_request)} bytes"
        )

        serialized_size = (
            request.ByteSize()
        )  # This gets the exact byte size when serialized
        print(f"METRIC ByteSize: grpc_login request size: {serialized_size} bytes")

        response = self.stub.Login(request)

        if not response.success:
            return False, response.error_message or "Login failed"

        # Serialize the response to get its size
        serialized_response = response.SerializeToString()
        print(
            f"METRIC: grpc_logic login response size: {len(serialized_response)} bytes"
        )

        return True, ""

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
        response = self.stub.GetUsersToDisplay(request)
        return response.usernames, response.error_message

    def get_chats(self, user_id):
        """Retrieve all chats for a user."""

        print(f"GetChats called for user_id: {user_id} of type {type(user_id)}")
        request = chat_pb2.GetChatsRequest(user_id=user_id)
        response = self.stub.GetChats(request)

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
        response = self.stub.GetMessages(request)
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

    def start_chat(self, current_user, other_user):
        """Initiate a new chat between two users."""
        request = chat_pb2.StartChatRequest(
            current_user=current_user,
            other_user=other_user,
        )
        response = self.stub.StartChat(request)
        if not response.success:
            return None, response.error_message
        return response.chat.chat_id, ""

    def get_user_message_limit(self, current_user):
        """Get the user's message limit (for UI or logic checks)."""
        request = chat_pb2.GetUserMessageLimitRequest(username=current_user)
        response = self.stub.GetUserMessageLimit(request)
        return response.limit, response.error_message

    def delete_messages(self, chat_id, message_indices, current_user):
        """Send a request to delete specific messages in a chat."""
        request = chat_pb2.DeleteMessagesRequest(
            chat_id=chat_id,
            message_indices=message_indices,
            current_user=current_user,
        )
        response = self.stub.DeleteMessages(request)
        return response.success, response.error_message

    def send_chat_message(self, chat_id, sender, content):
        """Send a new message in a chat."""
        request = chat_pb2.SendMessageRequest(
            chat_id=chat_id,
            sender=sender,
            content=content,
        )
        response = self.stub.SendChatMessage(request)
        return response.success, response.error_message

    def save_settings(self, username, message_limit):
        """Update user settings (message limit, etc.)."""
        request = chat_pb2.SaveSettingsRequest(
            username=username,
            message_limit=message_limit,
        )
        response = self.stub.SaveSettings(request)
        return response.success, response.error_message

    def delete_account(self, current_user):
        """Delete the current user's account."""
        request = chat_pb2.DeleteUserRequest(username=current_user)
        response = self.stub.DeleteUser(request)
        return response.success, response.error_message
