import grpc
from concurrent import futures
import os
import sys
from typing import Dict, Any

from protocol.grpc import chat_pb2, chat_pb2_grpc
from protocol.config_manager import ConfigManager
from . import api

class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """Implementation of the ChatService service."""
    
    def Signup(self, request, context):
        result = api.signup({
            "username": request.username,
            "nickname": request.nickname,
            "password": request.password
        })
        
        if "error_message" in result:
            return chat_pb2.UserResponse(success=False, error_message=result["error_message"])
        
        return chat_pb2.UserResponse(
            success=True,
            user=chat_pb2.User(
                username=result["username"],
                nickname=result["nickname"],
                message_limit=result.get("message_limit", 0)
            )
        )

    def Login(self, request, context):
        result = api.login({
            "username": request.username,
            "password": request.password
        })
        
        if "error_message" in result:
            return chat_pb2.UserResponse(success=False, error_message=result["error_message"])
        
        return chat_pb2.UserResponse(
            success=True,
            user=chat_pb2.User(
                username=result["username"],
                nickname=result["nickname"],
                message_limit=result.get("message_limit", 0)
            )
        )

    def DeleteUser(self, request, context):
        result = api.delete_user(request.user_id)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", "")
        )

    def GetChats(self, request, context):
        result = api.get_chats(request.user_id)
        chats = []
        for chat in result.get("chats", []):
            chats.append(chat_pb2.Chat(
                chat_id=chat["chat_id"],
                participants=chat["participants"]
            ))
        return chat_pb2.ChatsResponse(
            chats=chats,
            error_message=result.get("error_message", "")
        )

    def GetAllUsers(self, request, context):
        result = api.get_all_users(request.exclude_username)
        users = []
        for user in result.get("users", []):
            users.append(chat_pb2.User(
                username=user["username"],
                nickname=user["nickname"],
                message_limit=user.get("message_limit", 0)
            ))
        return chat_pb2.UsersResponse(
            users=users,
            error_message=result.get("error_message", "")
        )

    def UpdateViewLimit(self, request, context):
        result = api.update_view_limit(request.username, request.new_limit)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", "")
        )

    def GetUserMessageLimit(self, request, context):
        result = api.get_user_message_limit(request.username)
        return chat_pb2.MessageLimitResponse(
            limit=result.get("limit", 0),
            error_message=result.get("error_message", "")
        )

    def SaveSettings(self, request, context):
        result = api.save_settings(request.username, request.message_limit)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", "")
        )

    def StartChat(self, request, context):
        result = api.start_chat(request.current_user, request.other_user)
        if "error_message" in result:
            return chat_pb2.ChatResponse(success=False, error_message=result["error_message"])
        
        return chat_pb2.ChatResponse(
            success=True,
            chat=chat_pb2.Chat(
                chat_id=result["chat_id"],
                participants=result["participants"]
            )
        )

    def DeleteChats(self, request, context):
        result = api.delete_chats(list(request.chat_ids))
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", "")
        )

    def DeleteMessages(self, request, context):
        result = api.delete_messages(request.chat_id, list(request.message_indices), request.current_user)
        return chat_pb2.StatusResponse(
            success=True if not result.get("error_message") else False,
            error_message=result.get("error_message", "")
        )

    def GetMessages(self, request, context):
        result = api.get_messages({
            "chat_id": request.chat_id,
            "current_user": request.current_user
        })
        messages = []
        for msg in result.get("messages", []):
            messages.append(chat_pb2.Message(
                sender=msg["sender"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            ))
        return chat_pb2.MessagesResponse(
            messages=messages,
            error_message=result.get("error_message", "")
        )

    def SendChatMessage(self, request, context):
        result = api.send_chat_message(request.chat_id, request.sender, request.content)
        if "error_message" in result:
            return chat_pb2.MessageResponse(success=False, error_message=result["error_message"])
        
        return chat_pb2.MessageResponse(
            success=True,
            message=chat_pb2.Message(
                sender=result["sender"],
                content=result["content"],
                timestamp=result["timestamp"]
            )
        )

    def GetUsersToDisplay(self, request, context):
        result = api.get_users_to_display(
            request.exclude_username,
            request.search_pattern,
            request.current_page,
            request.users_per_page
        )
        users = []
        for user in result.get("users", []):
            users.append(chat_pb2.User(
                username=user["username"],
                nickname=user["nickname"],
                message_limit=user.get("message_limit", 0)
            ))
        return chat_pb2.UsersDisplayResponse(
            users=users,
            total_pages=result.get("total_pages", 0),
            error_message=result.get("error_message", "")
        )


class GRPCServer:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()
        
        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), self.server)

    def start(self):
        """Start the gRPC server"""
        try:
            # Use same host/port as socket server for now
            address = f"{self.config.host}:{self.config.port}"
            self.server.add_insecure_port(address)
            self.server.start()
            print(f"gRPC Server started on {address}")
            print(f"Maximum workers: 10")
            self.server.wait_for_termination()
        except Exception as e:
            print(f"Error starting gRPC server: {e}")
            self.server.stop(0)
