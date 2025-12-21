"""Shared type contracts for TS-0002 RAG Transcript Ingestion.

NOTE: All contracts already exist in rag/core/ from TS-0001.
This file serves as a reference for parallel development agents.
DO NOT import from this file - import from rag.core instead.

Existing contracts:
- rag/core/interfaces.py: ChunkerInterface, EmbedderInterface, VectorStoreInterface, RetrieverInterface
- rag/core/schemas.py: Document, Chunk, Embedding, SearchQuery, SearchResult
- rag/core/acl.py: Visibility, QueryACLContext, ACLFilterSpec
"""

# Reference: ChunkerInterface signature
# class ChunkerInterface(ABC):
#     def chunk(self, document: Document) -> list[Chunk]: ...

# Reference: EmbedderInterface signature
# class EmbedderInterface(ABC):
#     @property
#     def model_name(self) -> str: ...
#     @property
#     def dimensions(self) -> int: ...
#     def embed(self, text: str) -> list[float]: ...
#     def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

# Reference: Chunk.from_document() factory
# @classmethod
# def from_document(cls, document: Document, **chunk_fields) -> Chunk:
#     """Create Chunk with ACL fields copied from parent Document."""

# Reference: Visibility enum values
# class Visibility(str, Enum):
#     PRIVATE = "private"
#     SHARED = "shared"
#     INTERNAL = "internal"
#     PUBLIC = "public"

# Reference: QueryACLContext for search
# class QueryACLContext(BaseModel):
#     principal_id: str
#     member_of_groups: list[str] = []
#     tenant_id: str | None = None
#     bypass_acl: bool = False
#
#     @classmethod
#     def system_context(cls) -> QueryACLContext:
#         return cls(principal_id="system", bypass_acl=True)
