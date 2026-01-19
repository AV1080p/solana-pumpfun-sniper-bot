"""
Role-Based Access Control Service

Handles granular permissions and RBAC.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import User, Permission, RolePermission, UserPermission, UserRole


class RBACService:
    """Service for managing role-based access control"""
    
    # Default permissions for each role
    DEFAULT_ROLE_PERMISSIONS = {
        UserRole.USER: [
            "bookings.view_own",
            "bookings.create",
            "tours.view",
            "profile.view_own",
            "profile.update_own",
            "invoices.view_own",
            "feedback.create"
        ],
        UserRole.MODERATOR: [
            "bookings.view",
            "bookings.update",
            "tours.view",
            "tours.update",
            "users.view",
            "feedback.view",
            "feedback.update"
        ],
        UserRole.ADMIN: [
            "*"  # Admin has all permissions
        ]
    }
    
    async def check_permission(
        self,
        user: User,
        permission: str,
        db: Session
    ) -> bool:
        """Check if user has a specific permission"""
        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            return True
        
        # Check user-specific permissions (overrides)
        user_perm = db.query(UserPermission).join(Permission).filter(
            UserPermission.user_id == user.id,
            Permission.name == permission
        ).first()
        
        if user_perm:
            return user_perm.granted
        
        # Check role permissions
        role_perm = db.query(RolePermission).join(Permission).filter(
            RolePermission.role == user.role,
            Permission.name == permission
        ).first()
        
        return role_perm is not None
    
    async def has_permission(
        self,
        user: User,
        permission: str,
        db: Session
    ) -> bool:
        """Alias for check_permission"""
        return await self.check_permission(user, permission, db)
    
    async def require_permission(
        self,
        user: User,
        permission: str,
        db: Session
    ):
        """Require permission or raise exception"""
        if not await self.check_permission(user, permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
    
    async def get_user_permissions(
        self,
        user: User,
        db: Session
    ) -> List[str]:
        """Get all permissions for a user"""
        permissions = []
        
        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            all_perms = db.query(Permission).all()
            return [p.name for p in all_perms]
        
        # Get role permissions
        role_perms = db.query(Permission).join(RolePermission).filter(
            RolePermission.role == user.role
        ).all()
        
        role_permission_names = {p.name for p in role_perms}
        
        # Get user-specific permissions
        user_perms = db.query(UserPermission).join(Permission).filter(
            UserPermission.user_id == user.id
        ).all()
        
        # Apply user-specific overrides
        for user_perm in user_perms:
            perm_name = user_perm.permission.name
            if user_perm.granted:
                permissions.append(perm_name)
            elif perm_name in role_permission_names:
                role_permission_names.remove(perm_name)
        
        # Add remaining role permissions
        permissions.extend(list(role_permission_names))
        
        return sorted(set(permissions))
    
    async def grant_permission(
        self,
        user: User,
        permission_name: str,
        db: Session
    ) -> Dict[str, Any]:
        """Grant a permission to a user"""
        permission = db.query(Permission).filter(
            Permission.name == permission_name
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission not found: {permission_name}"
            )
        
        # Check if already exists
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user.id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if existing:
            if existing.granted:
                return {
                    "success": True,
                    "message": "Permission already granted"
                }
            existing.granted = True
        else:
            user_perm = UserPermission(
                user_id=user.id,
                permission_id=permission.id,
                granted=True
            )
            db.add(user_perm)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Permission {permission_name} granted to user"
        }
    
    async def revoke_permission(
        self,
        user: User,
        permission_name: str,
        db: Session
    ) -> Dict[str, Any]:
        """Revoke a permission from a user"""
        permission = db.query(Permission).filter(
            Permission.name == permission_name
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission not found: {permission_name}"
            )
        
        user_perm = db.query(UserPermission).filter(
            UserPermission.user_id == user.id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if user_perm:
            user_perm.granted = False
            db.commit()
        else:
            # Create a deny permission
            user_perm = UserPermission(
                user_id=user.id,
                permission_id=permission.id,
                granted=False
            )
            db.add(user_perm)
            db.commit()
        
        return {
            "success": True,
            "message": f"Permission {permission_name} revoked from user"
        }
    
    async def initialize_default_permissions(self, db: Session) -> Dict[str, Any]:
        """Initialize default permissions and role assignments"""
        created_count = 0
        
        # Create permissions
        for role, perm_names in self.DEFAULT_ROLE_PERMISSIONS.items():
            if perm_names == ["*"]:
                continue  # Skip admin wildcard
            
            for perm_name in perm_names:
                # Check if permission exists
                perm = db.query(Permission).filter(
                    Permission.name == perm_name
                ).first()
                
                if not perm:
                    # Extract resource and action
                    parts = perm_name.split(".")
                    resource = parts[0] if len(parts) > 0 else "general"
                    action = parts[1] if len(parts) > 1 else "view"
                    
                    perm = Permission(
                        name=perm_name,
                        resource=resource,
                        action=action,
                        description=f"{action} {resource}"
                    )
                    db.add(perm)
                    created_count += 1
                
                # Check if role permission exists
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role == role,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(
                        role=role,
                        permission_id=perm.id
                    )
                    db.add(role_perm)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Initialized {created_count} permissions",
            "created_count": created_count
        }
    
    async def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new permission"""
        existing = db.query(Permission).filter(Permission.name == name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission {name} already exists"
            )
        
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description or f"{action} {resource}"
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        return {
            "success": True,
            "permission": {
                "id": permission.id,
                "name": permission.name,
                "resource": permission.resource,
                "action": permission.action,
                "description": permission.description
            }
        }

