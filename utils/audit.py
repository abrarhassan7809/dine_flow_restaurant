import json
from datetime import datetime
from database.connection import get_db


class AuditLogger:
    """Logger for user actions"""

    def __init__(self, user=None):
        self.user = user

    def set_user(self, user):
        """Set current user"""
        self.user = user

    def log(self, action, table_name, record_id=None, old_value=None, new_value=None):
        """Log an action to audit log"""
        if not self.user:
            return

        conn = get_db()

        # Convert complex objects to JSON string
        if old_value and not isinstance(old_value, str):
            try:
                old_value = json.dumps(old_value, default=str)
            except:
                old_value = str(old_value)

        if new_value and not isinstance(new_value, str):
            try:
                new_value = json.dumps(new_value, default=str)
            except:
                new_value = str(new_value)

        conn.execute("""
                     INSERT INTO audit_log (user_id, user_name, user_role, action,
                                            table_name, record_id, old_value, new_value)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                     """, (
                         self.user.get('id'),
                         self.user.get('name'),
                         self.user.get('role'),
                         action,
                         table_name,
                         record_id,
                         old_value,
                         new_value
                     ))

        conn.commit()
        conn.close()

    def log_login(self, user):
        """Log user login"""
        conn = get_db()
        conn.execute("""
                     INSERT INTO login_history (user_id, user_name)
                     VALUES (?, ?)
                     """, (user.get('id'), user.get('name')))
        conn.commit()
        conn.close()

        self.log('LOGIN', 'session', user.get('id'), None, f"User {user.get('name')} logged in")

    def log_logout(self, user_id):
        """Log user logout"""
        conn = get_db()
        conn.execute("""
                     UPDATE login_history
                     SET logout_time = CURRENT_TIMESTAMP
                     WHERE user_id = ?
                       AND logout_time IS NULL ORDER BY login_time DESC LIMIT 1
                     """, (user_id,))
        conn.commit()
        conn.close()

        self.log('LOGOUT', 'session', user_id, None, f"User logged out")

    def log_create(self, table_name, record_id, data):
        """Log record creation"""
        self.log('CREATE', table_name, record_id, None, data)

    def log_update(self, table_name, record_id, old_data, new_data):
        """Log record update"""
        self.log('UPDATE', table_name, record_id, old_data, new_data)

    def log_delete(self, table_name, record_id, data):
        """Log record deletion"""
        self.log('DELETE', table_name, record_id, data, None)


# Global audit logger instance
audit_logger = AuditLogger()