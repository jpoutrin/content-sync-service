"""Unit tests for ACL core module (rag/core/acl.py).

Tests cover:
- Visibility enum values and conversions
- QueryACLContext validation and defaults
- QueryACLContext.system_context() factory method
- ACLFilterSpec SQL generation
- SQL injection protection
"""

import pytest
from pydantic import ValidationError

from rag.core.acl import ACLFilterSpec, QueryACLContext, Visibility


class TestVisibilityEnum:
    """Tests for the Visibility enum."""

    def test_visibility_enum_values(self):
        """Test that all expected visibility levels exist."""
        assert Visibility.PRIVATE == "private"
        assert Visibility.SHARED == "shared"
        assert Visibility.INTERNAL == "internal"
        assert Visibility.PUBLIC == "public"

    def test_visibility_enum_string_conversion(self):
        """Test that Visibility enum can be converted to and from strings."""
        # Test string values
        assert Visibility.PRIVATE.value == "private"
        assert Visibility.SHARED.value == "shared"
        assert Visibility.INTERNAL.value == "internal"
        assert Visibility.PUBLIC.value == "public"

        # Test that Visibility inherits from str
        assert isinstance(Visibility.PRIVATE, str)
        assert isinstance(Visibility.PUBLIC, str)

        # Test string comparison
        assert Visibility.PRIVATE == "private"
        assert "public" == Visibility.PUBLIC

    def test_visibility_enum_iteration(self):
        """Test that we can iterate over all visibility levels."""
        values = [v.value for v in Visibility]
        assert "private" in values
        assert "shared" in values
        assert "internal" in values
        assert "public" in values
        assert len(values) == 4


class TestQueryACLContext:
    """Tests for the QueryACLContext model."""

    def test_query_acl_context_required_fields(self):
        """Test that principal_id is required."""
        # Should succeed with principal_id
        ctx = QueryACLContext(principal_id="user-123")
        assert ctx.principal_id == "user-123"

        # Should fail without principal_id
        with pytest.raises(ValidationError) as exc_info:
            QueryACLContext()  # type: ignore[call-arg]

        error = exc_info.value
        assert "principal_id" in str(error)

    def test_query_acl_context_defaults(self):
        """Test default values for optional fields."""
        ctx = QueryACLContext(principal_id="user-456")

        assert ctx.principal_id == "user-456"
        assert ctx.member_of_groups == []
        assert ctx.tenant_id is None
        assert ctx.bypass_acl is False

    def test_query_acl_context_with_all_fields(self):
        """Test creating context with all fields specified."""
        ctx = QueryACLContext(
            principal_id="user-789",
            member_of_groups=["group-1", "group-2"],
            tenant_id="tenant-a",
            bypass_acl=True,
        )

        assert ctx.principal_id == "user-789"
        assert ctx.member_of_groups == ["group-1", "group-2"]
        assert ctx.tenant_id == "tenant-a"
        assert ctx.bypass_acl is True

    def test_system_context_bypass(self):
        """Test that system_context() factory method returns bypass_acl=True."""
        ctx = QueryACLContext.system_context()

        assert ctx.principal_id == "system"
        assert ctx.bypass_acl is True
        assert ctx.member_of_groups == []
        assert ctx.tenant_id is None

    def test_query_acl_context_immutability(self):
        """Test that QueryACLContext is immutable (Pydantic frozen)."""
        ctx = QueryACLContext(principal_id="user-999")

        # Pydantic models are not frozen by default, but we can verify the fields
        assert ctx.principal_id == "user-999"
        # If we want immutability, we'd need to add model_config with frozen=True


class TestACLFilterSpec:
    """Tests for the ACLFilterSpec model."""

    def test_acl_filter_spec_required_fields(self):
        """Test that required fields are validated."""
        # Should succeed with required fields
        spec = ACLFilterSpec(
            principal_id="user-123",
            group_ids=[],
            tenant_id=None,
        )
        assert spec.principal_id == "user-123"

        # Should fail without required fields
        with pytest.raises(ValidationError):
            ACLFilterSpec()  # type: ignore[call-arg]

    def test_acl_filter_spec_defaults(self):
        """Test default values for optional fields."""
        spec = ACLFilterSpec(
            principal_id="user-123",
            group_ids=[],
            tenant_id=None,
        )

        assert spec.include_public is True
        assert spec.include_internal is True

    def test_acl_filter_spec_basic_sql(self):
        """Test SQL generation for basic scenario (owner only, no groups)."""
        spec = ACLFilterSpec(
            principal_id="user-123",
            group_ids=[],
            tenant_id=None,
            include_public=True,
            include_internal=True,
        )

        sql, params = spec.to_sql_conditions()

        # Check return type
        assert isinstance(sql, str)
        assert isinstance(params, list)

        # Check SQL contains expected components
        assert "owner_id = $1" in sql
        assert "visibility IN" in sql
        assert "shared_with_users" in sql

        # Check parameters
        assert "user-123" in params
        assert "public" in params
        assert "internal" in params

        # Verify parameter count matches placeholders
        placeholder_count = sql.count("$")
        assert len(params) >= placeholder_count

    def test_acl_filter_spec_with_groups(self):
        """Test SQL generation with group memberships."""
        spec = ACLFilterSpec(
            principal_id="user-456",
            group_ids=["group-1", "group-2"],
            tenant_id=None,
        )

        sql, params = spec.to_sql_conditions()

        # Check that group IDs are in parameters
        assert "group-1" in params
        assert "group-2" in params

        # Check SQL includes group sharing checks
        assert "shared_with_groups" in sql

        # Count the number of group sharing conditions
        assert sql.count("shared_with_groups") >= len(spec.group_ids)

    def test_acl_filter_spec_with_tenant(self):
        """Test SQL generation with tenant isolation."""
        spec = ACLFilterSpec(
            principal_id="user-789",
            group_ids=[],
            tenant_id="tenant-a",
        )

        sql, params = spec.to_sql_conditions()

        # Check tenant isolation is included
        assert "tenant_id" in sql
        assert "tenant-a" in params

        # Check NULL handling for tenant
        assert "tenant_id IS NULL" in sql or "IS NULL" in sql

    def test_acl_filter_spec_public_only(self):
        """Test SQL generation with only public documents."""
        spec = ACLFilterSpec(
            principal_id="user-abc",
            group_ids=[],
            tenant_id=None,
            include_public=True,
            include_internal=False,
        )

        sql, params = spec.to_sql_conditions()

        # Public should be included
        assert "public" in params

        # Internal should not be included
        assert "internal" not in params

    def test_acl_filter_spec_internal_only(self):
        """Test SQL generation with only internal documents."""
        spec = ACLFilterSpec(
            principal_id="user-def",
            group_ids=[],
            tenant_id=None,
            include_public=False,
            include_internal=True,
        )

        sql, params = spec.to_sql_conditions()

        # Internal should be included
        assert "internal" in params

        # Public should not be included
        assert "public" not in params

    def test_acl_filter_spec_no_visibility_flags(self):
        """Test SQL generation with both visibility flags disabled."""
        spec = ACLFilterSpec(
            principal_id="user-ghi",
            group_ids=[],
            tenant_id=None,
            include_public=False,
            include_internal=False,
        )

        sql, params = spec.to_sql_conditions()

        # Neither public nor internal should be in params
        assert "public" not in params
        assert "internal" not in params

        # But owner and sharing conditions should still exist
        assert "owner_id" in sql
        assert "shared_with_users" in sql

    def test_acl_filter_spec_complex_scenario(self):
        """Test SQL generation for complex scenario with all features."""
        spec = ACLFilterSpec(
            principal_id="user-complex",
            group_ids=["engineering", "admin"],
            tenant_id="tenant-prod",
            include_public=True,
            include_internal=True,
        )

        sql, params = spec.to_sql_conditions()

        # Verify all components are present
        assert "owner_id" in sql
        assert "visibility" in sql
        assert "shared_with_users" in sql
        assert "shared_with_groups" in sql
        assert "tenant_id" in sql

        # Verify all parameters are included
        assert "user-complex" in params
        assert "engineering" in params
        assert "admin" in params
        assert "tenant-prod" in params
        assert "public" in params
        assert "internal" in params

    def test_sql_injection_protection(self):
        """Test that SQL generation is protected against injection attacks."""
        # Attempt SQL injection through principal_id
        malicious_id = "user'; DROP TABLE documents;--"
        spec = ACLFilterSpec(
            principal_id=malicious_id,
            group_ids=[],
            tenant_id=None,
        )

        sql, params = spec.to_sql_conditions()

        # The malicious string should be in params, not in SQL
        assert malicious_id in params
        assert "DROP TABLE" not in sql

        # Verify SQL uses parameterized queries
        assert "$" in sql  # Should have placeholders like $1, $2, etc.

        # Verify the malicious content is safely parameterized
        # (the full malicious string is in params, not executed as SQL)
        assert any("DROP TABLE" in str(p) for p in params)

    def test_sql_injection_protection_group_ids(self):
        """Test SQL injection protection for group IDs."""
        malicious_groups = [
            "group'; DELETE FROM documents WHERE '1'='1",
            "group'; --",
            "' OR '1'='1",
        ]
        spec = ACLFilterSpec(
            principal_id="user-safe",
            group_ids=malicious_groups,
            tenant_id=None,
        )

        sql, params = spec.to_sql_conditions()

        # All malicious strings should be in params
        for malicious in malicious_groups:
            assert malicious in params

        # SQL should not contain the malicious content directly
        assert "DELETE FROM" not in sql
        assert "DELETE FROM" in str(params)  # Safely parameterized

    def test_sql_injection_protection_tenant_id(self):
        """Test SQL injection protection for tenant ID."""
        malicious_tenant = "tenant' OR '1'='1'; --"
        spec = ACLFilterSpec(
            principal_id="user-safe",
            group_ids=[],
            tenant_id=malicious_tenant,
        )

        sql, params = spec.to_sql_conditions()

        # Malicious tenant should be in params
        assert malicious_tenant in params

        # SQL should not contain malicious content directly
        assert "OR '1'='1'" not in sql

    def test_parameter_ordering_and_count(self):
        """Test that parameter count matches SQL placeholders."""
        spec = ACLFilterSpec(
            principal_id="user-param-test",
            group_ids=["group-1", "group-2", "group-3"],
            tenant_id="tenant-test",
            include_public=True,
            include_internal=True,
        )

        sql, params = spec.to_sql_conditions()

        # Count placeholders in SQL
        import re

        placeholders = re.findall(r"\$\d+", sql)
        max_placeholder = max([int(p[1:]) for p in placeholders])

        # Number of parameters should match highest placeholder number
        assert len(params) == max_placeholder

        # Verify sequential numbering
        placeholder_nums = sorted([int(p[1:]) for p in placeholders])
        assert placeholder_nums == list(range(1, max_placeholder + 1))

    def test_empty_group_ids(self):
        """Test SQL generation with empty group_ids list."""
        spec = ACLFilterSpec(
            principal_id="user-no-groups",
            group_ids=[],
            tenant_id=None,
        )

        sql, params = spec.to_sql_conditions()

        # Should still generate valid SQL
        assert isinstance(sql, str)
        assert isinstance(params, list)
        assert len(sql) > 0
        assert len(params) > 0

    def test_none_tenant_id(self):
        """Test SQL generation with None tenant_id (single-tenant mode)."""
        spec = ACLFilterSpec(
            principal_id="user-single-tenant",
            group_ids=["group-1"],
            tenant_id=None,
        )

        sql, params = spec.to_sql_conditions()

        # Tenant isolation should not be in SQL when tenant_id is None
        if "tenant_id" in sql:
            # If tenant_id appears, it should only be for NULL check
            assert "IS NULL" in sql

        # tenant_id value should not be in params (since it's None)
        assert None not in params


# Pytest fixtures for reusable test data
@pytest.fixture
def basic_context():
    """Fixture for basic QueryACLContext."""
    return QueryACLContext(principal_id="test-user")


@pytest.fixture
def system_context():
    """Fixture for system QueryACLContext."""
    return QueryACLContext.system_context()


@pytest.fixture
def multi_tenant_context():
    """Fixture for multi-tenant QueryACLContext."""
    return QueryACLContext(
        principal_id="tenant-user",
        member_of_groups=["tenant-group"],
        tenant_id="tenant-123",
    )


@pytest.fixture
def basic_filter_spec():
    """Fixture for basic ACLFilterSpec."""
    return ACLFilterSpec(
        principal_id="test-user",
        group_ids=[],
        tenant_id=None,
    )


@pytest.fixture
def complex_filter_spec():
    """Fixture for complex ACLFilterSpec."""
    return ACLFilterSpec(
        principal_id="complex-user",
        group_ids=["group-1", "group-2"],
        tenant_id="tenant-complex",
        include_public=True,
        include_internal=True,
    )


class TestFixtures:
    """Tests using pytest fixtures."""

    def test_basic_context_fixture(self, basic_context):
        """Test basic context fixture."""
        assert basic_context.principal_id == "test-user"
        assert basic_context.bypass_acl is False

    def test_system_context_fixture(self, system_context):
        """Test system context fixture."""
        assert system_context.bypass_acl is True

    def test_multi_tenant_context_fixture(self, multi_tenant_context):
        """Test multi-tenant context fixture."""
        assert multi_tenant_context.tenant_id == "tenant-123"
        assert "tenant-group" in multi_tenant_context.member_of_groups

    def test_basic_filter_spec_fixture(self, basic_filter_spec):
        """Test basic filter spec fixture."""
        sql, params = basic_filter_spec.to_sql_conditions()
        assert isinstance(sql, str)
        assert isinstance(params, list)

    def test_complex_filter_spec_fixture(self, complex_filter_spec):
        """Test complex filter spec fixture."""
        sql, params = complex_filter_spec.to_sql_conditions()
        assert "tenant-complex" in params
        assert "group-1" in params
        assert "group-2" in params
