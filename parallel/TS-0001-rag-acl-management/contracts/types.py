# Shared Type Contracts for TS-0001: RAG ACL Management
# These types define the interface contract between parallel tasks
# DO NOT import from this file in production code - this is documentation only

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Visibility(str, Enum):
    """Document visibility levels.

    Determines who can access a document/chunk in search results.
    """
    PRIVATE = "private"    # Only owner can access
    SHARED = "shared"      # Owner + explicitly granted principals
    INTERNAL = "internal"  # All authenticated users in tenant
    PUBLIC = "public"      # Anyone (including anonymous)


class QueryACLContext(BaseModel):
    """ACL context provided with every search query.

    Built by the host application (Django) from authenticated user info.
    Required for all search operations unless bypass_acl=True.
    """
    principal_id: str
    """The ID of the user/service making the query."""

    member_of_groups: list[str] = []
    """Group IDs the principal belongs to (resolved by host app)."""

    tenant_id: Optional[str] = None
    """Tenant ID for multi-tenant isolation. None for single-tenant."""

    bypass_acl: bool = False
    """Skip ACL filtering (system operations only). Should be logged/audited."""

    @classmethod
    def system_context(cls) -> "QueryACLContext":
        """Create a system context that bypasses ACL checks."""
        return cls(principal_id="system", bypass_acl=True)


class ACLFilterSpec(BaseModel):
    """Specification for ACL filtering in vector store queries.

    For pgvector, this translates directly to SQL WHERE clauses.
    """
    principal_id: str
    group_ids: list[str]
    tenant_id: Optional[str]
    include_public: bool = True
    include_internal: bool = True

    def to_sql_conditions(self) -> tuple[str, list]:
        """Generate SQL WHERE clause for pgvector ACL filtering.

        Returns:
            Tuple of (SQL string with $N placeholders, parameters list)

        Example output:
            ("(owner_id = $1 OR visibility IN ($2, $3) OR $4 = ANY(shared_with_users))",
             ["user-123", "public", "internal", "user-123"])
        """
        ...  # Implementation in task-001


# Document ACL Fields (added to existing Document model)
class DocumentACLFields(BaseModel):
    """ACL fields to be added to the Document model in schemas.py"""
    owner_id: str
    """Principal ID who owns this document. Required."""

    visibility: Visibility = Visibility.PRIVATE
    """Access visibility level. Defaults to PRIVATE."""

    shared_with_users: list[str] = []
    """User IDs with direct access (for SHARED visibility)."""

    shared_with_groups: list[str] = []
    """Group IDs with access (for SHARED visibility)."""

    tenant_id: Optional[str] = None
    """Tenant ID for multi-tenant deployments."""


# Chunk ACL Fields (denormalized from Document)
class ChunkACLFields(BaseModel):
    """ACL fields to be added to the Chunk model in schemas.py

    These are denormalized from the parent Document for query performance.
    Use Chunk.from_document() to copy ACL fields from parent.
    """
    owner_id: str
    visibility: Visibility
    shared_with_users: list[str] = []
    shared_with_groups: list[str] = []
    tenant_id: Optional[str] = None
