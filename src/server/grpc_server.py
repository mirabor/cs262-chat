import grpc
from concurrent import futures
from typing import Dict, Any, List

from protocol.grpc import chat_pb2, chat_pb2_grpc, replication_pb2, replication_pb2_grpc
from protocol.config_manager import ConfigManager
from src.services import api
import logging

from src.server.replication_servicer import ReplicationServicer

logger = logging.getLogger(__name__)

class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """Implementation of the ChatService service."""

    # ---------------------------- User Management ----------------------------#
    def Signup(self, request, context):
        result = api.signup(
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
        result = api.login({"username": request.username, "password": request.password})

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
        result = api.delete_user(request.username)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )

    def GetUserMessageLimit(self, request, context):
        result = api.get_user_message_limit(request.username)
        print(
            f"ChatServicer.GetUserMessageLimit: results from api: {result} and type of message limit: {type(result.get('message_limit', 0))}"
        )
        return chat_pb2.MessageLimitResponse(
            limit=result.get("message_limit", 0),
            error_message=result.get("error_message", ""),
        )

    def SaveSettings(self, request, context):
        result = api.save_settings(request.username, request.message_limit)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )

    def GetUsersToDisplay(self, request, context):
        result = api.get_users_to_display(
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
        result = api.get_chats(request.user_id)
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
        result = api.start_chat(request.current_user, request.other_user)
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
        result = api.get_messages(
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
        result = api.send_chat_message(request.chat_id, request.sender, request.content)
        if not result["success"]:
            return chat_pb2.MessageResponse(
                success=False, error_message=result["error_message"]
            )

        return chat_pb2.MessageResponse(
            success=True,
            error_message=result.get("error_message", ""),
        )

    def DeleteMessages(self, request, context):
        result = api.delete_messages(
            request.chat_id, list(request.message_indices), request.current_user
        )
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", ""),
        )

class GRPCServer:
    def __init__(self, host: str, peers: List[str]):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()

        self.host = host
        self.peers = peers

        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), self.server)
        replication_pb2_grpc.add_ReplicationServiceServicer_to_server(ReplicationServicer(), self.server)

    def connect_to_peers(self):
        """Connect to peer servers and confirm connections."""
        for peer in self.peers:
            if peer == self.host:
                continue  # Skip self

            channel = grpc.insecure_channel(peer)
            stub = replication_pb2_grpc.ReplicationServiceStub(channel)
            try:
                response = stub.ConfirmConnection(replication_pb2.PeerAddress(peer_address=self.host))
                if response.success:
                    logger.info(f"Connection to peer {peer} confirmed.")
                else:
                    logger.warning(f"Failed to confirm connection to peer {peer}.")
            except grpc.RpcError as e:
                logger.error(f"Failed to connect to peer {peer}: {e}")

    def start(self):
        """Start the gRPC server and connect to peers."""
        try:
            self.server.add_insecure_port(self.host)
            self.server.start()
            logger.info(f"gRPC Server started on {self.host}")
            logger.info(f"Maximum workers: 10")

            # Connect to peers
            self.connect_to_peers()

            self.server.wait_for_termination()
        except Exception as e:
            logger.error(f"Error starting gRPC server: {e}")
            self.server.stop(0)