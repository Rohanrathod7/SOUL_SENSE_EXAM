import tkinter as tk
from tkinter import messagebox
from app.utils import save_settings

class SettingsManager:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        
    def show_settings(self):
        """Show settings configuration window"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x400")
        
        # Apply theme to settings window
        settings_win.configure(bg=self.app.colors["bg"])
        
        # Center window
        settings_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - settings_win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - settings_win.winfo_height()) // 2
        settings_win.geometry(f"+{x}+{y}")
        
        # Title
        title = tk.Label(
            settings_win,
            text="Configure Test Settings",
            font=("Arial", 16, "bold"),
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"]
        )
        title.pack(pady=15)
        
        # Question Count
        qcount_frame = tk.Frame(settings_win, bg=self.app.colors["bg"])
        qcount_frame.pack(pady=10, fill="x", padx=20)
        
        qcount_label = tk.Label(
            qcount_frame,
            text="Number of Questions:",
            font=("Arial", 12),
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"]
        )
        qcount_label.pack(anchor="w")
        
        self.app.qcount_var = tk.IntVar(value=self.app.settings.get("question_count", 10))
        # Need access to total questions count. 
        # app.questions is the *subset*. We need the total.
        # In main.py, all_questions variable was local to the script/global scope but not strictly on 'app' usually?
        # Checking main.py: "all_questions = [...]" is global.
        # But 'app' might not have it invalid access.
        # We can pass total_questions via app if we attached it, or just use a safe max.
        # Let's check if 'all_questions' is attached to 'app' or available.
        # It seems 'app.questions' is the SUBSET. 'all_questions' was a global in main.py.
        # We should probably attach 'all_questions_count' to app or just assume 50 for now/check main.py again.
        
        # Wait, in main.py: "self.questions = all_questions[:min(...)]"
        # It doesn't seem to store all_questions on 'self'.
        # I should modify main.py to store 'self.all_questions_count' or reference it.
        # For now, I will use a reasonable default max (e.g. 50) or try to read it if I add it.
        # Or better: let's not break dependencies. The original code used 'all_questions' from global scope!
        # "to=min(50, len(all_questions))"
        # We need to solve this dependency.
        
        max_questions = 50 # Default fallback
        if hasattr(self.app, 'total_questions_count'):
             max_questions = min(50, self.app.total_questions_count)
             
        qcount_spin = tk.Spinbox(
            qcount_frame,
            from_=5,
            to=max_questions, 
            textvariable=self.app.qcount_var,
            font=("Arial", 12),
            width=10,
            bg=self.app.colors["entry_bg"],
            fg=self.app.colors["entry_fg"],
            buttonbackground=self.app.colors["button_bg"]
        )
        qcount_spin.pack(anchor="w", pady=5)
        
        # Theme Selection
        theme_frame = tk.Frame(settings_win, bg=self.app.colors["bg"])
        theme_frame.pack(pady=10, fill="x", padx=20)
        
        theme_label = tk.Label(
            theme_frame,
            text="Theme:",
            font=("Arial", 12),
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"]
        )
        theme_label.pack(anchor="w")
        
        self.app.theme_var = tk.StringVar(value=self.app.settings.get("theme", "light"))
        
        theme_light = tk.Radiobutton(
            theme_frame,
            text="Light Theme",
            variable=self.app.theme_var,
            value="light",
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"],
            selectcolor=self.app.colors["bg"],
            activebackground=self.app.colors["bg"],
            activeforeground=self.app.colors["fg"]
        )
        theme_light.pack(anchor="w", pady=2)
        
        theme_dark = tk.Radiobutton(
            theme_frame,
            text="Dark Theme",
            variable=self.app.theme_var,
            value="dark",
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"],
            selectcolor=self.app.colors["bg"],
            activebackground=self.app.colors["bg"],
            activeforeground=self.app.colors["fg"]
        )
        theme_dark.pack(anchor="w", pady=2)
        
        # Sound Effects
        sound_frame = tk.Frame(settings_win, bg=self.app.colors["bg"])
        sound_frame.pack(pady=10, fill="x", padx=20)
        
        self.app.sound_var = tk.BooleanVar(value=self.app.settings.get("sound_effects", True))
        sound_cb = tk.Checkbutton(
            sound_frame,
            text="Enable Sound Effects",
            variable=self.app.sound_var,
            bg=self.app.colors["bg"],
            fg=self.app.colors["fg"],
            selectcolor=self.app.colors["bg"],
            activebackground=self.app.colors["bg"],
            activeforeground=self.app.colors["fg"]
        )
        sound_cb.pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(settings_win, bg=self.app.colors["bg"])
        btn_frame.pack(pady=20)
        
        def apply_settings():
            """Apply and save settings"""
            new_settings = {
                "question_count": self.app.qcount_var.get(),
                "theme": self.app.theme_var.get(),
                "sound_effects": self.app.sound_var.get()
            }
            
            # Save settings
            self.app.settings.update(new_settings)
            
            # Update app questions - Delegate this back to app to handle logic? 
            # Or just do it here if we assume 'load_questions' behavior availability.
            # The original code did:
            # question_count = new_settings["question_count"]
            # self.questions = all_questions[:min(question_count, len(all_questions))]
            # We can expose a method on app: self.app.reload_questions(count)
            
            if save_settings(self.app.settings):
                # Apply theme immediately
                self.app.apply_theme(new_settings["theme"])
                
                # Reload questions logic needs to be on App side to access source of truth
                if hasattr(self.app, 'reload_questions'):
                    self.app.reload_questions(new_settings["question_count"])
                
                messagebox.showinfo("Success", "Settings saved successfully!")
                settings_win.destroy()
                # Recreate welcome screen with updated settings
                self.app.create_welcome_screen()
        
        apply_btn = tk.Button(
            btn_frame,
            text="Apply",
            command=apply_settings,
            font=("Arial", 12),
            bg=self.app.colors["button_bg"],
            fg=self.app.colors["button_fg"],
            width=10,
            activebackground=self.app.darken_color(self.app.colors["button_bg"])
        )
        apply_btn.pack(side="left", padx=5)
        
        def reset_defaults():
            # Defaults - ideally imported, but hardcoding for now or get from app
            DEFAULT_SETTINGS = {"question_count": 10, "theme": "light", "sound_effects": True}
            self.app.qcount_var.set(DEFAULT_SETTINGS["question_count"])
            self.app.theme_var.set(DEFAULT_SETTINGS["theme"])
            self.app.sound_var.set(DEFAULT_SETTINGS["sound_effects"])

        reset_btn = tk.Button(
            settings_win,
            text="Reset to Defaults",
            command=reset_defaults,
            font=("Arial", 10),
            bg=self.app.colors["button_bg"],
            fg=self.app.colors["button_fg"],
            activebackground=self.app.darken_color(self.app.colors["button_bg"])
        )
        reset_btn.pack(pady=10)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=settings_win.destroy,
            font=("Arial", 12),
            bg=self.app.colors["button_bg"],
            fg=self.app.colors["fg"],
            width=10,
            activebackground=self.app.darken_color(self.app.colors["button_bg"])
        )
        cancel_btn.pack(side="left", padx=5)
