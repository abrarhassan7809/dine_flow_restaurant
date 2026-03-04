from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QComboBox, QDateTimeEdit,
                               QLineEdit, QAbstractItemView, QApplication)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QFont
from widgets.buttons import GhostButton, DangerButton, AccentButton
from widgets.styles import table_style, input_style
from database.connection import get_db
from utils.constants import *
from utils.helpers import format_datetime
from utils.audit import audit_logger
import json


class AuditView(QWidget):
    """Audit log view for administrators"""

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📋 Audit Log")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Export button
        export_btn = GhostButton("📥 Export CSV")
        export_btn.clicked.connect(self._export_csv)
        header.addWidget(export_btn)

        # Clear logs button (danger style)
        self.clear_btn = DangerButton("🗑️ Clear All Logs")
        self.clear_btn.clicked.connect(self._confirm_clear_logs)
        header.addWidget(self.clear_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        filter_bar.addWidget(QLabel("From:"))
        self.filter_from = QDateTimeEdit()
        self.filter_from.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.filter_from.setCalendarPopup(True)
        self.filter_from.setStyleSheet(input_style())
        filter_bar.addWidget(self.filter_from)

        filter_bar.addWidget(QLabel("To:"))
        self.filter_to = QDateTimeEdit()
        self.filter_to.setDateTime(QDateTime.currentDateTime())
        self.filter_to.setCalendarPopup(True)
        self.filter_to.setStyleSheet(input_style())
        filter_bar.addWidget(self.filter_to)

        filter_bar.addWidget(QLabel("User:"))
        self.filter_user = QLineEdit()
        self.filter_user.setPlaceholderText("Filter by user")
        self.filter_user.setStyleSheet(input_style())
        filter_bar.addWidget(self.filter_user)

        filter_bar.addWidget(QLabel("Action:"))
        self.filter_action = QComboBox()
        self.filter_action.addItems(["All", "LOGIN", "LOGOUT", "CREATE", "UPDATE", "DELETE"])
        self.filter_action.setStyleSheet(input_style())
        filter_bar.addWidget(self.filter_action)

        apply_btn = GhostButton("Apply Filter")
        apply_btn.clicked.connect(self.refresh)
        filter_bar.addWidget(apply_btn)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Stats bar with clear indication
        stats_bar = QHBoxLayout()
        self.total_count_label = QLabel("Total Entries: 0")
        self.total_count_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        stats_bar.addWidget(self.total_count_label)

        stats_bar.addStretch()

        # Legend for action colors
        legend = QHBoxLayout()
        legend.setSpacing(15)

        # Login - Green
        login_legend = QHBoxLayout()
        login_dot = QLabel("●")
        login_dot.setStyleSheet(f"color: {GREEN}; font-size: 14px;")
        login_legend.addWidget(login_dot)
        login_legend.addWidget(QLabel("Login"))
        legend.addLayout(login_legend)

        # Logout - Orange
        logout_legend = QHBoxLayout()
        logout_dot = QLabel("●")
        logout_dot.setStyleSheet(f"color: {ORANGE}; font-size: 14px;")
        logout_legend.addWidget(logout_dot)
        logout_legend.addWidget(QLabel("Logout"))
        legend.addLayout(logout_legend)

        # Create - Green
        create_legend = QHBoxLayout()
        create_dot = QLabel("●")
        create_dot.setStyleSheet(f"color: {GREEN}; font-size: 14px;")
        create_legend.addWidget(create_dot)
        create_legend.addWidget(QLabel("Create"))
        legend.addLayout(create_legend)

        # Update - Blue
        update_legend = QHBoxLayout()
        update_dot = QLabel("●")
        update_dot.setStyleSheet(f"color: {BLUE}; font-size: 14px;")
        update_legend.addWidget(update_dot)
        update_legend.addWidget(QLabel("Update"))
        legend.addLayout(update_legend)

        # Delete - Red
        delete_legend = QHBoxLayout()
        delete_dot = QLabel("●")
        delete_dot.setStyleSheet(f"color: {RED}; font-size: 14px;")
        delete_legend.addWidget(delete_dot)
        delete_legend.addWidget(QLabel("Delete"))
        legend.addLayout(delete_legend)

        stats_bar.addLayout(legend)
        layout.addLayout(stats_bar)

        # Audit table with horizontal scrolling
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Role", "Action", "Table", "Record ID", "Details", "Changes"
        ])

        # Enable both horizontal and vertical scrolling
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Set column widths - make Changes column wider
        self.table.setColumnWidth(0, 180)  # Timestamp
        self.table.setColumnWidth(1, 150)  # User
        self.table.setColumnWidth(2, 100)  # Role
        self.table.setColumnWidth(3, 100)  # Action
        self.table.setColumnWidth(4, 120)  # Table
        self.table.setColumnWidth(5, 90)  # Record ID
        self.table.setColumnWidth(6, 250)  # Details
        self.table.setColumnWidth(7, 400)  # Changes - wider for JSON data

        # Set resize mode - allow manual resizing
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)

        self.table.setStyleSheet(table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(500)

        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        """Refresh audit log"""
        from_date = self.filter_from.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        to_date = self.filter_to.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        user_filter = self.filter_user.text().strip()
        action_filter = self.filter_action.currentText()

        conn = get_db()

        query = """
                SELECT *
                FROM audit_log
                WHERE timestamp BETWEEN ? AND ? \
                """
        params = [from_date, to_date]

        if user_filter:
            query += " AND user_name LIKE ?"
            params.append(f"%{user_filter}%")

        if action_filter != "All":
            query += " AND action = ?"
            params.append(action_filter)

        query += " ORDER BY timestamp DESC LIMIT 1000"

        logs = conn.execute(query, params).fetchall()
        conn.close()

        self.table.setRowCount(len(logs))
        self.total_count_label.setText(f"Total Entries: {len(logs)}")

        for row, log in enumerate(logs):
            log_dict = dict(log)

            # Timestamp
            time_str = format_datetime(log_dict['timestamp'], "%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, time_item)

            # User
            user_name = log_dict.get('user_name', 'System')
            if user_name is None:
                user_name = 'System'
            self.table.setItem(row, 1, QTableWidgetItem(user_name))

            # Role
            role = log_dict.get('user_role', '')
            if role:
                role = role.capitalize()
            role_item = QTableWidgetItem(role)
            role_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, role_item)

            # Action with improved color coding
            action = log_dict['action']

            # Define action colors with better differentiation
            if action == 'LOGIN':
                action_color = "#2ECC71"  # Bright Green
                bg_color = "#2ECC7122"  # Light green background
            elif action == 'LOGOUT':
                action_color = "#E67E22"  # Orange
                bg_color = "#E67E2222"  # Light orange background
            elif action == 'CREATE':
                action_color = "#27AE60"  # Dark Green
                bg_color = "#27AE6022"  # Light dark green background
            elif action == 'UPDATE':
                action_color = "#3498DB"  # Bright Blue
                bg_color = "#3498DB22"  # Light blue background
            elif action == 'DELETE':
                action_color = "#E74C3C"  # Bright Red
                bg_color = "#E74C3C22"  # Light red background
            else:
                action_color = TEXT2
                bg_color = "transparent"

            action_item = QTableWidgetItem(action)
            action_item.setTextAlignment(Qt.AlignCenter)
            action_item.setForeground(QColor(action_color))
            action_item.setBackground(QColor(bg_color))

            # Make action bold
            font = action_item.font()
            font.setBold(True)
            action_item.setFont(font)
            self.table.setItem(row, 3, action_item)

            # Table
            table_name = log_dict['table_name'] or '-'
            table_item = QTableWidgetItem(table_name)
            table_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, table_item)

            # Record ID
            record_id = str(log_dict['record_id']) if log_dict['record_id'] else '-'
            id_item = QTableWidgetItem(record_id)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, id_item)

            # Details (summary)
            details = self._format_details(log_dict)
            details_item = QTableWidgetItem(details)
            details_item.setToolTip(details)
            self.table.setItem(row, 6, details_item)

            # Changes (formatted JSON)
            changes = self._format_changes(log_dict)
            changes_item = QTableWidgetItem(changes)
            changes_item.setToolTip(changes)
            # Use monospace font for JSON data
            font = QFont("Monospace")
            font.setStyleHint(QFont.TypeWriter)
            changes_item.setFont(font)
            self.table.setItem(row, 7, changes_item)

            self.table.setRowHeight(row, 50)

        # Adjust column widths to content
        self.table.resizeColumnsToContents()

        # But ensure Changes column doesn't get too narrow
        if self.table.columnWidth(7) < 300:
            self.table.setColumnWidth(7, 300)

    def _confirm_clear_logs(self):
        """Confirm and clear all audit logs (admin only)"""
        # Double-check that user is admin
        main_window = self.window()
        if not hasattr(main_window, 'current_user') or not main_window.current_user:
            QMessageBox.warning(self, "Access Denied", "You must be logged in to perform this action.")
            return

        if main_window.current_user['role'] != 'admin':
            QMessageBox.warning(
                self,
                "Access Denied",
                "Only administrators can clear audit logs.\n\n"
                "This action has been logged for security purposes."
            )
            return

        # Show warning with multiple confirmations
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⚠️ Clear All Audit Logs")
        msg.setText(
            "You are about to permanently delete ALL audit logs.\n\n"
            "This action:"
            "\n• Cannot be undone"
            "\n• Will remove all login history"
            "\n• Will remove all action records"
            "\n• Will be logged for security"
        )
        msg.setInformativeText(
            "Are you ABSOLUTELY sure you want to continue?\n\n"
            "Type 'DELETE' in the box below to confirm:"
        )

        # Add text input for confirmation
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self,
            "Confirm Deletion",
            "Type 'DELETE' to confirm:",
            QLineEdit.Normal
        )

        if not ok or text != "DELETE":
            QMessageBox.information(
                self,
                "Cancelled",
                "Log deletion cancelled. No records were removed."
            )
            return

        # Final confirmation
        reply = QMessageBox.question(
            self,
            "Final Confirmation",
            "This is your last chance!\n\n"
            "All audit logs will be permanently deleted.\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._clear_logs()

    def _clear_logs(self):
        """Actually clear the audit logs"""
        try:
            conn = get_db()

            # Get count before deletion
            count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

            # Log this action before deleting (if possible)
            main_window = self.window()
            if hasattr(main_window, 'current_user') and main_window.current_user:
                audit_logger.log(
                    'DELETE',
                    'audit_log',
                    None,
                    None,
                    f"Bulk deletion of {count} audit log entries by admin"
                )

            # Delete all logs
            conn.execute("DELETE FROM audit_log")
            conn.execute("DELETE FROM login_history")
            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Logs Cleared",
                f"✅ Successfully deleted {count} audit log entries.\n\n"
                "This action has been recorded in the new logs."
            )

            self.refresh()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear logs:\n{str(e)}"
            )

    def _format_details(self, log):
        """Format log details"""
        action = log['action']

        if action == 'LOGIN':
            return f"👤 User logged in"
        elif action == 'LOGOUT':
            return f"🚪 User logged out"
        elif action == 'CREATE':
            return f"➕ Created new record in {log['table_name']}"
        elif action == 'UPDATE':
            return f"✏️ Updated record in {log['table_name']}"
        elif action == 'DELETE':
            return f"❌ Deleted record from {log['table_name']}"
        else:
            new_val = log.get('new_value')
            if new_val:
                try:
                    if new_val.startswith('{'):
                        data = json.loads(new_val)
                        if 'name' in data:
                            return f"Name: {data['name']}"
                        elif 'customer_name' in data:
                            return f"Customer: {data['customer_name']}"
                except:
                    pass
                return new_val[:100] if len(new_val) > 100 else new_val
            return ''

    def _format_changes(self, log):
        """Format old/new values in a readable way"""
        old = log.get('old_value')
        new = log.get('new_value')

        if not old and not new:
            return '-'

        result = []

        # Handle new values (for CREATE actions)
        if new and not old:
            try:
                if new.startswith('{'):
                    data = json.loads(new)
                    # Format as key: value pairs
                    for key, value in data.items():
                        if value and key not in ['created_at', 'updated_at', 'timestamp']:
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:50] + "..."
                            result.append(f"{key}: {value}")
                    return ' | '.join(result)
                else:
                    return new
            except:
                return new[:200]

        # Handle old and new values (for UPDATE actions)
        if old and new:
            try:
                old_data = json.loads(old) if old.startswith('{') else {}
                new_data = json.loads(new) if new.startswith('{') else {}

                # Find what changed
                changes = []
                all_keys = set(old_data.keys()) | set(new_data.keys())
                for key in all_keys:
                    old_val = old_data.get(key)
                    new_val = new_data.get(key)
                    if old_val != new_val:
                        # Format the change with arrows
                        if old_val and new_val:
                            # Truncate long values
                            if isinstance(old_val, str) and len(old_val) > 30:
                                old_val = old_val[:30] + "..."
                            if isinstance(new_val, str) and len(new_val) > 30:
                                new_val = new_val[:30] + "..."
                            changes.append(f"{key}: {old_val} → {new_val}")
                        elif new_val:
                            changes.append(f"{key}: (new) → {new_val}")
                        elif old_val:
                            changes.append(f"{key}: {old_val} → (removed)")

                if changes:
                    return ' | '.join(changes[:5])  # Limit to 5 changes
                else:
                    return "No significant changes"
            except:
                return f"Old: {old[:100]} → New: {new[:100]}"

        # Handle old values only (for DELETE actions)
        if old and not new:
            try:
                if old.startswith('{'):
                    data = json.loads(old)
                    items = []
                    for k, v in data.items():
                        if v and k not in ['created_at', 'updated_at', 'timestamp']:
                            if isinstance(v, str) and len(v) > 30:
                                v = v[:30] + "..."
                            items.append(f"{k}: {v}")
                    return ' | '.join(items[:5])
                else:
                    return old
            except:
                return old[:200]

        return str(new or old or '-')[:200]

    def _export_csv(self):
        """Export audit log to CSV"""
        try:
            import csv
            from datetime import datetime
            from PySide6.QtWidgets import QFileDialog

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Audit Log",
                f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            # Get current filtered data
            from_date = self.filter_from.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            to_date = self.filter_to.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            user_filter = self.filter_user.text().strip()
            action_filter = self.filter_action.currentText()

            conn = get_db()

            query = """
                    SELECT *
                    FROM audit_log
                    WHERE timestamp BETWEEN ? AND ? \
                    """
            params = [from_date, to_date]

            if user_filter:
                query += " AND user_name LIKE ?"
                params.append(f"%{user_filter}%")

            if action_filter != "All":
                query += " AND action = ?"
                params.append(action_filter)

            query += " ORDER BY timestamp DESC"

            logs = conn.execute(query, params).fetchall()
            conn.close()

            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Timestamp', 'User', 'Role', 'Action', 'Table',
                                 'Record ID', 'Details', 'Changes'])

                # Write data
                for log in logs:
                    log_dict = dict(log)
                    writer.writerow([
                        log_dict['timestamp'],
                        log_dict.get('user_name', 'System'),
                        log_dict.get('user_role', ''),
                        log_dict['action'],
                        log_dict['table_name'],
                        log_dict['record_id'],
                        self._format_details(log_dict),
                        self._format_changes(log_dict)
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Audit log exported to:\n{filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export audit log:\n{str(e)}"
            )