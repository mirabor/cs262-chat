from .utils import hash_password

class ChatAppLogic:
    def __init__(self, client):
        self.current_user = None
        self.client = client
        self.filtered_users = []
        self.chat_cache = {}

        if not self.client.connect():
            print("Failed to connect to the server.")

    def delete_chats(self, chat_ids):
        """Send a request to delete chats."""
        self.client.send_message({
            "action": "delete_chats",
            "chat_ids": chat_ids
        })
        response = self.client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def delete_messages(self, chat_id, message_indices, current_user):
        # TODO: error handling for messages trying to be deleted if not from that user
        unauthorized_attempt = False
        self.client.send_message({
            "action": "delete_messages",
            "chat_id": chat_id,
            "message_indices": message_indices,
            "current_user": current_user
        })
        response = self.client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def login(self, username, password):
        if not username or not password:
            return False, "Username and password are required."

        hashed_password = hash_password(password)

        # Attempt to send login message
        if not self.client.send_message({
            "action": "login",
            "username": username,
            "password": hashed_password
        }):
            return False, "Error: logic.login Failed to send message to server"

        # Get server response
        response = self.client.receive_message()
        
        # If login failed, ensure we're disconnected
        if not response.get("success", False):
            return False, response.get("error_message", "Invalid username or password")
            
        return response.get("success", False), response.get("error_message", "500 Internal Server Error")

    def signup(self, username, nickname, password):
        if not username or not nickname or not password:
            return False, "All fields are required."
        
        hashed_password = hash_password(password)

        # Send the signup request to the server
        self.client.send_message({
            "action": "signup",
            "username": username,
            "nickname": nickname,
            "password": hashed_password
        })

        # Receive the server's response
        response = self.client.receive_message()
        return response.get("success", False), response.get("error_message", "")
    
    def save_settings(self, username, message_limit):
        self.client.send_message({
            "action": "save_settings",
            "username": username,
            "message_limit": message_limit
        })
        response = self.client.receive_message()
        print("savings saved, response: ", response)
        return response.get("success"), response.get("error_message", "")

    def start_chat(self, current_user, other_user):
       """Send a request to start a new chat."""
       self.client.send_message({
            "action": "start_chat",
            "current_user": current_user,
            "other_user": other_user
        })
       response = self.client.receive_message()
       return response.get("chat_id"), response.get("error_message", "")

    def get_users_to_display(
        self, current_user, search_pattern, current_page, users_per_page
    ):
        print(f"Sending request with page={current_page}, users_per_page={users_per_page}")
        # if current_page is None:
        #     current_page = 1  # Default to the first page
        # if users_per_page is None:
        #     users_per_page = 10

        self.client.send_message({
    "action": "get_users_to_display",
    "current_user": current_user,
    "search_pattern": search_pattern,
    "page": current_page,
    "users_per_page": users_per_page
        })
        response = self.client.receive_message()
        return response.get("users", []), response.get("error_message", "")

    def delete_account(self, current_user):
        # Remove user from all chats

        # NOTE: (DOCS) This means, users who interacted with with curr user
        # will lose all chats/messages
        self.client.send_message({
            "action": "delete_user",
            "username": current_user
        })
        response = self.client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def get_user_message_limit(self, current_user):
        self.client.send_message({
            "action": "get_user_message_limit",
            "username": current_user
        })
        response = self.client.receive_message()
        return response.get("message_limit"), response.get("error_message", "")
    
    def get_chats(self, user_id):
        """Request chat history for a user."""
        self.client.send_message({
            "action": "get_chats",
            "user_id": user_id
        })
        response = self.client.receive_message()
        if response.get("success"):
            chats = response.get("chats", [])
            # Update the chat cache, for quick access (esp. on ChatPage)
            # to get some metadata (e.g. other user's name  )
            for chat in chats:
                print("chat: ", chat)
                self.chat_cache[chat["chat_id"]] = chat

            return response.get("chats", []), response.get("error_message", "")
        else:
            return [], response.get("error_message", "Failed to fetch chats")
        
    def get_other_user_in_chat(self, chat_id):
        """Get the other user in the chat."""
        return self.chat_cache.get(chat_id, {}).get("other_user")

    def get_messages(self, chat_id, current_user):
        """Get messages for a chat."""
        self.client.send_message({
            "action": "get_messages",
            "chat_id": chat_id,
            "current_user": current_user
        })
        response = self.client.receive_message()
        print("response: is what we r getting and giving to display ", response)
        return response.get("messages", []), response.get("error_message", "")
    
    def send_chat_message(self, chat_id, sender, content):
        """Send a message in a chat."""
        self.client.send_message({
            "action": "send_chat_message",
            "chat_id": chat_id,
            "sender": sender,
            "content": content
        })
        response = self.client.receive_message()
        return response.get("success", False), response.get("error_message", "")
