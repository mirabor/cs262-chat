import functools
import grpc
import logging
from src.protocol.grpc import chat_pb2

logger = logging.getLogger(__name__)


def replicate_to_followers(method_name):
    """
    Decorator to handle replication of write operations to follower nodes.

    Args:
        method_name (str): The name of the method being decorated.
                           Used for logging and forwarding to followers.

    Returns:
        Decorated function that handles replication before executing the original method.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, context, *args, **kwargs):
            # Skip replication if not in replica mode
            if not self.replica:
                return func(self, request, context, *args, **kwargs)

            # Handle replication
            try:
                logger.info(
                    f"Request to {method_name} is of type: {str(type(request))}"
                )
                serialized_request = request.SerializeToString()
                success = self.replica.replicate_to_followers(
                    "ChatServicer", method_name, serialized_request
                )

                if not success:
                    # This happens when we are follower replica, and we
                    # couldn't forward this to a known leader. So client should retry
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details(
                        "Operation must be performed on leader, and we couldn't forward it to a known leader; client should retry"
                    )

                    # Return appropriate response type based on method
                    if method_name in ["Signup", "Login"]:
                        return chat_pb2.UserResponse(
                            success=False,
                            error_message="Contacted followers but couldn't forward",
                        )
                    elif method_name in ["StartChat"]:
                        return chat_pb2.ChatResponse(
                            success=False,
                            error_message="Contacted followers but couldn't forward",
                        )
                    elif method_name in ["SendChatMessage"]:
                        return chat_pb2.MessageResponse(
                            success=False,
                            error_message="Contacted followers but couldn't forward",
                        )
                    else:
                        return chat_pb2.StatusResponse(
                            success=False,
                            error_message="Contacted followers but couldn't forward",
                        )
            except Exception as e:
                logger.error(f"Error replicating to followers in {method_name}: {e}")

                # Return appropriate response type based on method
                if method_name in ["Signup", "Login"]:
                    return chat_pb2.UserResponse(
                        success=False,
                        error_message=f"Error 500: Internal Server Error: {e}",
                    )
                elif method_name in ["StartChat"]:
                    return chat_pb2.ChatResponse(
                        success=False,
                        error_message=f"Error 500: Internal Server Error: {e}",
                    )
                elif method_name in ["SendChatMessage"]:
                    return chat_pb2.MessageResponse(
                        success=False,
                        error_message=f"Error 500: Internal Server Error: {e}",
                    )
                else:
                    return chat_pb2.StatusResponse(
                        success=False,
                        error_message=f"Error 500: Internal Server Error: {e}",
                    )

            logger.info(
                f"ChatServicer.{method_name}: replication handled, now handling locally"
            )
            return func(self, request, context, *args, **kwargs)

        return wrapper

    return decorator
