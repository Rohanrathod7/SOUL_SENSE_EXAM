import tkinter as tk
from tkinter import messagebox, ttk
import logging
import sys
from datetime import datetime
import json
import os
import random
import copy

# --- NEW IMPORTS FOR GRAPHS (Upstream used Tkinter Canvas, so we stick to that for simplicity and speed) ---

from app.db import get_session
from app.models import Score, Response, User
from app.questions import load_questions
from app.utils import compute_age_group
from app.auth import AuthManager
from app import config

# ---------------- BENCHMARK DATA (From Upstream) ----------------
BENCHMARK_DATA = {
    "age_groups": {
        "Under 18": {"avg_score": 28, "std_dev": 6, "sample_size": 1200},
        "18-25": {"avg_score": 32, "std_dev": 7, "sample_size": 2500},
        "26-35": {"avg_score": 34, "std_dev": 6, "sample_size": 3200},
        "36-50": {"avg_score": 36, "std_dev": 5, "sample_size": 2800},
        "51-65": {"avg_score": 38, "std_dev": 4, "sample_size": 1800},
        "65+": {"avg_score": 35, "std_dev": 6, "sample_size": 900}
    },
    "global": {
        "avg_score": 34,
        "std_dev": 6,
        "sample_size": 12500,
        "percentiles": {
            10: 24,
            25: 29,
            50: 34,
            75: 39,
            90: 42
        }
    },
    "professions": {
        "Student": {"avg_score": 31, "std_dev": 7},
        "Professional": {"avg_score": 36, "std_dev": 5},
        "Manager": {"avg_score": 38, "std_dev": 4},
        "Healthcare": {"avg_score": 39, "std_dev": 3},
        "Education": {"avg_score": 37, "std_dev": 4},
        "Technology": {"avg_score": 33, "std_dev": 6},
        "Creative": {"avg_score": 35, "std_dev": 5},
        "Other": {"avg_score": 34, "std_dev": 6}
    }
}

# ---------------- LOGGING ----------------
logging.basicConfig(
    filename="logs/soulsense.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application started")

# ---------------- THEMES ----------------
THEMES = {
    "light": {
        "bg_primary": "#F5F7FA",
        "bg_secondary": "white",
        "text_primary": "#2C3E50",
        "text_secondary": "#555555",
        "text_input": "#34495E",
        "accent": "#2980B9",
        "success": "#2E7D32",
        "danger": "#C0392B",
        "card_bg": "white",
        "input_bg": "white",
        "input_fg": "black",
        "tooltip_bg": "#FFFFE0",
        "tooltip_fg": "black",
        # Visual Results Specific
        "chart_bg": "#ffffff",
        "chart_fg": "#000000",
        "improvement_good": "#4CAF50",
        "improvement_bad": "#F44336",
        "improvement_neutral": "#FFC107",
        "excellent": "#2196F3",
        "good": "#4CAF50",
        "average": "#FF9800",
        "needs_work": "#F44336",
        "benchmark_better": "#4CAF50",
        "benchmark_worse": "#F44336",
        "benchmark_same": "#FFC107"
    },
    "dark": {
        "bg_primary": "#121212",
        "bg_secondary": "#1e1e1e",
        "text_primary": "#ffffff",
        "text_secondary": "#e0e0e0",
        "text_input": "#f0f0f0",
        "accent": "#5DADE2",
        "success": "#58D68D",
        "danger": "#EC7063",
        "card_bg": "#1e1e1e",
        "input_bg": "#2d2d2d",
        "input_fg": "white",
        "tooltip_bg": "#333333",
        "tooltip_fg": "white",
        # Visual Results Specific
        "chart_bg": "#2e2e2e",
        "chart_fg": "#ffffff",
        "improvement_good": "#4CAF50",
        "improvement_bad": "#F44336",
        "improvement_neutral": "#FFC107",
        "excellent": "#2196F3",
        "good": "#4CAF50",
        "average": "#FF9800",
        "needs_work": "#F44336",
        "benchmark_better": "#4CAF50",
        "benchmark_worse": "#F44336",
        "benchmark_same": "#FFC107"
    }
}

class SoulSenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Soul Sense EQ Test")
        self.root.geometry("850x700") # Increased size for visual results
        
        # Load Theme
        self.current_theme_name = config.THEME
        self.colors = THEMES.get(self.current_theme_name, THEMES["light"])
        
        self.root.configure(bg=self.colors["bg_primary"])
        self.username = ""
        self.age = None
        self.education = None
        self.profession = None # Added for benchmarking
        self.age_group = None
        self.auth_manager = AuthManager()

        self.current_question = 0
        self.total_questions = 0
        self.responses = []
        
        # Scoring state
        self.current_score = 0
        self.current_max_score = 0
        self.current_percentage = 0

        self.create_login_screen()

    # ---------- HELPERS ----------
    def show_loading(self, message="Loading..."):
        """Overlay a loading screen"""
        self.loading_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        tk.Label(
            self.loading_frame,
            text="⏳",
            font=("Arial", 40),
            bg=self.colors["bg_primary"]
        ).pack(expand=True, pady=(0, 10))
        
        tk.Label(
            self.loading_frame,
            text=message,
            font=("Arial", 16),
            bg=self.colors["bg_primary"],
            fg=self.colors["text_primary"]
        ).pack(expand=True)
        
        self.root.update()

    def hide_loading(self):
        """Remove loading screen"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            del self.loading_frame

    def toggle_theme(self):
        new_theme = "dark" if self.current_theme_name == "light" else "light"
        
        # Update app state
        self.current_theme_name = new_theme
        self.colors = THEMES.get(self.current_theme_name, THEMES["light"])
        self.root.configure(bg=self.colors["bg_primary"])
        
        # Update Config
        try:
            current_config = config.load_config()
            current_config["ui"]["theme"] = new_theme
            config.save_config(current_config)
            messagebox.showinfo("Theme Changed", "Theme changed! Please restart the application to fully apply changes.")
        except Exception as e:
            logging.error(f"Failed to save theme: {e}")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            # Don't destroy loading frame if it exists
            if hasattr(self, 'loading_frame') and widget == self.loading_frame:
                continue
            widget.destroy()

    def create_widget(self, widget_type, parent, **kwargs):
        """Helper to create widgets with consistent theme styling (Merged from Upstream idea)"""
        # Set defaults based on type/theme
        if widget_type == tk.Label:
            kwargs.setdefault("bg", self.colors["bg_primary"])
            kwargs.setdefault("fg", self.colors["text_primary"])
        elif widget_type == tk.Button:
            # Buttons usually have specific classes (primary, danger), manual overrides used there
            pass 
        elif widget_type == tk.Frame:
            kwargs.setdefault("bg", self.colors["bg_primary"])
            
        return widget_type(parent, **kwargs)

    def force_exit(self):
        self.root.destroy()
        sys.exit(0)

    # ---------- SCREENS ----------
    def create_login_screen(self):
        self.clear_screen()
        
        card = tk.Frame(self.root, bg=self.colors["card_bg"], padx=30, pady=25, relief="flat", borderwidth=1)
        card.pack(pady=50)
        
        header_frame = tk.Frame(card, bg=self.colors["card_bg"])
        header_frame.pack(fill="x", pady=(0, 8))
        
        tk.Label(
            header_frame, text="🧠 Soul Sense", font=("Arial", 26, "bold"),
            bg=self.colors["card_bg"], fg=self.colors["text_primary"]
        ).pack(side="left")
        
        # Theme Toggle
        tk.Button(
            header_frame, text="🌓", command=self.toggle_theme, font=("Arial", 14),
            bg=self.colors["card_bg"], fg=self.colors["text_primary"], relief="flat", cursor="hand2"
        ).pack(side="right", padx=5)

        # Settings Button
        tk.Button(
            header_frame, text="⚙️", command=self.show_settings, font=("Arial", 14),
            bg=self.colors["card_bg"], fg=self.colors["text_primary"], relief="flat", cursor="hand2"
        ).pack(side="right", padx=5)
        
        tk.Label(
            card, text="Please login to continue", font=("Arial", 13),
            bg=self.colors["card_bg"], fg=self.colors["text_secondary"]
        ).pack(pady=(0, 20))
        
        # Form
        tk.Label(card, text="Username", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 13, "bold")).pack(anchor="w", pady=(5, 2))
        self.login_username_entry = ttk.Entry(card, font=("Arial", 14), width=30)
        self.login_username_entry.pack(pady=5)
        self.login_username_entry.focus_set()
        
        tk.Label(card, text="Password", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 13, "bold")).pack(anchor="w", pady=(5, 2))
        self.login_password_entry = ttk.Entry(card, font=("Arial", 14), width=30, show="*")
        self.login_password_entry.pack(pady=5)
        self.login_password_entry.bind('<Return>', lambda e: self.handle_login())
        
        button_frame = tk.Frame(card, bg=self.colors["card_bg"])
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame, text="Login", command=self.handle_login,
            font=("Arial", 14, "bold"), bg=self.colors["success"], fg="white",
            relief="flat", padx=20, pady=8
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            button_frame, text="Sign Up", command=self.create_signup_screen,
            font=("Arial", 14), bg=self.colors["accent"], fg="white",
            relief="flat", padx=20, pady=8
        ).pack(side="left")

    def show_settings(self):
        """Settings Window (Merged Upstream Features)"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("450x450")
        settings_win.configure(bg=self.colors["bg_primary"])
        
        x = self.root.winfo_x() + (self.root.winfo_width() - settings_win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - settings_win.winfo_height()) // 2
        settings_win.geometry(f"+{x}+{y}")
        
        tk.Label(
            settings_win, text="System Config", font=("Arial", 16, "bold"),
            bg=self.colors["bg_primary"], fg=self.colors["text_primary"]
        ).pack(pady=15)
        
        current_conf = config.load_config()

        # Question Count (Upstream Feature)
        qcount_frame = tk.Frame(settings_win, bg=self.colors["bg_primary"])
        qcount_frame.pack(pady=10, fill="x", padx=20)
        
        tk.Label(qcount_frame, text="Questions per Test:", font=("Arial", 12), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(anchor="w")
        qcount_var = tk.IntVar(value=current_conf.get("features", {}).get("question_count", 10))
        qcount_spin = tk.Spinbox(qcount_frame, from_=5, to=50, textvariable=qcount_var, font=("Arial", 12), width=10)
        qcount_spin.pack(anchor="w", pady=5)

        # Sound Effects (Upstream Feature)
        sound_var = tk.BooleanVar(value=current_conf.get("features", {}).get("sound_effects", True))
        sound_cb = tk.Checkbutton(
            settings_win, text="Enable Sound Effects (Simulated)", variable=sound_var,
            bg=self.colors["bg_primary"], fg=self.colors["text_primary"], 
            selectcolor=self.colors["bg_secondary"], activebackground=self.colors["bg_primary"],
            font=("Arial", 12)
        )
        sound_cb.pack(pady=10, anchor="w", padx=20)
        
        # Info Labels
        tk.Label(
            settings_win, text=f"Current Theme: {self.current_theme_name}",
            bg=self.colors["bg_primary"], fg=self.colors["text_secondary"]
        ).pack(pady=5)

        tk.Label(
            settings_win, text="Database: " + config.DB_FILENAME,
            bg=self.colors["bg_primary"], fg=self.colors["text_secondary"]
        ).pack(pady=5)

        def save_and_close():
            current_conf["features"]["question_count"] = qcount_var.get()
            current_conf["features"]["sound_effects"] = sound_var.get()
            config.save_config(current_conf)
            messagebox.showinfo("Saved", "Settings saved successfully.")
            settings_win.destroy()

        btn_frame = tk.Frame(settings_win, bg=self.colors["bg_primary"])
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Save & Close", command=save_and_close, bg=self.colors["success"], fg="white", font=("Arial", 11)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=settings_win.destroy, bg=self.colors["danger"], fg="white", font=("Arial", 11)).pack(side="left", padx=5)
    
    def create_signup_screen(self):
        self.clear_screen()
        card = tk.Frame(self.root, bg=self.colors["card_bg"], padx=30, pady=25)
        card.pack(pady=50)
        
        tk.Label(card, text="🧠 Create Account", font=("Arial", 26, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_primary"]).pack(pady=(0, 8))
        tk.Label(card, text="Join Soul Sense EQ Test", font=("Arial", 13), bg=self.colors["card_bg"], fg=self.colors["text_secondary"]).pack(pady=(0, 20))
        
        tk.Label(card, text="Username", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 13, "bold")).pack(anchor="w", pady=(5, 2))
        self.signup_username_entry = ttk.Entry(card, font=("Arial", 14), width=30)
        self.signup_username_entry.pack(pady=5)
        self.signup_username_entry.focus_set()
        
        tk.Label(card, text="Password", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 13, "bold")).pack(anchor="w", pady=(5, 2))
        self.signup_password_entry = ttk.Entry(card, font=("Arial", 14), width=30, show="*")
        self.signup_password_entry.pack(pady=5)
        
        tk.Label(card, text="Confirm Password", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 13, "bold")).pack(anchor="w", pady=(5, 2))
        self.signup_confirm_entry = ttk.Entry(card, font=("Arial", 14), width=30, show="*")
        self.signup_confirm_entry.pack(pady=5)
        self.signup_confirm_entry.bind('<Return>', lambda e: self.handle_signup())
        
        button_frame = tk.Frame(card, bg=self.colors["card_bg"])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Create Account", command=self.handle_signup, font=("Arial", 14, "bold"), bg=self.colors["success"], fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=(0, 10))
        tk.Button(button_frame, text="Back to Login", command=self.create_login_screen, font=("Arial", 14), bg="#757575", fg="white", relief="flat", padx=20, pady=8).pack(side="left")
    
    def handle_login(self):
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return
        success, message = self.auth_manager.login_user(username, password)
        if success:
            self.username = username
            logging.info(f"User logged in: {username}")
            self.create_username_screen()
        else:
            messagebox.showerror("Login Failed", message)
    
    def handle_signup(self):
        username = self.signup_username_entry.get().strip()
        password = self.signup_password_entry.get()
        confirm_password = self.signup_confirm_entry.get()
        if not username or not password or not confirm_password:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return
        if password != confirm_password:
            messagebox.showwarning("Input Error", "Passwords do not match.")
            return
        success, message = self.auth_manager.register_user(username, password)
        if success:
            messagebox.showinfo("Success", "Account created successfully! Please login.")
            self.create_login_screen()
        else:
            messagebox.showerror("Registration Failed", message)
    
    def handle_logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.auth_manager.logout_user()
            self.username = ""
            logging.info("User logged out")
            self.create_login_screen()

    def create_username_screen(self):
        self.clear_screen()
        card = tk.Frame(self.root, bg=self.colors["card_bg"], padx=30, pady=25)
        card.pack(pady=30)

        tk.Label(card, text="🧠 Soul Sense EQ Test", font=("Arial", 22, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_primary"]).pack(pady=(0, 8))
        
        logout_frame = tk.Frame(card, bg=self.colors["card_bg"])
        logout_frame.pack(fill="x", pady=(0, 10))
        tk.Label(logout_frame, text=f"Logged in as: {self.username}", bg=self.colors["card_bg"], fg=self.colors["text_secondary"], font=("Arial", 10)).pack(side="left")
        tk.Button(logout_frame, text="Logout", command=self.handle_logout, font=("Arial", 10), bg=self.colors["danger"], fg="white", relief="flat", padx=15, pady=5).pack(side="right")
        
        # View History Option (Merged from Upstream & Local)
        tk.Button(logout_frame, text="History", command=self.show_history_screen, font=("Arial", 10), bg=self.colors["accent"], fg="white", relief="flat", padx=15, pady=5).pack(side="right", padx=5)

        tk.Label(card, text="Enter Name", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 2))
        self.name_entry = ttk.Entry(card, font=("Arial", 12), width=30)
        self.name_entry.insert(0, self.username)
        self.name_entry.configure(state='readonly')
        self.name_entry.pack(pady=5)

        tk.Label(card, text="Enter Age", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 2))
        self.age_entry = ttk.Entry(card, font=("Arial", 12), width=30)
        self.age_entry.pack(pady=5)

        # Profession Input (Upstream Feature)
        tk.Label(card, text="Your Profession (Optional)", bg=self.colors["card_bg"], fg=self.colors["text_input"], font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 2))
        
        self.profession_var = tk.StringVar()
        professions = ["Student", "Professional", "Manager", "Healthcare", "Education", "Technology", "Creative", "Other"]
        # Use simple OptionMenu consistent with theme
        prof_menu = tk.OptionMenu(card, self.profession_var, *professions)
        prof_menu.config(width=25, font=("Arial", 12), bg=self.colors["bg_primary"], fg=self.colors["text_primary"])
        prof_menu.pack(pady=5)

        tk.Button(card, text="Start EQ Test →", command=self.start_test, font=("Arial", 12, "bold"), bg=self.colors["success"], fg="white", relief="flat", padx=20, pady=8).pack(pady=25)

    def validate_age_input(self, age_str):
        if not age_str: return False, None, "Please enter your age."
        try:
            val = int(age_str)
            if val <= 0: return False, None, "Age must be positive."
            if val > 120: return False, None, "Age implies you are a vampire/ghost."
            return True, val, None
        except ValueError:
            return False, None, "Age must be numeric."

    def start_test(self):
        self.username = self.name_entry.get().strip()
        age_str = self.age_entry.get().strip()
        self.profession = self.profession_var.get() if self.profession_var.get() else None # Capture profession
        
        ok, age, err = self.validate_age_input(age_str)
        if not ok:
            messagebox.showwarning("Input Error", err)
            return
            
        self.age = age
        self.age_group = compute_age_group(age)

        # Loading Indicator (My Feature)
        self.show_loading("Loading Questions...")
        
        try:
            # Respect "question_count" setting
            try:
                conf = config.load_config()
                limit = conf.get("features", {}).get("question_count", 10)
            except:
                limit = 10

            rows = load_questions(age=self.age) # [(id, text, tooltip)]
            
            # Shuffle and limit
            questions_subset = rows[:]
            random.shuffle(questions_subset)
            questions_subset = questions_subset[:limit]

            self.questions = [(q[1], q[2]) for q in questions_subset]
            self.total_questions = len(self.questions)
            self.current_question = 0 # Reset counter
            self.responses = [] # Reset responses

            if not self.questions:
                raise RuntimeError("No questions loaded")
        except Exception:
            self.hide_loading()
            logging.error("Failed to load questions", exc_info=True)
            messagebox.showerror("Error", "No questions available for your age group.")
            return

        self.hide_loading()
        logging.info("Session started | user=%s | age=%s | profession=%s", self.username, self.age, self.profession)
        self.show_question()

    def show_question(self):
        self.clear_screen()
        
        if self.current_question >= len(self.questions):
            self.finish_test()
            return

        q_text, q_tooltip = self.questions[self.current_question]
        
        question_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        question_frame.pack(pady=20)
        
        # Question Counter (Upstream feature)
        tk.Label(
            question_frame, text=f"Question {self.current_question + 1} of {len(self.questions)}",
            font=("Arial", 10), bg=self.colors["bg_primary"], fg=self.colors["text_secondary"]
        ).pack(pady=(0, 10))

        tk.Label(
            question_frame,
            text=f"Q{self.current_question + 1}: {q_text}",
            wraplength=600,
            font=("Arial", 14),
            bg=self.colors["bg_primary"],
            fg=self.colors["text_primary"]
        ).pack(side="left")
        
        if q_tooltip:
            # Accessibility: Button not Label
            tooltip_btn = tk.Button(
                question_frame,
                text="ℹ️",
                font=("Arial", 14),
                fg=self.colors["accent"],
                bg=self.colors["bg_primary"],
                activebackground=self.colors["bg_secondary"],
                relief="flat",
                cursor="hand2",
                command=lambda: self.toggle_tooltip(q_tooltip, question_frame),
                highlightthickness=2, highlightcolor=self.colors["accent"]
            )
            tooltip_btn.pack(side="left", padx=5)
            tooltip_btn.bind("<Enter>", lambda e: self.show_tooltip_popup(e, q_tooltip))
            tooltip_btn.bind("<Leave>", lambda e: self.hide_tooltip_popup())

        self.answer_var = tk.IntVar()
        
        for val, txt in enumerate(["Never", "Sometimes", "Often", "Always"], 1):
             tk.Radiobutton(
                self.root,
                text=f"{txt} ({val})",
                variable=self.answer_var,
                value=val,
                font=("Arial", 14), 
                bg=self.colors["bg_primary"],
                fg=self.colors["text_primary"],
                selectcolor=self.colors["bg_secondary"],
                activebackground=self.colors["bg_primary"],
                highlightthickness=2, highlightcolor=self.colors["accent"]
            ).pack(anchor="w", padx=100, pady=10)

        # Nav Buttons
        btn_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        btn_frame.pack(pady=15)
        
        # Next Button
        next_btn = tk.Button(
            btn_frame, 
            text="Next", 
            command=self.save_answer, 
            font=("Arial", 12, "bold"), 
            bg=self.colors["success"], 
            fg="white", 
            padx=20,
            highlightthickness=2, highlightcolor=self.colors["accent"]
        )
        next_btn.pack(side="left")
        
        self.root.bind('<Return>', lambda e: self.save_answer())
        next_btn.focus_set()

    def toggle_tooltip(self, text, parent):
        messagebox.showinfo("Tip", text)
        
    def show_tooltip_popup(self, event, text):
        self.tooltip_w = tk.Toplevel(self.root)
        self.tooltip_w.wm_overrideredirect(True)
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 20
        self.tooltip_w.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip_w, text=text, bg=self.colors["tooltip_bg"], fg=self.colors["tooltip_fg"], relief="solid", borderwidth=1, padx=5, pady=3).pack()

    def hide_tooltip_popup(self):
        if hasattr(self, 'tooltip_w'): self.tooltip_w.destroy()

    def save_answer(self):
        try:
            ans = self.answer_var.get()
            if ans == 0:
                messagebox.showwarning("Input Error", "Please select an answer.")
                return
        except: return

        self.responses.append(ans)
        
        # Save response to DB (Using ORM)
        session = get_session()
        try:
            response = Response(
                username=self.username,
                question_id=self.current_question + 1,
                response_value=ans,
                age_group=self.age_group,
                timestamp=datetime.utcnow().isoformat()
            )
            session.add(response)
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()

        self.current_question += 1
        self.show_question()

    def finish_test(self):
        # Loading Indicator
        self.show_loading("Analyzing Emotional Intelligence...")
        self.root.after(100, self._process_results)

    def _process_results(self):
        # Calculate scores
        self.current_score = sum(self.responses)
        self.current_max_score = len(self.responses) * 4
        if self.current_max_score > 0:
            self.current_percentage = (self.current_score / self.current_max_score) * 100
        else:
            self.current_percentage = 0

        # Save Score to DB (ORM)
        session = get_session()
        try:
            score = Score(
                username=self.username,
                age=self.age,
                total_score=self.current_score
            )
            session.add(score)
            session.commit()
        except Exception:
            logging.error("Failed to store final score", exc_info=True)
            session.rollback()
        finally:
            session.close()
            
        self.hide_loading()
        # Navigate to Detailed Visual Results (Merged from Upstream)
        self.show_visual_results()

    # ---------------- INTEGRATED UPSTREAM VISUAL FEATURES ----------------

    def calculate_percentile(self, score, avg_score, std_dev):
        """Calculate percentile based on normal distribution (Upstream logic)"""
        if std_dev == 0:
            return 50 if score == avg_score else (100 if score > avg_score else 0)
        z_score = (score - avg_score) / std_dev
        
        if z_score <= -2.5: percentile = 1
        elif z_score <= -2.0: percentile = 2
        elif z_score <= -1.5: percentile = 7
        elif z_score <= -1.0: percentile = 16
        elif z_score <= -0.5: percentile = 31
        elif z_score <= 0: percentile = 50
        elif z_score <= 0.5: percentile = 69
        elif z_score <= 1.0: percentile = 84
        elif z_score <= 1.5: percentile = 93
        elif z_score <= 2.0: percentile = 98
        elif z_score <= 2.5: percentile = 99
        else: percentile = 99.5
        return percentile

    def get_benchmark_comparison(self):
        """Get benchmark comparisons for the current score"""
        comparisons = {}
        # Global comparison
        global_bench = BENCHMARK_DATA["global"]
        comparisons["global"] = {
            "avg_score": global_bench["avg_score"],
            "difference": self.current_score - global_bench["avg_score"],
            "percentile": self.calculate_percentile(self.current_score, global_bench["avg_score"], global_bench["std_dev"]),
            "sample_size": global_bench["sample_size"]
        }
        # Age group comparison
        if self.age_group and self.age_group in BENCHMARK_DATA["age_groups"]:
            age_bench = BENCHMARK_DATA["age_groups"][self.age_group]
            comparisons["age_group"] = {
                "group": self.age_group,
                "avg_score": age_bench["avg_score"],
                "difference": self.current_score - age_bench["avg_score"],
                "percentile": self.calculate_percentile(self.current_score, age_bench["avg_score"], age_bench["std_dev"]),
                "sample_size": age_bench["sample_size"]
            }
        # Profession comparison
        if self.profession and self.profession in BENCHMARK_DATA["professions"]:
            prof_bench = BENCHMARK_DATA["professions"][self.profession]
            comparisons["profession"] = {
                "profession": self.profession,
                "avg_score": prof_bench["avg_score"],
                "difference": self.current_score - prof_bench["avg_score"],
                "percentile": self.calculate_percentile(self.current_score, prof_bench["avg_score"], prof_bench["std_dev"])
            }
        return comparisons

    def create_benchmark_chart(self, parent, comparisons):
        """Create a visual benchmark comparison chart using Canvas"""
        chart_frame = tk.Frame(parent, bg=self.colors["bg_primary"])
        chart_frame.pack(fill="x", pady=10)
        
        tk.Label(chart_frame, text="Benchmark Comparison", font=("Arial", 12, "bold"), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(anchor="w", pady=5)
        
        chart_canvas = tk.Canvas(chart_frame, height=150, bg=self.colors["chart_bg"], highlightthickness=0)
        chart_canvas.pack(fill="x", pady=10)
        
        # Prepare data
        chart_data = []
        if "global" in comparisons:
            chart_data.append(("Global", comparisons["global"]["avg_score"], self.current_score))
        if "age_group" in comparisons:
            chart_data.append((comparisons["age_group"]["group"], comparisons["age_group"]["avg_score"], self.current_score))
        if "profession" in comparisons:
            chart_data.append((comparisons["profession"]["profession"], comparisons["profession"]["avg_score"], self.current_score))
            
        if not chart_data: return chart_frame

        # Drawing params
        num_bars = len(chart_data)
        bar_width = 80
        spacing = 40
        start_x = 50
        max_val = max([max(d[1], d[2]) for d in chart_data] + [40]) # Max score of 40 is roughly standard for 10q * 4
        # Adjust max_val if questions vary, but keeping simple for now
        max_val = max(max_val, self.total_questions * 4 if self.total_questions else 40)

        scale_factor = 100 / max(1, max_val)

        for i, (label, avg, your) in enumerate(chart_data):
            x = start_x + i * (bar_width * 2 + spacing)
            
            # Your Score Bar
            your_h = your * scale_factor
            y_your = 130 - your_h
            chart_canvas.create_rectangle(x, y_your, x + bar_width, 130, fill=self.colors["benchmark_better"], outline="black")
            chart_canvas.create_text(x + bar_width/2, y_your - 10, text=f"You: {your}", fill=self.colors["chart_fg"], font=("Arial", 8, "bold"))

            # Avg Score Bar
            avg_h = avg * scale_factor
            y_avg = 130 - avg_h
            chart_canvas.create_rectangle(x + bar_width, y_avg, x + bar_width*2, 130, fill="#888888", outline="black")
            chart_canvas.create_text(x + bar_width*1.5, y_avg - 10, text=f"Avg: {avg}", fill=self.colors["chart_fg"], font=("Arial", 8, "bold"))
            
            # Label
            chart_canvas.create_text(x + bar_width, 145, text=label, fill=self.colors["chart_fg"], font=("Arial", 9))

        return chart_frame

    def show_visual_results(self):
        """Show detailed visual results (Merged Upstream Implementation)"""
        self.clear_screen()
        
        comparisons = self.get_benchmark_comparison()
        
        # Scrollable Frame Pattern
        canvas = tk.Canvas(self.root, bg=self.colors["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg_primary"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Content
        tk.Label(scrollable_frame, text=f"Results for {self.username}", font=("Arial", 22, "bold"), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(pady=20)
        
        # Score Big
        tk.Label(scrollable_frame, text=f"{self.current_score} / {self.current_max_score}", font=("Arial", 40, "bold"), bg=self.colors["bg_primary"], fg=self.colors["excellent"]).pack()
        tk.Label(scrollable_frame, text=f"{self.current_percentage:.1f}%", font=("Arial", 20), bg=self.colors["bg_primary"], fg=self.colors["text_secondary"]).pack()
        
        # Progress Bar
        bar_frame = tk.Frame(scrollable_frame, bg=self.colors["bg_primary"])
        bar_frame.pack(pady=10)
        bar = tk.Canvas(bar_frame, width=500, height=30, bg="white", highlightthickness=0)
        bar.pack()
        
        fill_w = (self.current_percentage / 100.0) * 500
        color = self.colors["improvement_good"] if self.current_percentage >= 65 else self.colors["improvement_bad"]
        bar.create_rectangle(0, 0, 500, 30, fill="#e0e0e0", outline="")
        bar.create_rectangle(0, 0, fill_w, 30, fill=color, outline="")
        
        # Interpret Text
        interpret = "Excellent" if self.current_percentage >= 80 else "Good" if self.current_percentage >= 65 else "Average" if self.current_percentage >= 50 else "Needs Work"
        tk.Label(scrollable_frame, text=f"Rating: {interpret}", font=("Arial", 16), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(pady=10)
        
        # Benchmarks
        self.create_benchmark_chart(scrollable_frame, comparisons)
        
         # Buttons
        btn_frame = tk.Frame(scrollable_frame, bg=self.colors["bg_primary"])
        btn_frame.pack(pady=30)
        
        tk.Button(btn_frame, text="Comparison History", command=self.show_comparison_screen, font=("Arial", 12), bg=self.colors["accent"], fg="white").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Main Menu", command=self.create_username_screen, font=("Arial", 12), bg=self.colors["text_secondary"], fg="white").pack(side="left", padx=10)

    def show_history_screen(self):
        """History List (Updated to match Upstream visual style but with SQLAlchemy)"""
        self.clear_screen()
        
        header_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        header_frame.pack(fill="x", pady=10)
        tk.Button(header_frame, text="← Back", command=self.create_username_screen, font=("Arial", 10)).pack(side="left", padx=10)
        tk.Label(header_frame, text=f"History: {self.username}", font=("Arial", 16, "bold"), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(side="left", padx=20)
        
        session = get_session()
        try:
            scores_data = session.query(Score).filter_by(username=self.username).order_by(Score.id.desc()).all()
        finally:
            session.close()

        if not scores_data:
            tk.Label(self.root, text="No history found.", bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(pady=50)
            return

        # List
        canvas = tk.Canvas(self.root, bg=self.colors["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_primary"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        for s in scores_data:
            f = tk.Frame(scroll_frame, bg="white", pady=10, padx=10, relief="groove", bd=1)
            f.pack(fill="x", pady=5)
            
            # Info
            info_frame = tk.Frame(f, bg="white")
            info_frame.pack(fill="x")
            tk.Label(info_frame, text=f"Test #{s.id}", font=("Arial", 11, "bold"), bg="white").pack(side="left")
            tk.Label(info_frame, text=f"Score: {s.total_score}", font=("Arial", 11), bg="white").pack(side="right")
            
            # Simple bar
            max_s = 40 # approx
            pct = (s.total_score / max_s) * 100
            if pct > 100: pct = 100
            
            c = tk.Canvas(f, height=10, bg="#eee", highlightthickness=0)
            c.pack(fill="x", pady=5)
            c.create_rectangle(0, 0, pct*4, 10, fill=self.colors["excellent"] if pct > 80 else self.colors["good"]) # Width scaling is rough

    def show_comparison_screen(self):
        """Show visual comparison of tests (Merged Upstream Feature)"""
        self.clear_screen()
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        header_frame.pack(fill="x", pady=10)
        tk.Button(header_frame, text="← Back", command=self.show_visual_results, font=("Arial", 10)).pack(side="left", padx=10)
        tk.Label(header_frame, text=f"Progress Trend for {self.username}", font=("Arial", 16, "bold"), bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(side="left")

        session = get_session()
        try:
            scores_data = session.query(Score).filter_by(username=self.username).order_by(Score.id.asc()).all()
        finally:
            session.close()

        if len(scores_data) < 2:
            tk.Label(self.root, text="Need at least 2 tests to show trends.", bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(pady=50)
            return

        # Simple Bar Chart
        chart_h = 400
        chart_w = 600
        canvas = tk.Canvas(self.root, width=chart_w, height=chart_h, bg=self.colors["bg_primary"], highlightthickness=0)
        canvas.pack(pady=20)
        
        # Draw bars
        bar_w = 40
        space = 20
        start_x = 50
        max_score = 40 # Standardize
        
        scale = (chart_h - 50) / max_score
        
        for i, s in enumerate(scores_data[-10:]): # Show last 10
            h = s.total_score * scale
            x = start_x + i * (bar_w + space)
            y = chart_h - h - 30
            
            color = self.colors["average"]
            if i > 0 and s.total_score > scores_data[i-1].total_score: color = self.colors["improvement_good"]
            elif i > 0 and s.total_score < scores_data[i-1].total_score: color = self.colors["improvement_bad"]
            
            canvas.create_rectangle(x, y, x + bar_w, chart_h - 30, fill=color, outline="black")
            canvas.create_text(x + bar_w/2, y - 10, text=str(s.total_score), fill=self.colors["text_primary"])
            canvas.create_text(x + bar_w/2, chart_h - 10, text=f"#{s.id}", fill=self.colors["text_secondary"])

if __name__ == "__main__":
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root)
    
    def launch_main_app():
        splash.root.destroy()
        root = tk.Tk()
        app = SoulSenseApp(root)
        root.mainloop()

    splash.close_after_delay(2000, launch_main_app)
    splash_root.mainloop()
