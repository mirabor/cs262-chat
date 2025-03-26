import grpc
import logging
from src.protocol.grpc import chat_pb2, chat_pb2_grpc
from src.protocol.grpc import replication_pb2
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

    def _add_replica_metadata(self, context):
        """
        Add metadata about available replicas to the gRPC context.
        This helps clients find alternative replicas if this one fails.
        """
        if not self.replica or not context:
            return

        try:
            # Add leader information if available
            if (
                self.replica.state.leader_id
                and self.replica.state.leader_id != self.replica.state.server_id
            ):
                if self.replica.state.leader_id in self.replica.state.peers:
                    leader_address = self.replica.state.peers[
                        self.replica.state.leader_id
                    ]
                    context.set_trailing_metadata(
                        (
                            ("leader-id", self.replica.state.leader_id),
                            ("leader-address", leader_address),
                        )
                    )

            # Add information about all known replicas
            for server_id, server_info in self.replica.state.servers_info.items():
                if server_id != self.replica.state.server_id:
                    context.add_trailing_metadata(("replica-id", server_id))
                    context.add_trailing_metadata(
                        ("replica-address", server_info.address)
                    )
                    context.add_trailing_metadata(("replica-role", server_info.role))
        except Exception as e:
            logger.error(f"Error adding replica metadata: {e}")

    def _forward_to_leader_if_needed(self, context, method_name, request):
        """
        Forward write requests to the leader if this replica is not the leader.
        """
        # Only forward if we're in a replicated setup and we're not the leader
        if not self.replica or self.replica.state.role == "leader":
            return None

        # Only forward write operations (not reads)
        write_operations = [
            "Signup",
            "Login",
            "DeleteUser",
            "SaveSettings",
            "StartChat",
            "SendChatMessage",
            "DeleteMessages",
        ]
        if method_name not in write_operations:
            return None

        # If we know who the leader is, forward the request
        if (
            self.replica.state.leader_id
            and self.replica.state.leader_id in self.replica.state.peers
        ):
            leader_address = self.replica.state.peers[self.replica.state.leader_id]
            try:
                logger.info(
                    f"Forwarding {method_name} request to leader at {leader_address}"
                )
                with grpc.insecure_channel(leader_address) as channel:
                    stub = chat_pb2_grpc.ChatServiceStub(channel)
                    method = getattr(stub, method_name)
                    return method(request)
            except Exception as e:
                logger.error(f"Error forwarding to leader: {e}")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(f"Leader unavailable: {e}")
                self._add_replica_metadata(context)
                return None

        # If we don't know who the leader is
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(
            "Operation must be performed on leader, but leader is unknown"
        )
        self._add_replica_metadata(context)
        return None

    # ---------------------------- User Management ----------------------------#
    def Signup(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "Signup", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.signup(
            {
                "username": request.username,
                "nickname": request.nickname,
                "password": request.password,
            }
        )

        if not result["success"]:
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)
            return chat_pb2.UserResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.UserResponse(
            success=True, error_message=result.get("error_message", "")
        )

    def Login(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "Login", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.login(
            {"username": request.username, "password": request.password}
        )

        print(f"ChatServicer.Login: returning results: {result}")

        if not result["success"]:
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)
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
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "DeleteUser", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.delete_user(request.username)

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

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

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

        return chat_pb2.MessageLimitResponse(
            limit=result.get("message_limit", 0),
            error_message=result.get("error_message", ""),
        )

    def SaveSettings(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "SaveSettings", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.save_settings(request.username, request.message_limit)

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

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

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

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

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

        return chat_pb2.ChatsResponse(
            chats=chats, error_message=result.get("error_message", "")
        )

    def StartChat(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "StartChat", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.start_chat(request.current_user, request.other_user)
        if not result["success"]:
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)
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

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

        return chat_pb2.MessagesResponse(
            messages=messages, error_message=result.get("error_message", "")
        )

    def SendChatMessage(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "SendChatMessage", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.send_chat_message(
            request.chat_id, request.sender, request.content
        )
        if not result["success"]:
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)
            return chat_pb2.MessageResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.MessageResponse(
            success=True,
            error_message=result.get("error_message", ""),
        )

    def DeleteMessages(self, request, context):
        # Check if we need to forward to leader
        forwarded_response = self._forward_to_leader_if_needed(
            context, "DeleteMessages", request
        )
        if forwarded_response is not None:
            return forwarded_response

        result = self.api.delete_messages(
            request.chat_id, list(request.message_indices), request.current_user
        )

        if result.get("error_message"):
            # Add replica metadata to help client find alternatives
            self._add_replica_metadata(context)

        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )
