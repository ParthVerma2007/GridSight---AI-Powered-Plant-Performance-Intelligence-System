from enum import Enum
from typing import List, Optional
from fastapi import Header, Query, HTTPException, Depends, status

class UserRole(str, Enum):
    CEO = "CEO"
    CFO = "CFO"
    OPERATIONS = "OPERATIONS"
    TECHNICIAN = "TECHNICIAN"
    ADMIN = "ADMIN"

def get_current_role(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role_query: Optional[str] = Query(None, alias="role")
) -> UserRole:
    """
    Extracts and validates user role from X-User-Role header or query parameter.
    Defaults to OPERATIONS if not explicitly specified.
    """
    role_str = (x_user_role or role_query or "OPERATIONS").strip().upper()
    
    if role_str in ["CEO", "CFO", "EXECUTIVE"]:
        return UserRole.CEO
    elif role_str in ["OPERATIONS", "OPS", "MANAGER"]:
        return UserRole.OPERATIONS
    elif role_str in ["TECHNICIAN", "TECH", "FIELD"]:
        return UserRole.TECHNICIAN
    elif role_str in ["ADMIN"]:
        return UserRole.ADMIN
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid or unauthorized role: '{role_str}'. Allowed roles: CEO, CFO, OPERATIONS, TECHNICIAN, ADMIN."
        )

def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory to enforce RBAC permissions on sensitive API endpoints.
    """
    def role_checker(current_role: UserRole = Depends(get_current_role)):
        if current_role == UserRole.ADMIN or current_role in allowed_roles:
            return current_role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_role.value}' is not authorized to access this resource. Allowed: {[r.value for r in allowed_roles]}"
        )
    return role_checker
