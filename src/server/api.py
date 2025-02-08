from .db_manager import DBManager

db_manager = DBManager()

def signup(input_data):
    """Sign up a new user. assume password encrypted"""
    return db_manager.add_user(
        username=input_data["username"],
        nickname=input_data["nickname"],
        password=input_data["password"]
    )

def login(login_data):
    """Log in a user. assume password encrypted already"""
    return db_manager.login(login_data)

def delete_user(user_id):
    """Delete a user."""
    return db_manager.delete_user(user_id)

def get_chats(user_id):
    """Get all chats involving a user."""
    return db_manager.get_chats(user_id)

def get_all_users(exclude_username=None):
    """Get all users except the excluded one."""
    return db_manager.get_all_users(exclude_username)

def update_view_limit(username, new_limit):
    """Update the message view limit for a user."""
    return db_manager.update_view_limit(username, new_limit)

if __name__ == "__main__":
    db_manager.initialize_database()

    # Sign up a new user
    signup_response = signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    })
    print("Signup Response:", signup_response)

    # Log in the user
    login_response = login({
        "username": "test_user",
        "password": "password123"
    })
    print("Login Response:", login_response)

    # Update the message view limit
    update_response = update_view_limit("test_user", 10)
    print("Update View Limit Response:", update_response)

    # Get all users
    users_response = get_all_users()
    print("All Users:", users_response)

    # Get chats for a user
    chats_response = get_chats(1)
    print("Chats for User 1:", chats_response)

    # Delete a user
    delete_response = delete_user(1)
    print("Delete User Response:", delete_response)