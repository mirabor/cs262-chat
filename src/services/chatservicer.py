import grpc
import logging
from src.protocol.grpc import chat_pb2, chat_pb2_grpc
from src.services.api_manager import APIManager

logger = logging.getLogger(__name__)


class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """Implementation of the ChatService service."""

    def __init__(self, replica=None):
        """
        Initialize the ChatServicer instance.

        Args:
            replica (ReplicaNode): The replica node instance.
                    When running in standalone mode (no replication),
                    this parameter is None.
        """
        self.replica = replica
        db_name = f"database_{replica.state.server_id}.db" if replica else "database.db"

        print(f"Using database: {db_name}")
        self.api = APIManager(db_file=db_name)

    # ---------------------------- User Management ----------------------------#
    def Signup(self, request, context):

        if self.replica:
            try:
                logger.info("Request to signup is of type: %s", str(type(request)))
                serialized_request = request.SerializeToString()
                success = self.replica.replicate_to_followers(
                    "ChatServicer", "Signup", serialized_request
                )

                if not success:  # this happens when we are follower replica, and we
                    # couldn't forward this to a known leader. So client should retry
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details(
                        "Operation must be performed on leader, and we couldn't forward it to a known leader; client should retry"
                    )
                    return chat_pb2.UserResponse(
                        success=False,
                        error_message="Contacted followers but couldn't forward",
                    )
            except Exception as e:
                logger.error(f"Error replicating to followers: {e}")
                return chat_pb2.UserResponse(
                    success=False,
                    error_message=f"Error 500: Internal Server Error: {e}",
                )

            logger.info(
                "ChatServicer.Signup: replication handled, now handling locally"
            )

        result = self.api.signup(
            {
                "username": request.username,
                "nickname": request.nickname,
                "password": request.password,
            }
        )

        if not result["success"]:
            return chat_pb2.UserResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.UserResponse(
            success=True, error_message=result.get("error_message", "")
        )

    def Login(self, request, context):
        result = self.api.login(
            {"username": request.username, "password": request.password}
        )

        print(f"ChatServicer.Login: returning results: {result}")

        if not result["success"]:
            return chat_pb2.UserResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.UserResponse(
            success=result["success"],
            error_message=result.get("error_message", ""),
            user_id=result["user_id"],
            nickname=result["nickname"],
            view_limit=result.get("view_limit", 0),
        )

    def DeleteUser(self, request, context):
        result = self.api.delete_user(request.username)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )

    def GetUserMessageLimit(self, request, context):
        # This is a read operation, so we don't need to forward to leader
        result = self.api.get_user_message_limit(request.username)
        print(
            f"ChatServicer.GetUserMessageLimit: results from api: {result} and type of message limit: {type(result.get('message_limit', 0))}"
        )

        return chat_pb2.MessageLimitResponse(
            limit=result.get("message_limit", 0),
            error_message=result.get("error_message", ""),
        )

    def SaveSettings(self, request, context):
        result = self.api.save_settings(request.username, request.message_limit)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )

    def GetUsersToDisplay(self, request, context):
        # This is a read operation, so we don't need to forward to leader
        result = self.api.get_users_to_display(
            request.exclude_username,
            request.search_pattern,
            request.current_page,
            request.users_per_page,
        )

        return chat_pb2.UsersDisplayResponse(
            usernames=result.get("users", []),
            total_pages=result.get("total_pages", 0),
            error_message=result.get("error_message", ""),
        )

    # ---------------------------- Chat Management ----------------------------#
    def GetChats(self, request, context):
        # This is a read operation, so we don't need to forward to leader
        result = self.api.get_chats(request.user_id)
        print(f"ChatServicer.GetChats: results from api: {result}")
        chats = []
        for chat in result.get("chats", []):
            chats.append(
                chat_pb2.Chat(
                    chat_id=chat["chat_id"],
                    other_user=chat["other_user"],
                    unread_count=chat["unread_count"],
                )
            )

        return chat_pb2.ChatsResponse(
            chats=chats, error_message=result.get("error_message", "")
        )

    def StartChat(self, request, context):
        result = self.api.start_chat(request.current_user, request.other_user)
        if not result["success"]:
            return chat_pb2.ChatResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.ChatResponse(
            success=True,
            chat=chat_pb2.Chat(
                chat_id=result["chat_id"],
            ),
        )

    def GetMessages(self, request, context):
        # This is a read operation, so we don't need to forward to leader
        result = self.api.get_messages(
            {"chat_id": request.chat_id, "current_user": request.current_user}
        )
        messages = []
        for msg in result.get("messages", []):
            messages.append(
                chat_pb2.Message(
                    sender=msg["sender"],
                    content=msg["content"],
                    timestamp=msg["timestamp"],
                )
            )
        return chat_pb2.MessagesResponse(
            messages=messages, error_message=result.get("error_message", "")
        )

    def SendChatMessage(self, request, context):
        result = self.api.send_chat_message(
            request.chat_id, request.sender, request.content
        )
        if not result["success"]:
            return chat_pb2.MessageResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.MessageResponse(
            success=True,
            error_message=result.get("error_message", ""),
        )

    def DeleteMessages(self, request, context):
        result = self.api.delete_messages(
            request.chat_id, list(request.message_indices), request.current_user
        )
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )
