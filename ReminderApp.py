import sqlite3
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem
from plyer import notification
import sys

# Database setup
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        reminder_datetime TEXT,
                        notified INTEGER DEFAULT 0
                    )''')
    conn.commit()
    conn.close()

# Notification checker using QTimer
class ReminderChecker(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60000)  # Check every 60 seconds

    def check_reminders(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description FROM reminders WHERE reminder_datetime = ? AND notified = 0", (now,))
        reminders = cursor.fetchall()

        for reminder in reminders:
            try:
                notification.notify(
                    title=f"Reminder: {reminder[1]}",
                    message=reminder[2],
                    timeout=10
                )
                cursor.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (reminder[0],))
            except Exception as e:
                print(f"Notification error: {e}")

        conn.commit()
        conn.close()

# Main GUI application
class ReminderApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Reminder App")
        self.setWindowIcon(QtGui.QIcon("app_logo.png"))
        self.resize(900, 600)
        self.setStyleSheet("background-color: #f4f4f4; font-family: Arial; font-size: 14px;")

        # Input fields
        self.title_input = QtWidgets.QLineEdit()
        self.title_input.setPlaceholderText("Title (max 100 characters)")
        self.description_input = QtWidgets.QPlainTextEdit()
        self.description_input.setPlaceholderText("Description (max 500 characters)")
        self.start_date_input = QtWidgets.QDateEdit(calendarPopup=True)
        self.start_date_input.setDate(QtCore.QDate.currentDate())
        self.end_date_input = QtWidgets.QDateEdit(calendarPopup=True)
        self.end_date_input.setDate(QtCore.QDate.currentDate())
        self.reminder_datetime_input = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.reminder_datetime_input.setDateTime(QtCore.QDateTime.currentDateTime())

        # Buttons
        self.add_button = QtWidgets.QPushButton("Add Reminder")
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 5px;")
        self.add_button.clicked.connect(self.add_reminder)

        self.view_button = QtWidgets.QPushButton("Refresh List")
        self.view_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; border-radius: 5px;")
        self.view_button.clicked.connect(self.load_reminders)

        self.delete_button = QtWidgets.QPushButton("Delete Selected")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px; border-radius: 5px;")
        self.delete_button.clicked.connect(self.delete_reminder)

        # Table for reminders
        self.reminders_table = QtWidgets.QTableWidget()
        self.reminders_table.setColumnCount(7)
        self.reminders_table.setHorizontalHeaderLabels(["ID", "Title", "Description", "Start Date", "End Date", "Reminder Date", "Notified"])
        self.reminders_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # Layout
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Description:", self.description_input)
        form_layout.addRow("Start Date:", self.start_date_input)
        form_layout.addRow("End Date:", self.end_date_input)
        form_layout.addRow("Reminder Date and Time:", self.reminder_datetime_input)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.delete_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.reminders_table)
        self.setLayout(layout)

        self.load_reminders()

    def add_reminder(self):
        title = self.title_input.text()
        description = self.description_input.toPlainText()
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        reminder_datetime = self.reminder_datetime_input.dateTime().toString("yyyy-MM-dd HH:mm")

        if not title or len(title) > 100:
            QtWidgets.QMessageBox.warning(self, "Error", "Title is required and must be 100 characters or less.")
            return

        if len(description) > 500:
            QtWidgets.QMessageBox.warning(self, "Error", "Description must be 500 characters or less.")
            return

        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (title, description, start_date, end_date, reminder_datetime) VALUES (?, ?, ?, ?, ?)",
                       (title, description, start_date, end_date, reminder_datetime))
        conn.commit()
        conn.close()

        QtWidgets.QMessageBox.information(self, "Success", "Reminder added successfully.")
        self.clear_inputs()
        self.load_reminders()

    def clear_inputs(self):
        self.title_input.clear()
        self.description_input.clear()
        self.start_date_input.setDate(QtCore.QDate.currentDate())
        self.end_date_input.setDate(QtCore.QDate.currentDate())
        self.reminder_datetime_input.setDateTime(QtCore.QDateTime.currentDateTime())

    def load_reminders(self):
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, start_date, end_date, reminder_datetime, notified FROM reminders")
        reminders = cursor.fetchall()
        conn.close()

        self.reminders_table.setRowCount(len(reminders))
        for row_index, reminder in enumerate(reminders):
            for col_index, value in enumerate(reminder):
                item = QTableWidgetItem(str(value))
                if col_index == 6 and value == 1:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("green")))
                self.reminders_table.setItem(row_index, col_index, item)

    def delete_reminder(self):
        selected_row = self.reminders_table.currentRow()
        if selected_row == -1:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a record to delete.")
            return

        reminder_id = self.reminders_table.item(selected_row, 0).text()
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()

        QtWidgets.QMessageBox.information(self, "Success", "Reminder deleted successfully.")
        self.load_reminders()

if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)

    reminder_checker = ReminderChecker()  # Start reminder checking

    window = ReminderApp()
    window.show()
    sys.exit(app.exec_())
