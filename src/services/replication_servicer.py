"""
ReplicationService implementation for handling replication and consensus between
server replicas.
"""

import logging
from typing import Optional

from src.protocol.grpc import replication_pb2
from src.protocol.grpc import replication_pb2_grpc


logger = logging.getLogger(__name__)


class ReplicationServicer(replication_pb2_grpc.ReplicationServiceServicer):
    """Implementation of the ReplicationService gRPC service."""

    def __init__(self):
        """Initialize the replication servicer."""
        self.current_term: int = 0
        self.voted_for: Optional[str] = None
        # Will be replaced with proper persistent storage in future
        self.log_entries = []

    def AppendEntries(
        self, request: replication_pb2.EntriesRequest, context
    ) -> replication_pb2.AckResponse:
        """
        Handle AppendEntries RPC from leader.
        For now, just log the operation and return success.
        """
        logger.info(
            "Received AppendEntries from leader %s (term: %d)",
            request.leader_id,
            request.term,
        )
        logger.info("Number of entries: %d", len(request.entries))

        # Update term if leader's term is newer
        if request.term > self.current_term:
            self.current_term = request.term
            self.voted_for = None

        # Simple validation for now - will be enhanced in future implementation
        if request.term < self.current_term:
            return replication_pb2.AckResponse(term=self.current_term, success=False)

        # Log entry details for debugging
        for entry in request.entries:
            logger.debug(
                "Entry - term: %d, index: %d, command size: %d bytes",
                entry.term,
                entry.index,
                len(entry.command),
            )

        return replication_pb2.AckResponse(term=self.current_term, success=True)

    def RequestVote(
        self, request: replication_pb2.VoteRequest, context
    ) -> replication_pb2.VoteResponse:
        """
        Handle RequestVote RPC from candidate.
        For now, implement simple voting logic without log comparison.
        """
        logger.info(
            "Received RequestVote from candidate %s (term: %d)",
            request.candidate_id,
            request.term,
        )

        # Update term if candidate's term is newer
        if request.term > self.current_term:
            self.current_term = request.term
            self.voted_for = None

        # Deny vote if candidate's term is outdated
        if request.term < self.current_term:
            return replication_pb2.VoteResponse(
                term=self.current_term, vote_granted=False
            )

        # Grant vote if we haven't voted this term and candidate's log is up-to-date
        # Note: Proper log comparison will be implemented in future
        vote_granted = self.voted_for is None or self.voted_for == request.candidate_id

        if vote_granted:
            self.voted_for = request.candidate_id
            logger.info("Granted vote to candidate %s", request.candidate_id)
        else:
            logger.info(
                "Denied vote to candidate %s, already voted for %s",
                request.candidate_id,
                self.voted_for,
            )

        return replication_pb2.VoteResponse(
            term=self.current_term, vote_granted=vote_granted
        )
