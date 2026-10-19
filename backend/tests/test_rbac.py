import pytest
from fastapi import HTTPException
from app.auth.rbac import get_current_role, require_role, UserRole

def test_role_extraction_and_normalization():
    assert get_current_role(x_user_role="CEO", role_query=None) == UserRole.CEO
    assert get_current_role(x_user_role="CFO", role_query=None) == UserRole.CEO
    assert get_current_role(x_user_role="operations", role_query=None) == UserRole.OPERATIONS
    assert get_current_role(x_user_role="tech", role_query=None) == UserRole.TECHNICIAN
    assert get_current_role(x_user_role=None, role_query=None) == UserRole.OPERATIONS

def test_invalid_role_raises_403():
    with pytest.raises(HTTPException) as exc:
        get_current_role(x_user_role="UNAUTHORIZED_HACKER")
    assert exc.value.status_code == 403

def test_require_role_enforcement():
    checker = require_role([UserRole.OPERATIONS, UserRole.ADMIN])
    
    # Operations allowed
    assert checker(UserRole.OPERATIONS) == UserRole.OPERATIONS
    # Admin allowed
    assert checker(UserRole.ADMIN) == UserRole.ADMIN

    # Technician forbidden on operations-only endpoint
    with pytest.raises(HTTPException) as exc:
        checker(UserRole.TECHNICIAN)
    assert exc.value.status_code == 403
