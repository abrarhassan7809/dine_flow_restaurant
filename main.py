import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from database.connection import init_db
from widgets.styles import style_app

def main():
    # Initialize database
    init_db()

    # Create application
    app = QApplication(sys.argv)
    app.setStyleSheet(style_app())
    app.setApplicationName("DineFlow OS")
    app.setApplicationDisplayName("Restaurant Management System")

    # Set application icon (optional)
    app.setWindowIcon(QIcon.fromTheme("applications-graphics"))

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()