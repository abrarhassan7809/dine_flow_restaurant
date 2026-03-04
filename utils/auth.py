"""Authentication and authorization utilities"""


class Permission:
    """Permission constants"""
    VIEW_FLOOR = 'view_floor'
    VIEW_ORDERS = 'view_orders'
    CREATE_ORDER = 'create_order'
    EDIT_ORDER = 'edit_order'
    DELETE_ORDER = 'delete_order'
    VIEW_KITCHEN = 'view_kitchen'
    UPDATE_ORDER_STATUS = 'update_order_status'
    VIEW_REPORTS = 'view_reports'
    VIEW_MENU = 'view_menu'
    EDIT_MENU = 'edit_menu'
    DELETE_MENU = 'delete_menu'
    VIEW_TABLES = 'view_tables'
    EDIT_TABLES = 'edit_tables'
    DELETE_TABLES = 'delete_tables'
    VIEW_RESERVATIONS = 'view_reservations'
    CREATE_RESERVATION = 'create_reservation'
    EDIT_RESERVATION = 'edit_reservation'
    DELETE_RESERVATION = 'delete_reservation'
    VIEW_INVENTORY = 'view_inventory'
    EDIT_INVENTORY = 'edit_inventory'
    VIEW_STAFF = 'view_staff'
    EDIT_STAFF = 'edit_staff'
    DELETE_STAFF = 'delete_staff'
    VIEW_AUDIT = 'view_audit'
    MANAGE_SYSTEM = 'manage_system'


class Role:
    """Role definitions with permissions"""

    ADMIN = {
        'name': 'admin',
        'permissions': [
            Permission.VIEW_FLOOR,
            Permission.VIEW_ORDERS,
            Permission.CREATE_ORDER,
            Permission.EDIT_ORDER,
            Permission.DELETE_ORDER,
            Permission.VIEW_KITCHEN,
            Permission.UPDATE_ORDER_STATUS,
            Permission.VIEW_REPORTS,
            Permission.VIEW_MENU,
            Permission.EDIT_MENU,
            Permission.DELETE_MENU,
            Permission.VIEW_TABLES,
            Permission.EDIT_TABLES,
            Permission.DELETE_TABLES,
            Permission.VIEW_RESERVATIONS,
            Permission.CREATE_RESERVATION,
            Permission.EDIT_RESERVATION,
            Permission.DELETE_RESERVATION,
            Permission.VIEW_INVENTORY,
            Permission.EDIT_INVENTORY,
            Permission.VIEW_STAFF,
            Permission.EDIT_STAFF,
            Permission.DELETE_STAFF,
            Permission.VIEW_AUDIT,
            Permission.MANAGE_SYSTEM,
        ]
    }

    MANAGER = {
        'name': 'manager',
        'permissions': [
            Permission.VIEW_FLOOR,
            Permission.VIEW_ORDERS,
            Permission.CREATE_ORDER,
            Permission.EDIT_ORDER,
            Permission.VIEW_KITCHEN,
            Permission.UPDATE_ORDER_STATUS,
            Permission.VIEW_REPORTS,
            Permission.VIEW_MENU,
            Permission.EDIT_MENU,
            Permission.VIEW_TABLES,
            Permission.EDIT_TABLES,
            Permission.VIEW_RESERVATIONS,
            Permission.CREATE_RESERVATION,
            Permission.EDIT_RESERVATION,
            Permission.VIEW_INVENTORY,
            Permission.EDIT_INVENTORY,
            Permission.VIEW_STAFF,
        ]
    }

    CHEF = {
        'name': 'chef',
        'permissions': [
            Permission.VIEW_FLOOR,
            Permission.VIEW_ORDERS,
            Permission.VIEW_KITCHEN,
            Permission.UPDATE_ORDER_STATUS,
            Permission.VIEW_MENU,
        ]
    }

    WAITER = {
        'name': 'waiter',
        'permissions': [
            Permission.VIEW_FLOOR,
            Permission.VIEW_ORDERS,
            Permission.CREATE_ORDER,
            Permission.EDIT_ORDER,
            Permission.VIEW_KITCHEN,
            Permission.VIEW_MENU,
            Permission.VIEW_TABLES,
            Permission.VIEW_RESERVATIONS,
            Permission.CREATE_RESERVATION,
        ]
    }

    CASHIER = {
        'name': 'cashier',
        'permissions': [
            Permission.VIEW_FLOOR,
            Permission.VIEW_ORDERS,
            Permission.VIEW_REPORTS,
            Permission.VIEW_MENU,
            Permission.VIEW_TABLES,
        ]
    }

    @classmethod
    def get_permissions(cls, role_name):
        """Get permissions for a role"""
        roles = {
            'admin': cls.ADMIN['permissions'],
            'manager': cls.MANAGER['permissions'],
            'chef': cls.CHEF['permissions'],
            'waiter': cls.WAITER['permissions'],
            'cashier': cls.CASHIER['permissions'],
        }
        return roles.get(role_name, [])


def has_permission(user_role, permission):
    """Check if user role has specific permission"""
    permissions = Role.get_permissions(user_role)
    return permission in permissions


def require_permission(permission):
    """Decorator to check permissions before allowing access"""

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Get current user from the widget's window
            main_window = self.window()
            if hasattr(main_window, 'current_user') and main_window.current_user:
                user_role = main_window.current_user.get('role', '')
                if has_permission(user_role, permission):
                    return func(self, *args, **kwargs)
                else:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Access Denied",
                        f"You don't have permission to perform this action.\n"
                        f"Required permission: {permission}"
                    )
                    return None
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Not Logged In", "Please log in to continue")
                return None

        return wrapper

    return decorator