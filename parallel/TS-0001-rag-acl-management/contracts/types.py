from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Visibility(str, Enum):
    """Document visibility levels."""
    PRIVATE = "private"
    SHARED = "shared"
    INTERNAL = "internal"
    PUBLIC = "public"


class QueryACLContext(BaseModel):
    """ACL context provided with every search query."""
    principal_id: str
    member_of_groups: list[str] = []
    tenant_id: Optional[str] = None
    bypass_acl: bool = False

    @classmethod
    def system_context(cls) -> "QueryACLContext":
        return cls(principal_id="system", bypass_acl=True)


class ACLFilterSpec(BaseModel):
    """Specification for ACL filtering in SQL queries."""
    principal_id: str
    group_ids: list[str]
    tenant_id: Optional[str]
    include_public: bool = True
    include_internal: bool = True

    def to_sql_conditions(self) -> tuple[str, list]:
        """Generate SQL WHERE clause for pgvector ACL filtering."""
        ...


# Schema ACL fields (to be added to Document and Chunk)
ACL_FIELDS = {
    "owner_id": "str (required)",
    "visibility": "Visibility (default=PRIVATE)",
    "shared_with_users": "list[str] (default=[])",
    "shared_with_groups": "list[str] (default=[])",
    "tenant_id": "Optional[str] (default=None)",
}


# VectorStoreInterface new method signatures
VECTOR_STORE_NEW_METHODS = {
    "search": "(query_vector, top_k, filters, acl_context) -> list[tuple[Chunk, float]]",
    "delete_by_owner": "(owner_id, tenant_id) -> int",
    "update_document_acl": "(document_id, visibility, shared_with_users, shared_with_groups) -> int",
}
