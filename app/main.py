import signal
import atexit
import tkinter as tk
from tkinter import messagebox
import logging
from app.ui.app_initializer import AppInitializer
from app.ui.view_manager import ViewManager
from app.auth.app_auth import AppAuth
from app.shutdown_handler import ShutdownHandler
from app.ui.styles import UIStyles
from app.startup_checks import run_all_checks, get_check_summary, CheckStatus
from app.exceptions import IntegrityError
from app.logger import setup_logging
from app.error_handler import setup_global_exception_handlers
from app.questions import initialize_questions
from typing import Optional, Dict, Any
from app.error_handler import get_error_handler, ErrorSeverity
from app.logger import get_logger
from app.i18n_manager import get_i18n
from app.auth import AuthManager
from app.questions import load_questions
from app.ui.sidebar import SidebarNav
from app.ui.assessments import AssessmentHub
from app.ui.exam import ExamManager
from app.ui.dashboard import AnalyticsDashboard
from app.ui.journal import JournalFeature

class SoulSenseApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SoulSense AI - Mental Wellbeing")
        self.root.geometry("1400x900")
        
        # Initialize Logger (use centralized logger)
        self.logger = get_logger(__name__)
        
        # Initialize Styles
        self.ui_styles = UIStyles(self)
        self.colors: Dict[str, str] = {} # Will be populated by apply_theme
        self.ui_styles.apply_theme("dark") # Default theme
        
        # Fonts
        self.fonts = {
            "h1": ("Segoe UI", 24, "bold"),
            "h2": ("Segoe UI", 20, "bold"),
            "h3": ("Segoe UI", 16, "bold"),
            "body": ("Segoe UI", 12),
            "small": ("Segoe UI", 10)
        }
        
        # State
        self.username: Optional[str] = None # Set after login
        self.current_user_id: Optional[int] = None
        self.age = 25
        self.age_group = "adult"
        self.i18n = get_i18n()
        self.questions = []
        self.auth = AuthManager()
        self.settings: Dict[str, Any] = {} 
        
        # Load Questions
        try:
            self.questions = load_questions()
        except Exception as e:
            self.logger.error(f"Failed to load questions: {e}")
            messagebox.showerror("Error", f"Could not load questions: {e}")
        
        # --- UI Layout ---
        self.main_container = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar (Initialized but hidden until login)
        # Sidebar (Initialized but hidden until login)
        self.sidebar = SidebarNav(self.main_container, self, [
            {"id": "home", "label": "Home", "icon": "🏠"},
            {"id": "exam", "label": "Assessment", "icon": "🧠"},
            {"id": "dashboard", "label": "Dashboard", "icon": "📊"},
            {"id": "journal", "label": "Journal", "icon": "📝"},
            {"id": "assessments", "label": "Deep Dive", "icon": "🔍"},
            {"id": "history", "label": "History", "icon": "�"}, # Replaces Profile
        ], on_change=self.switch_view)
        # self.sidebar.pack(side="left", fill="y") # Don't pack yet
        
        # Content Area
        self.content_area = tk.Frame(self.main_container, bg=self.colors["bg"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Initialize Features
        self.exam_manager = None
        self.view_manager = ViewManager(self)

        # Start Login Flow
        self.root.after(100, self.show_login_screen)

    def show_login_screen(self) -> None:
        """Delegate to AppAuth"""
        self.auth_handler.show_login_screen()

    def _load_user_settings(self, username: str) -> None:
        """Load settings from DB for user"""
        try:
            from app.db import get_session
            from app.models import User
            
            session = get_session()
            user_obj = session.query(User).filter_by(username=username).first()
            if user_obj:
                self.current_user_id = int(user_obj.id)
                if user_obj.settings:
                    self.settings = {
                        "theme": user_obj.settings.theme,
                        "question_count": user_obj.settings.question_count,
                        "sound_enabled": user_obj.settings.sound_enabled
                    }
                    # Apply Theme immediately
                    if self.settings.get("theme"):
                        self.apply_theme(self.settings["theme"])
            session.close()
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")

    def _post_login_init(self) -> None:
        """Initialize UI after login"""
        if hasattr(self, 'sidebar'):
            self.sidebar.update_user_info()
            self.sidebar.pack(side="left", fill="y")
            # Select Home to trigger view and visual update
            self.sidebar.select_item("home") # This triggers on_change -> switch_view, which is fine for init
        else:
            self.switch_view("home")

    def center_window(self, window, width, height):
        """Center a window on the screen"""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def apply_theme(self, theme_name: str) -> None:
        """Update colors based on theme"""
        # Delegate to UIStyles manager
        self.ui_styles.apply_theme(theme_name)

        # Refresh current view
        # A full restart might be best, but we'll try to update existing frames
        self.main_container.configure(bg=self.colors["bg"])
        self.content_area.configure(bg=self.colors["bg"])

        # Update Sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.update_theme()

        # Refresh current content (re-render)
        # This is strictly necessary to apply new colors to inner widgets
        # We can implement a specific update hook or just switch view (reloads it)
        # Determine current view from sidebar if possible, or track it.
        if hasattr(self, 'current_view') and self.current_view:
             self.switch_view(self.current_view)
        elif hasattr(self, 'sidebar') and self.sidebar.active_id:
             self.switch_view(self.sidebar.active_id)

        


    def switch_view(self, view_id):
        """Delegate view switching to ViewManager"""
        self.view_manager.switch_view(view_id)

    def show_history(self):
        """Delegate to ViewManager"""
        self.view_manager.show_history()

    def clear_screen(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def show_assessments(self):
        """Show Assessment Selection Hub"""
        self.clear_screen()
        hub = AssessmentHub(self.content_area, self)
        hub.render()



    def start_exam(self):
        """Delegate to ViewManager"""
        self.view_manager.start_exam()

    def show_dashboard(self):
        """Delegate to ViewManager"""
        self.view_manager.show_dashboard()

    def show_journal(self):
        """Delegate to ViewManager"""
        self.view_manager.show_journal()

    def show_profile(self):
        """Delegate to ViewManager"""
        self.view_manager.show_profile()

    def _do_logout(self) -> None:
        """Clear user session and show login screen."""
        # Clear user state
        self.username = None
        self.current_user_id = None
        self.settings = {}
        
        # Hide sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.pack_forget()
        
        # Clear content area
        self.clear_screen()
        
        # Show login screen
        self.show_login_screen()

    def graceful_shutdown(self) -> None:
        """Perform graceful shutdown operations"""
        self.logger.info("Initiating graceful application shutdown...")

        try:
            # Commit any pending database operations from the scoped session
            from app.db import SessionLocal
            session = SessionLocal()
            if session:
                session.commit()
                SessionLocal.remove()  # Remove the session from the scoped registry
                self.logger.info("Database session committed and removed successfully")
        except Exception as e:
            self.logger.error(f"Error during database shutdown: {e}")

        # Log shutdown
        self.logger.info("Application shutdown complete")

        # Destroy the root window to exit
        if hasattr(self, 'root') and self.root:
            try:
                self.root.destroy()
            except Exception:
                pass  # Window already destroyed

# --- Global Error Handlers ---

def show_error(title, message, exception=None):
    """Global error display function"""
    if exception:
        logging.error(f"{title}: {message} - {exception}")
    else:
        logging.error(f"{title}: {message}")
        
    try:
        messagebox.showerror(title, message)
    except:
        print(f"CRITICAL ERROR (No GUI): {title} - {message}")

def global_exception_handler(self, exc_type, exc_value, traceback_obj):
    """Handle uncaught exceptions"""
    import traceback
    traceback_str = "".join(traceback.format_exception(exc_type, exc_value, traceback_obj))
    logging.critical(f"Uncaught Exception: {traceback_str}")
    show_error("Unexpected Error", f"An unexpected error occurred:\n{exc_value}", exception=traceback_str)


if __name__ == "__main__":
    # Setup centralized logging and error handling
    setup_logging()
    setup_global_exception_handlers()
    
    try:
        # Run startup integrity checks before initializing the app
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        try:
            results = run_all_checks(raise_on_critical=True)
            summary = get_check_summary(results)
            logger.info(summary)
            
            # Show warning dialog if there were any warnings
            warnings = [r for r in results if r.status == CheckStatus.WARNING]
            if warnings:
                # Create a temporary root for the warning dialog
                temp_root = tk.Tk()
                temp_root.withdraw()
                warning_msg = "\n".join([f"• {r.name}: {r.message}" for r in warnings])
                messagebox.showwarning(
                    "Startup Warnings",
                    f"The application started with the following warnings:\n\n{warning_msg}\n\nThe application will continue with default settings."
                )
                temp_root.destroy()
                
        except IntegrityError as e:
            # Critical failure - show error and exit
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror(
                "Startup Failed",
                f"Critical integrity check failed:\n\n{str(e)}\n\nThe application cannot start."
            )
            temp_root.destroy()
            raise SystemExit(1)
        
        # All checks passed, start the application
        
        # Initialize Questions Cache (Preload)
        from app.questions import initialize_questions
        logger.info("Preloading questions into memory...")
        if not initialize_questions():
            logger.warning("Initial question preload failed. Application will attempt lazy-loading.")

        root = tk.Tk()
        
        # Register tkinter-specific exception handler
        def tk_report_callback_exception(exc_type, exc_value, exc_tb):
            """Handle exceptions in tkinter callbacks."""
            handler = get_error_handler()
            handler.log_error(
                exc_value,
                module="tkinter",
                operation="callback",
                severity=ErrorSeverity.HIGH
            )
            user_msg = handler.get_user_message(exc_value)
            show_error("Interface Error", user_msg, exc_value)
        
        root.report_callback_exception = tk_report_callback_exception
        
        app = SoulSenseApp(root)

        # Set up graceful shutdown handlers
        root.protocol("WM_DELETE_WINDOW", app.graceful_shutdown)

        # Signal handlers for SIGINT (Ctrl+C) and SIGTERM
        def signal_handler(signum, frame):
            app.logger.info(f"Received signal {signum}, initiating shutdown")
            app.graceful_shutdown()

        signal.signal(signal.SIGINT, signal_handler)

        # Try to register SIGTERM handler, but don't fail if it's not available
        try:
            signal.signal(signal.SIGTERM, signal_handler)
        except (AttributeError, ValueError, OSError):
            # SIGTERM may not be available on some platforms (e.g., older Windows)
            app.logger.debug("SIGTERM not available on this platform, skipping registration")

        # Register atexit handler as backup
        atexit.register(app.graceful_shutdown)

        root.mainloop()
        
    except SystemExit:
        pass  # Clean exit from integrity failure
    except Exception as e:
        import traceback
        handler = get_error_handler()
        handler.log_error(e, module="main", operation="startup", severity=ErrorSeverity.CRITICAL)
        traceback.print_exc()

