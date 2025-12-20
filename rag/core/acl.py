"""ACL (Access Control List) core module for RAG system.

This module provides the foundational types for implementing access control
in the RAG vector search system. It defines visibility levels, query contexts,
and SQL filter generation for pgvector-based ACL filtering.

Key components:
- Visibility: Enum defining document access levels
- QueryACLContext: Context object built from authenticated user info
- ACLFilterSpec: Specification for generating SQL WHERE clauses
"""

from enum import Enum

from pydantic import BaseModel, Field


class Visibility(str, Enum):
    """Document visibility levels.

    Determines who can access a document/chunk in search results.
    Inherits from str to ensure JSON serialization compatibility.

    Attributes:
        PRIVATE: Only the document owner can access
        SHARED: Owner + explicitly granted principals (users/groups)
        INTERNAL: All authenticated users within the same tenant
        PUBLIC: Anyone, including anonymous users
    """
    PRIVATE = "private"
    SHARED = "shared"
    INTERNAL = "internal"
    PUBLIC = "public"


class QueryACLContext(BaseModel):
    """ACL context provided with every search query.

    Built by the host application (Django) from authenticated user information.
    Required for all search operations unless bypass_acl=True (system context).

    This context is used to generate ACL filter specifications that ensure
    users only see documents they have permission to access.

    Attributes:
        principal_id: The ID of the user/service making the query (required)
        member_of_groups: List of group IDs the principal belongs to
        tenant_id: Tenant ID for multi-tenant isolation (None for single-tenant)
        bypass_acl: Skip ACL filtering for system operations (should be logged/audited)
    """
    principal_id: str = Field(
        ...,
        description="The ID of the user/service making the query"
    )
    member_of_groups: list[str] = Field(
        default_factory=list,
        description="Group IDs the principal belongs to (resolved by host app)"
    )
    tenant_id: str | None = Field(
        default=None,
        description="Tenant ID for multi-tenant isolation. None for single-tenant."
    )
    bypass_acl: bool = Field(
        default=False,
        description="Skip ACL filtering (system operations only). Should be logged/audited."
    )

    @classmethod
    def system_context(cls) -> "QueryACLContext":
        """Create a system context that bypasses ACL checks.

        Returns a QueryACLContext with bypass_acl=True, allowing system-level
        operations to access all documents regardless of ACL settings.

        Use this sparingly and ensure all uses are properly logged/audited.

        Returns:
            QueryACLContext: A context configured for system-level access
        """
        return cls(principal_id="system", bypass_acl=True)


class ACLFilterSpec(BaseModel):
    """Specification for ACL filtering in vector store queries.

    For pgvector, this translates directly to SQL WHERE clauses that filter
    results based on ownership, visibility, and explicit sharing grants.

    The filter logic implements the following access rules:
    1. User is the document owner, OR
    2. Document visibility is PUBLIC/INTERNAL (based on flags), OR
    3. User is explicitly granted access via shared_with_users, OR
    4. User belongs to a group in shared_with_groups

    Additionally, tenant isolation is enforced (when tenant_id is set).

    Attributes:
        principal_id: The user/service ID performing the query
        group_ids: List of group IDs the principal belongs to
        tenant_id: Tenant ID for isolation (None allows untenanted documents)
        include_public: Whether to include PUBLIC visibility documents
        include_internal: Whether to include INTERNAL visibility documents
    """
    principal_id: str = Field(
        ...,
        description="The user/service ID performing the query"
    )
    group_ids: list[str] = Field(
        default_factory=list,
        description="List of group IDs the principal belongs to"
    )
    tenant_id: str | None = Field(
        default=None,
        description="Tenant ID for isolation (None allows untenanted documents)"
    )
    include_public: bool = Field(
        default=True,
        description="Whether to include PUBLIC visibility documents"
    )
    include_internal: bool = Field(
        default=True,
        description="Whether to include INTERNAL visibility documents"
    )

    def to_sql_conditions(self) -> tuple[str, list]:
        """Generate SQL WHERE clause for pgvector ACL filtering.

        Creates a parameterized SQL WHERE clause that implements the ACL
        filtering logic. Uses PostgreSQL-style positional parameters ($1, $2, etc.)
        to prevent SQL injection.

        The generated SQL enforces:
        - Ownership checks (owner_id = principal_id)
        - Visibility-based access (PUBLIC, INTERNAL based on flags)
        - Explicit user sharing (principal_id in shared_with_users)
        - Group-based sharing (any group_id in shared_with_groups)
        - Tenant isolation (with NULL handling for untenanted documents)

        Returns:
            tuple[str, list]: A tuple containing:
                - SQL WHERE clause with $N parameter placeholders
                - List of parameter values in order

        Example:
            >>> spec = ACLFilterSpec(
            ...     principal_id="user-123",
            ...     group_ids=["group-1", "group-2"],
            ...     tenant_id="tenant-1"
            ... )
            >>> sql, params = spec.to_sql_conditions()
            >>> print(sql)
            ((tenant_id IS NULL OR tenant_id = $1) AND (owner_id = $2 OR ...))
            >>> print(params)
            ['tenant-1', 'user-123', ...]
        """
        params = []
        param_index = 1

        # Tenant isolation (always enforced if tenant_id is set)
        # Allow access to untenanted documents (tenant_id IS NULL) or same tenant
        if self.tenant_id is not None:
            params.append(self.tenant_id)
            tenant_condition = f"(tenant_id IS NULL OR tenant_id = ${param_index})"
            param_index += 1
        else:
            # No tenant filtering - allow all
            tenant_condition = "TRUE"

        # Build OR conditions for access grants
        access_conditions = []

        # 1. Owner access: user owns the document
        params.append(self.principal_id)
        access_conditions.append(f"owner_id = ${param_index}")
        param_index += 1

        # 2. Visibility-based access
        visibility_values = []
        if self.include_public:
            visibility_values.append("public")
        if self.include_internal:
            visibility_values.append("internal")

        if visibility_values:
            # Add each visibility value as a separate parameter
            visibility_placeholders = []
            for vis_value in visibility_values:
                params.append(vis_value)
                visibility_placeholders.append(f"${param_index}")
                param_index += 1
            visibility_condition = f"visibility IN ({', '.join(visibility_placeholders)})"
            access_conditions.append(visibility_condition)

        # 3. Explicit user sharing: principal_id in shared_with_users array
        params.append(self.principal_id)
        access_conditions.append(f"${param_index} = ANY(shared_with_users)")
        param_index += 1

        # 4. Group-based sharing: any of user's groups in shared_with_groups array
        if self.group_ids:
            for group_id in self.group_ids:
                params.append(group_id)
                access_conditions.append(f"${param_index} = ANY(shared_with_groups)")
                param_index += 1

        # Combine tenant isolation AND access grants
        access_clause = " OR ".join(access_conditions)
        full_condition = f"({tenant_condition} AND ({access_clause}))"

        return full_condition, params
