# main.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QFormLayout,
    QMessageBox, QHBoxLayout, QHeaderView, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from db import fetch_cursor, call_procedure


# ---------------- LOGIN PAGE ----------------
class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MovieApp Login")
        self.setGeometry(400, 200, 350, 250)
        self.initUI()
        self.apply_styles()

    def initUI(self):
        layout = QFormLayout()

        self.id_input = QLineEdit()
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)

        layout.addRow("User ID:", self.id_input)
        layout.addRow("Password:", self.pwd_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Arial;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 4px;
            }
        """)

    def check_login(self):
        user_id = self.id_input.text().strip()
        password = self.pwd_input.text().strip()

        if not user_id or not password:
            self.show_error("User ID and Password required!")
            return

        if not user_id.isdigit():
            self.show_error("User ID must be a number!")
            return

        query = "SELECT NAME, ADMIN FROM USER_TABLE WHERE USER_ID = :id AND TRIM(PASSWORD) = :pwd"
        result = fetch_cursor(query, [int(user_id), password])

        if isinstance(result, str) or len(result) == 0:
            self.show_error("Invalid credentials!")
            return

        name, is_admin = result[0]
        if is_admin.upper() == 'Y':
            self.admin_panel = AdminPanel(name)
            self.admin_panel.showMaximized()
        else:
            self.user_panel = UserPanel(int(user_id), name)
            self.user_panel.showMaximized()
        self.close()

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)


# ---------------- USER PANEL ----------------
class UserPanel(QWidget):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.setWindowTitle(f"User Panel - {username}")
        self.initUI()
        self.apply_styles()

    def initUI(self):
        layout = QVBoxLayout()

        # Welcome label
        self.welcome_label = QLabel(f"Welcome, {self.username} (User)")
        self.welcome_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("color: white; background-color: #5DADE2; padding: 8px;")
        layout.addWidget(self.welcome_label)

        # Logout top-right
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        logout_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        logout_layout.addItem(spacer)
        logout_layout.addWidget(self.logout_btn)
        layout.addLayout(logout_layout)

        # Tabs
        self.tabs = QTabWidget()

        # My Reviews tab
        self.reviews_tab = QWidget()
        reviews_layout = QVBoxLayout()
        self.review_table = QTableWidget()
        self.review_table.setColumnCount(4)
        self.review_table.setHorizontalHeaderLabels(["Review ID", "Movie ID", "Rating", "Text"])
        self.review_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.review_table.setAlternatingRowColors(True)
        self.review_table.setStyleSheet("alternate-background-color: #e6f2ff; background-color: #ffffff;")
        reviews_layout.addWidget(self.review_table)
        self.reviews_tab.setLayout(reviews_layout)
        self.tabs.addTab(self.reviews_tab, "My Reviews")

        # Add Review tab
        self.add_tab = QWidget()
        add_layout = QFormLayout()
        self.movie_id_input_add = QLineEdit()
        self.rating_input_add = QLineEdit()
        self.review_text_input_add = QTextEdit()
        self.add_review_btn = QPushButton("Add Review")
        self.add_review_btn.clicked.connect(self.add_review)
        add_layout.addRow("Movie ID:", self.movie_id_input_add)
        add_layout.addRow("Rating:", self.rating_input_add)
        add_layout.addRow("Review Text:", self.review_text_input_add)
        add_layout.addWidget(self.add_review_btn)
        self.add_tab.setLayout(add_layout)
        self.tabs.addTab(self.add_tab, "Add Review")

        # Edit Review tab
        self.edit_tab = QWidget()
        edit_layout = QFormLayout()
        self.movie_id_input_edit = QLineEdit()
        self.rating_input_edit = QLineEdit()
        self.review_text_input_edit = QTextEdit()
        self.edit_review_btn = QPushButton("Edit Review")
        self.edit_review_btn.clicked.connect(self.edit_review)
        edit_layout.addRow("Movie ID:", self.movie_id_input_edit)
        edit_layout.addRow("Rating:", self.rating_input_edit)
        edit_layout.addRow("Review Text:", self.review_text_input_edit)
        edit_layout.addWidget(self.edit_review_btn)
        self.edit_tab.setLayout(edit_layout)
        self.tabs.addTab(self.edit_tab, "Edit Review")

        # All Movies tab
        self.all_movies_tab = QWidget()
        all_layout = QVBoxLayout()
        self.all_movies_table = QTableWidget()
        self.all_movies_table.setColumnCount(4)
        self.all_movies_table.setHorizontalHeaderLabels(["Movie ID", "Title", "Director ID", "Genre ID"])
        self.all_movies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        all_layout.addWidget(self.all_movies_table)
        self.all_movies_tab.setLayout(all_layout)
        self.tabs.addTab(self.all_movies_tab, "All Movies")

        # Top Rated Movies tab
        self.top_movies_tab = QWidget()
        top_layout = QVBoxLayout()
        self.top_movies_table = QTableWidget()
        self.top_movies_table.setColumnCount(2)
        self.top_movies_table.setHorizontalHeaderLabels(["Title", "Avg Rating"])
        self.top_movies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        top_layout.addWidget(self.top_movies_table)
        self.top_movies_tab.setLayout(top_layout)
        self.tabs.addTab(self.top_movies_tab, "Top Rated Movies")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Load data
        self.load_reviews()
        self.load_all_movies()
        self.load_top_movies()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #f9f9f9; }
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #218838; }
        """)

    # -------------------- USER FUNCTIONS --------------------
    def load_reviews(self):
        query = "SELECT REVIEW_ID, MOVIE_ID, RATING, REVIEW_TEXT FROM REVIEW WHERE USER_ID = :id"
        result = fetch_cursor(query, [self.user_id])
        if isinstance(result, str):
            return
        self.review_table.setRowCount(len(result))
        for r_idx, row in enumerate(result):
            for c_idx, val in enumerate(row):
                self.review_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def add_review(self):
        movie_id = self.movie_id_input_add.text().strip()
        rating = self.rating_input_add.text().strip()
        text = self.review_text_input_add.toPlainText().strip()

        if not movie_id.isdigit():
            QMessageBox.warning(self, "Error", "Movie ID must be a number!")
            return

        try:
            rating_val = float(rating)
            if rating_val < 0 or rating_val > 5:
                QMessageBox.warning(self, "Error", "Rating must be between 0 and 5!")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "Rating must be a number!")
            return

        if not text:
            QMessageBox.warning(self, "Error", "Review Text cannot be empty!")
            return

        success, msg = call_procedure("ADD_REVIEW", [self.user_id, int(movie_id), rating_val, text])
        if success:
            QMessageBox.information(self, "Success", "Review added successfully!")
            self.movie_id_input_add.clear()
            self.rating_input_add.clear()
            self.review_text_input_add.clear()
            self.load_reviews()
        else:
            QMessageBox.warning(self, "Error", f"Failed: {msg}")

    def edit_review(self):
        movie_id = self.movie_id_input_edit.text().strip()
        rating = self.rating_input_edit.text().strip()
        text = self.review_text_input_edit.toPlainText().strip()

        if not movie_id or not rating or not text:
            QMessageBox.warning(self, "Error", "All fields required!")
            return

        try:
            rating_val = float(rating)
            if rating_val < 0 or rating_val > 5:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Rating must be a number between 0 and 5!")
            return

        success, msg = call_procedure("EDIT_REVIEW", [self.user_id, int(movie_id), rating_val, text])
        if success:
            QMessageBox.information(self, "Success", "Review updated successfully!")
            self.load_reviews()
            self.movie_id_input_edit.clear()
            self.rating_input_edit.clear()
            self.review_text_input_edit.clear()
        else:
            QMessageBox.warning(self, "Error", f"Failed: {msg}")

    def load_all_movies(self):
        query = "SELECT MOVIE_ID, TITLE, DIRECTOR_ID, GENRE_ID FROM MOVIE"
        result = fetch_cursor(query)
        if isinstance(result, str):
            return
        self.all_movies_table.setRowCount(len(result))
        for r_idx, row in enumerate(result):
            for c_idx, val in enumerate(row):
                self.all_movies_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def load_top_movies(self):
        query = """
            SELECT m.TITLE, ROUND(AVG(r.RATING), 2)
            FROM MOVIE m
            JOIN REVIEW r ON m.MOVIE_ID = r.MOVIE_ID
            GROUP BY m.TITLE
            HAVING AVG(r.RATING) >= 4.5
        """
        result = fetch_cursor(query)
        if isinstance(result, str):
            return
        self.top_movies_table.setRowCount(len(result))
        for r_idx, row in enumerate(result):
            for c_idx, val in enumerate(row):
                self.top_movies_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def logout(self):
        self.close()
        self.login = LoginPage()
        self.login.showMaximized()


# ------------------- ADMIN PANEL -------------------
class AdminPanel(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"Admin Panel - {username}")
        self.initUI()
        self.apply_styles()

    def initUI(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.welcome_label = QLabel(f"Welcome, {self.username} (Admin)")
        self.welcome_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("color: white; background-color: #E74C3C; padding: 10px;")
        top_layout.addWidget(self.welcome_label)

        # Logout button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)
        layout.addLayout(top_layout)

        # Tabs
        self.tabs = QTabWidget()
        tab_names = [
            "Users", "Movies", "Reviews", "Average Ratings",
            "Top Rated Movies", "Delete/Modify User", "Delete Review"
        ]
        for name in tab_names:
            self.tabs.addTab(self.create_tab(name), name)

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_tab(self, name):
        tab = QWidget()
        layout = QVBoxLayout()

        # Special forms
        if name == "Delete/Modify User":
            form_layout = QFormLayout()
            self.user_id_input = QLineEdit()
            self.user_name_input = QLineEdit()
            self.user_admin_input = QLineEdit()
            delete_btn = QPushButton("Delete User")
            modify_btn = QPushButton("Modify User")
            delete_btn.clicked.connect(self.delete_user)
            modify_btn.clicked.connect(self.modify_user)
            form_layout.addRow("User ID:", self.user_id_input)
            form_layout.addRow("New Name:", self.user_name_input)
            form_layout.addRow("Admin (Y/N):", self.user_admin_input)
            form_layout.addRow(delete_btn, modify_btn)
            tab.setLayout(form_layout)
            return tab

        if name == "Delete Review":
            form_layout = QFormLayout()
            self.review_id_input = QLineEdit()
            delete_review_btn = QPushButton("Delete Review")
            delete_review_btn.clicked.connect(self.delete_review)
            form_layout.addRow("Review ID:", self.review_id_input)
            form_layout.addWidget(delete_review_btn)
            tab.setLayout(form_layout)
            return tab

        # Table-based tabs
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setStyleSheet("alternate-background-color: #fff0e6; background-color: #ffffff;")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        query, headers = None, []
        if name == "Users":
            query = "SELECT USER_ID, NAME, ADMIN FROM USER_TABLE"
            headers = ["User ID", "Name", "Admin"]
        elif name == "Movies":
            query = "SELECT MOVIE_ID, TITLE, RELEASE_YEAR, DURATION FROM MOVIE"
            headers = ["Movie ID", "Title", "Release Year", "Duration"]
        elif name == "Reviews":
            query = "SELECT REVIEW_ID, MOVIE_ID, USER_ID, RATING, REVIEW_TEXT FROM REVIEW"
            headers = ["Review ID", "Movie ID", "User ID", "Rating", "Text"]
        elif name == "Average Ratings":
            query = """
                SELECT m.TITLE, r.MOVIE_ID, ROUND(AVG(r.RATING), 2)
                FROM REVIEW r
                JOIN MOVIE m ON r.MOVIE_ID = m.MOVIE_ID
                GROUP BY m.TITLE, r.MOVIE_ID
            """
            headers = ["Title", "Movie ID", "Average Rating"]
        elif name == "Top Rated Movies":
            query = """
                SELECT m.TITLE, r.MOVIE_ID, ROUND(AVG(r.RATING), 2)
                FROM REVIEW r
                JOIN MOVIE m ON r.MOVIE_ID = m.MOVIE_ID
                GROUP BY m.TITLE, r.MOVIE_ID
                HAVING AVG(r.RATING) >= 4.5
            """
            headers = ["Title", "Movie ID", "Average Rating"]

        if query:
            result = fetch_cursor(query)
            if not isinstance(result, str):
                table.setColumnCount(len(result[0]) if result else len(headers))
                table.setHorizontalHeaderLabels(headers)
                table.setRowCount(len(result))
                for r_idx, row in enumerate(result):
                    for c_idx, val in enumerate(row):
                        table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

        tab.setLayout(layout)
        return tab

    # Admin actions
    def delete_user(self):
        user_id = self.user_id_input.text()
        if not user_id.isdigit():
            QMessageBox.warning(self, "Error", "User ID must be a number!")
            return
        success, msg = call_procedure("DELETE_USER", [int(user_id)])
        if success:
            QMessageBox.information(self, "Success", "User deleted successfully!")
            self.user_id_input.clear()
            self.user_name_input.clear()
            self.user_admin_input.clear()
        else:
            QMessageBox.warning(self, "Error", f"Failed: {msg}")

    def modify_user(self):
        user_id = self.user_id_input.text()
        name = self.user_name_input.text()
        admin = self.user_admin_input.text().upper()

        if not user_id.isdigit() or not name or admin not in ['Y', 'N']:
            QMessageBox.warning(self, "Error", "Enter valid User ID, Name, and Admin (Y/N)!")
            return

        success, msg = call_procedure("MODIFY_USER", [int(user_id), name, admin])
        if success:
            QMessageBox.information(self, "Success", "User modified successfully!")
            self.user_id_input.clear()
            self.user_name_input.clear()
            self.user_admin_input.clear()
        else:
            QMessageBox.warning(self, "Error", f"Failed: {msg}")

    def delete_review(self):
        review_id = self.review_id_input.text()
        if not review_id.isdigit():
            QMessageBox.warning(self, "Error", "Review ID must be a number!")
            return
        success, msg = call_procedure("DELETE_REVIEW", [int(review_id)])
        if success:
            QMessageBox.information(self, "Success", "Review deleted successfully!")
            self.review_id_input.clear()
        else:
            QMessageBox.warning(self, "Error", f"Failed: {msg}")

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #f2f2f2; }
            QTabBar::tab:selected {
                background: #ff9933;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab {
                background: #ffd699;
                padding: 6px;
            }
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)

    def logout(self):
        self.close()
        self.login = LoginPage()
        self.login.showMaximized()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginPage()
    login.showMaximized()
    sys.exit(app.exec_())