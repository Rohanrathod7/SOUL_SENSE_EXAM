import tkinter as tk
from app.ui.sidebar import SidebarNav
from app.ui.styles import UIStyles
from app.i18n_manager import get_i18n
from app.questions import load_questions
from app.auth import AuthManager
from app.logger import get_logger
from typing import Optional, Dict, Any

class AppInitializer:
    def __init__(self, app):
        self.app = app
        self.setup_ui()
        self.load_initial_data()
        self.start_login_flow()

    def setup_ui(self):
        """Set up the main UI components"""
        self.app.root.title("SoulSense AI - Mental Wellbeing")
        self.app.root.geometry("1400x900")

        # Initialize Logger
        self.app.logger = get_logger(__name__)

        # Initialize Styles
        self.app.ui_styles = UIStyles(self.app)
        self.app.colors: Dict[str, str] = {}
        self.app.ui_styles.apply_theme("dark")  # Default theme

        # Fonts
        self.app.fonts = {
            "h1": ("Segoe UI", 24, "bold"),
            "h2": ("Segoe UI", 20, "bold"),
            "h3": ("Segoe UI", 16, "bold"),
            "body": ("Segoe UI", 12),
            "small": ("Segoe UI", 10)
        }

        # State
        self.app.username: Optional[str] = None
        self.app.current_user_id: Optional[int] = None
        self.app.age = 25
        self.app.age_group = "adult"
        self.app.i18n = get_i18n()
        self.app.questions = []
        self.app.auth = AuthManager()
        self.app.settings: Dict[str, Any] = {}

        # UI Layout
        self.app.main_container = tk.Frame(self.app.root, bg=self.app.colors["bg"])
        self.app.main_container.pack(fill="both", expand=True)

        # Sidebar (Initialized but hidden until login)
        self.app.sidebar = SidebarNav(self.app.main_container, self.app, [
            {"id": "home", "label": "Home", "icon": "🏠"},
            {"id": "exam", "label": "Assessment", "icon": "🧠"},
            {"id": "dashboard", "label": "Dashboard", "icon": "📊"},
            {"id": "journal", "label": "Journal", "icon": "📝"},
            {"id": "assessments", "label": "Deep Dive", "icon": "🔍"},
            {"id": "history", "label": "History", "icon": "📚"},
        ], on_change=self.app.switch_view)

        # Content Area
        self.app.content_area = tk.Frame(self.app.main_container, bg=self.app.colors["bg"])
        self.app.content_area.pack(side="right", fill="both", expand=True)

        # Initialize Features
        self.app.exam_manager = None

    def load_initial_data(self):
        """Load initial data like questions"""
        try:
            self.app.questions = load_questions()
        except Exception as e:
            self.app.logger.error(f"Failed to load questions: {e}")
            tk.messagebox.showerror("Error", f"Could not load questions: {e}")


