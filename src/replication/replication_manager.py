import concurrent.futures
import grpc
import logging
from typing import Dict, List

import src.protocol.grpc.replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc

logger = logging.getLogger(__name__)


class ReplicationManager:
    """
    Manages replication of operations to followers.
    """

    def __init__(self, state):
        self.state = state

    def replicate_to_followers(
        self, service_name, method_name, serialized_request, operation_id
    ):
        """Replicate an operation to all followers."""
        if self.state.role != "leader":
            logger.warning("Only the leader can replicate operations")
            return

        successes = 1  # Count self as success
        futures = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for peer_id, peer_address in self.state.peers.items():
                futures.append(
                    executor.submit(
                        self.replicate_to_one_follower,
                        peer_id,
                        peer_address,
                        service_name,
                        method_name,
                        serialized_request,
                        operation_id,
                    )
                )

            for future in concurrent.futures.as_completed(futures):
                try:
                    if future.result():
                        successes += 1
                except Exception as e:
                    logger.error(f"Error in replication: {str(e)}")

        # Check if we have majority
        if successes > (len(self.state.peers) + 1) / 2:
            logger.info(
                f"Operation {operation_id} successfully replicated to majority of followers"
            )
        else:
            logger.warning(
                f"Failed to replicate operation {operation_id} to majority of followers"
            )

    def replicate_to_one_follower(
        self,
        peer_id,
        peer_address,
        service_name,
        method_name,
        serialized_request,
        operation_id,
    ):
        """Replicate an operation to a single follower."""
        try:
            with grpc.insecure_channel(peer_address) as channel:
                stub = replication_grpc.ReplicationServiceStub(channel)

                request = replication.OperationRequest(
                    service_name=service_name,
                    method_name=method_name,
                    serialized_request=serialized_request,
                    operation_id=operation_id,
                    server_id=self.state.server_id,
                    term=self.state.term,
                )

                response = stub.ReplicateOperation(request, timeout=2)

                if response.success:
                    logger.info(
                        f"Successfully replicated {service_name}.{method_name} to {peer_id}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to replicate {service_name}.{method_name} to {peer_id}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error replicating to {peer_id}: {str(e)}")
            return False

    def log_operation(self, service, method, parameters, result, operation_id):
        """Log an operation to the operation log."""
        self.state.operation_log.append(
            {
                "service": service,
                "method": method,
                "parameters": parameters,
                "result": result,
                "id": operation_id,
                "term": self.state.term,
            }
        )

    def get_next_operation_id(self):
        """Get the next operation ID."""
        self.state.last_operation_id += 1
        return self.state.last_operation_id
