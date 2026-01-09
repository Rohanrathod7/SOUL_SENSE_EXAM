import sqlite3
import tkinter as tk
from tkinter import messagebox, font, ttk
from journal_feature import JournalFeature
from analytics_dashboard import AnalyticsDashboard
from datetime import datetime

# DATABASE SETUP
conn = sqlite3.connect("soulsense_db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    age INTEGER,
    total_score INTEGER,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

try:
    cursor.execute("ALTER TABLE scores ADD COLUMN age INTEGER")
except sqlite3.OperationalError:
    pass

conn.commit()

# QUESTIONS
questions = [
    {"text": "You can recognize your emotions as they happen.", "age_min": 12, "age_max": 25},
    {"text": "You find it easy to understand why you feel a certain way.", "age_min": 14, "age_max": 30},
    {"text": "You can control your emotions even in stressful situations.", "age_min": 15, "age_max": 35},
    {"text": "You reflect on your emotional reactions to situations.", "age_min": 13, "age_max": 28},
    {"text": "You are aware of how your emotions affect others.", "age_min": 16, "age_max": 40}
]

# Custom colors - Light Theme
LIGHT_THEME = {
    "primary": "#4CAF50",
    "secondary": "#2196F3",
    "accent": "#FF9800",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "light_bg": "#f0f4f8",
    "card_bg": "#ffffff",
    "text": "#333333",
    "subtext": "#666666",
    "border": "#e0e0e0",
    "analytics": "#9C27B0",
    "correlation": "#E91E63",
    "insights": "#009688",
    "white": "#FFFFFF",
    "light_white": "#F8F9FA",
    "settings_bg": "#ffffff",
    "toggle_bg": "#e0e0e0",
    "toggle_fg": "#333333"
}

# Dark Theme
DARK_THEME = {
    "primary": "#4CAF50",
    "secondary": "#2196F3",
    "accent": "#FF9800",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "light_bg": "#121212",
    "card_bg": "#1e1e1e",
    "text": "#ffffff",
    "subtext": "#b0b0b0",
    "border": "#333333",
    "analytics": "#BA68C8",
    "correlation": "#F06292",
    "insights": "#4DB6AC",
    "white": "#1e1e1e",
    "light_white": "#2d2d2d",
    "settings_bg": "#1e1e1e",
    "toggle_bg": "#333333",
    "toggle_fg": "#ffffff"
}

# Global settings
CURRENT_THEME = LIGHT_THEME
QUESTION_COUNT = 5  # Default question count
SOUND_ENABLED = True

def apply_theme_to_widget(widget, theme):
    """Recursively apply theme to all widgets"""
    widget_type = widget.winfo_class()
    
    try:
        if widget_type == "Tk" or widget_type == "Toplevel" or widget_type == "Frame":
            if "bg" in widget.configure():
                widget.configure(bg=theme["light_bg"])
        elif widget_type == "Label":
            if "bg" in widget.configure():
                widget.configure(bg=theme.get("bg", theme["light_bg"]), fg=theme["text"])
        elif widget_type == "Button":
            if "bg" in widget.configure():
                current_bg = widget.cget("bg")
                # Preserve special button colors
                if current_bg in [LIGHT_THEME["primary"], LIGHT_THEME["secondary"], LIGHT_THEME["accent"], 
                                 LIGHT_THEME["analytics"], LIGHT_THEME["correlation"], LIGHT_THEME["insights"],
                                 "#607D8B", "#757575", "#B0BEC5"]:
                    # Keep original color but update text
                    widget.configure(fg="white")
                else:
                    widget.configure(bg=theme["card_bg"], fg=theme["text"])
        elif widget_type == "Entry":
            widget.configure(bg=theme["card_bg"], fg=theme["text"], insertbackground=theme["text"])
        elif widget_type == "Radiobutton":
            widget.configure(bg=theme["card_bg"], fg=theme["text"], 
                           selectcolor=theme["primary"], activebackground=theme["card_bg"],
                           activeforeground=theme["text"])
        elif widget_type == "Canvas":
            widget.configure(bg=theme.get("bg", theme["light_bg"]))
        elif widget_type == "Checkbutton":
            widget.configure(bg=theme["light_bg"], fg=theme["text"], 
                           selectcolor=theme["primary"], activebackground=theme["light_bg"],
                           activeforeground=theme["text"])
        elif widget_type == "Scale":
            widget.configure(bg=theme["light_bg"], fg=theme["text"])
    except:
        pass
    
    # Apply to children
    for child in widget.winfo_children():
        apply_theme_to_widget(child, theme)

def open_settings():
    """Open settings window"""
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings - SoulSense")
    settings_window.geometry("500x500")
    settings_window.resizable(False, False)
    settings_window.configure(bg=CURRENT_THEME["light_bg"])
    
    # Header
    header_frame = tk.Frame(settings_window, bg=CURRENT_THEME["primary"], height=70)
    header_frame.pack(fill="x", pady=(0, 20))
    header_frame.pack_propagate(False)
    
    tk.Label(
        header_frame,
        text="⚙️ Settings",
        font=("Arial", 22, "bold"),
        bg=CURRENT_THEME["primary"],
        fg="white"
    ).pack(pady=20)
    
    # Main content
    content_frame = tk.Frame(settings_window, bg=CURRENT_THEME["light_bg"], padx=40, pady=20)
    content_frame.pack(fill="both", expand=True)
    
    # Theme Settings
    theme_frame = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"], relief="solid", borderwidth=1, padx=20, pady=20)
    theme_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(
        theme_frame,
        text="Theme Settings",
        font=("Arial", 16, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(anchor="w", pady=(0, 15))
    
    # Theme toggle
    theme_toggle_frame = tk.Frame(theme_frame, bg=CURRENT_THEME["card_bg"])
    theme_toggle_frame.pack(fill="x", pady=5)
    
    tk.Label(
        theme_toggle_frame,
        text="Theme:",
        font=("Arial", 12),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(side="left", padx=(0, 20))
    
    def toggle_theme():
        global CURRENT_THEME
        if CURRENT_THEME == LIGHT_THEME:
            CURRENT_THEME = DARK_THEME
            theme_btn.config(text="🌙 Dark Theme")
        else:
            CURRENT_THEME = LIGHT_THEME
            theme_btn.config(text="☀️ Light Theme")
        
        # Apply theme to settings window
        apply_theme_to_widget(settings_window, CURRENT_THEME)
        
        # Apply theme to main window
        apply_theme_to_widget(root, CURRENT_THEME)
        
        messagebox.showinfo("Theme Changed", "Theme applied successfully!")
    
    theme_btn = tk.Button(
        theme_toggle_frame,
        text="☀️ Light Theme" if CURRENT_THEME == LIGHT_THEME else "🌙 Dark Theme",
        command=toggle_theme,
        bg=CURRENT_THEME["primary"],
        fg="white",
        font=("Arial", 11, "bold"),
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2"
    )
    theme_btn.pack(side="left")
    
    # Question Count Settings
    question_frame = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"], relief="solid", borderwidth=1, padx=20, pady=20)
    question_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(
        question_frame,
        text="Assessment Settings",
        font=("Arial", 16, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(anchor="w", pady=(0, 15))
    
    # Question count slider
    count_frame = tk.Frame(question_frame, bg=CURRENT_THEME["card_bg"])
    count_frame.pack(fill="x", pady=5)
    
    tk.Label(
        count_frame,
        text="Question Count:",
        font=("Arial", 12),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(side="left", padx=(0, 20))
    
    count_value = tk.StringVar(value=str(QUESTION_COUNT))
    
    def update_question_count(val):
        global QUESTION_COUNT
        QUESTION_COUNT = int(float(val))
        count_value.set(str(QUESTION_COUNT))
    
    count_slider = tk.Scale(
        count_frame,
        from_=3,
        to=len(questions),
        orient="horizontal",
        length=200,
        command=update_question_count,
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"],
        highlightbackground=CURRENT_THEME["light_bg"],
        troughcolor=CURRENT_THEME["border"],
        sliderrelief="flat"
    )
    count_slider.set(QUESTION_COUNT)
    count_slider.pack(side="left", padx=(0, 10))
    
    count_label = tk.Label(
        count_frame,
        textvariable=count_value,
        font=("Arial", 12, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["primary"],
        width=3
    )
    count_label.pack(side="left")
    
    tk.Label(
        count_frame,
        text="questions",
        font=("Arial", 11),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(side="left", padx=(5, 0))
    
    # Sound Settings
    sound_frame = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"], relief="solid", borderwidth=1, padx=20, pady=20)
    sound_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(
        sound_frame,
        text="Sound Settings",
        font=("Arial", 16, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(anchor="w", pady=(0, 15))
    
    # Sound toggle
    sound_toggle_frame = tk.Frame(sound_frame, bg=CURRENT_THEME["card_bg"])
    sound_toggle_frame.pack(fill="x", pady=5)
    
    tk.Label(
        sound_toggle_frame,
        text="Sound Effects:",
        font=("Arial", 12),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(side="left", padx=(0, 20))
    
    def toggle_sound():
        global SOUND_ENABLED
        SOUND_ENABLED = not SOUND_ENABLED
        if SOUND_ENABLED:
            sound_btn.config(text="🔊 ON")
            messagebox.showinfo("Sound", "Sound effects enabled!")
        else:
            sound_btn.config(text="🔇 OFF")
            messagebox.showinfo("Sound", "Sound effects disabled!")
    
    sound_btn = tk.Button(
        sound_toggle_frame,
        text="🔊 ON" if SOUND_ENABLED else "🔇 OFF",
        command=toggle_sound,
        bg=CURRENT_THEME["secondary"] if SOUND_ENABLED else "#757575",
        fg="white",
        font=("Arial", 11, "bold"),
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2"
    )
    sound_btn.pack(side="left")
    
    # Bottom buttons
    bottom_frame = tk.Frame(content_frame, bg=CURRENT_THEME["light_bg"])
    bottom_frame.pack(fill="x", pady=(10, 0))
    
    def save_settings():
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
        settings_window.destroy()
    
    tk.Button(
        bottom_frame,
        text="💾 Save Settings",
        command=save_settings,
        bg=CURRENT_THEME["primary"],
        fg="white",
        font=("Arial", 12, "bold"),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2"
    ).pack(side="left", padx=5)
    
    def reset_settings():
        global QUESTION_COUNT, SOUND_ENABLED, CURRENT_THEME
        QUESTION_COUNT = 5
        SOUND_ENABLED = True
        CURRENT_THEME = LIGHT_THEME
        messagebox.showinfo("Settings Reset", "All settings have been reset to defaults!")
        settings_window.destroy()
    
    tk.Button(
        bottom_frame,
        text="🔄 Reset to Defaults",
        command=reset_settings,
        bg=CURRENT_THEME["accent"],
        fg="white",
        font=("Arial", 12),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2"
    ).pack(side="left", padx=5)
    
    def close_settings():
        settings_window.destroy()
    
    tk.Button(
        bottom_frame,
        text="Close",
        command=close_settings,
        bg="#757575",
        fg="white",
        font=("Arial", 12),
        relief="flat",
        padx=25,
        pady=10,
        cursor="hand2"
    ).pack(side="right", padx=5)

def show_analysis_complete(username, score, age, total_questions):
    """Show the completion screen as a main window"""
    analysis_window = tk.Tk()
    analysis_window.title("Analysis & Insights - SoulSense")
    
    # Get screen dimensions
    screen_width = analysis_window.winfo_screenwidth()
    screen_height = analysis_window.winfo_screenheight()
    
    # Set to nearly full screen (95% of screen)
    window_width = int(screen_width * 0.95)
    window_height = int(screen_height * 0.95)
    
    analysis_window.geometry(f"{window_width}x{window_height}")
    analysis_window.configure(bg=CURRENT_THEME["light_bg"])
    
    # Make window resizable
    analysis_window.resizable(True, True)
    
    # Center the window
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    analysis_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Create main container with Canvas and Scrollbar
    main_container = tk.Frame(analysis_window, bg=CURRENT_THEME["light_bg"])
    main_container.pack(fill="both", expand=True)
    
    # Create a canvas for scrolling
    canvas = tk.Canvas(main_container, bg=CURRENT_THEME["light_bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    
    # Create a frame inside the canvas for content
    content_frame = tk.Frame(canvas, bg=CURRENT_THEME["light_bg"])
    
    # Configure canvas scrolling
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Put the content frame in the canvas
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
    
    # Update scrollregion when content frame size changes
    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    content_frame.bind("<Configure>", configure_scroll_region)
    
    # Also update canvas window width
    def configure_canvas_window(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    canvas.bind("<Configure>", configure_canvas_window)
    
    # Header
    header_frame = tk.Frame(content_frame, bg=CURRENT_THEME["primary"])
    header_frame.pack(fill="x", pady=(0, 30))
    
    header_content = tk.Frame(header_frame, bg=CURRENT_THEME["primary"], padx=min(100, window_width//10), pady=30)
    header_content.pack(fill="x")
    
    tk.Label(
        header_content,
        text="🎉 Assessment Complete!",
        font=("Arial", 28, "bold"),
        bg=CURRENT_THEME["primary"],
        fg="white"
    ).pack(pady=(0, 10))
    
    tk.Label(
        header_content,
        text=f"Congratulations {username}! Your emotional intelligence journey begins.",
        font=("Arial", 14),
        bg=CURRENT_THEME["primary"],
        fg=CURRENT_THEME["light_white"]
    ).pack()
    
    # Main content area
    main_content = tk.Frame(content_frame, bg=CURRENT_THEME["light_bg"], padx=min(80, window_width//12), pady=20)
    main_content.pack(fill="both", expand=True)
    
    # Congratulations message
    tk.Label(
        main_content,
        text="Your Results Are Ready",
        font=("Arial", 22, "bold"),
        bg=CURRENT_THEME["light_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(anchor="w", pady=(0, 10))
    
    tk.Label(
        main_content,
        text="Explore detailed insights and analysis options below:",
        font=("Arial", 14),
        bg=CURRENT_THEME["light_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(anchor="w", pady=(0, 30))
    
    # Score Summary Card
    score_card = tk.Frame(main_content, bg=CURRENT_THEME["card_bg"], relief="solid", borderwidth=1)
    score_card.pack(fill="x", pady=(0, 40))
    
    score_inner = tk.Frame(score_card, bg=CURRENT_THEME["card_bg"], padx=40, pady=40)
    score_inner.pack(fill="both", expand=True)
    
    tk.Label(
        score_inner,
        text="Your EQ Score Summary",
        font=("Arial", 24, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(pady=(0, 20))
    
    # Score display in center
    score_display_frame = tk.Frame(score_inner, bg=CURRENT_THEME["card_bg"])
    score_display_frame.pack(pady=20)
    
    tk.Label(
        score_display_frame,
        text=f"{score}",
        font=("Arial", 48, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["primary"]
    ).pack(side="left")
    
    tk.Label(
        score_display_frame,
        text=f" / {total_questions * 5}",
        font=("Arial", 32),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(side="left", padx=(10, 0), pady=(15, 0))
    
    # Average score
    avg_score = score / total_questions
    avg_frame = tk.Frame(score_inner, bg=CURRENT_THEME["card_bg"])
    avg_frame.pack(pady=10)
    
    tk.Label(
        avg_frame,
        text="Average Score: ",
        font=("Arial", 16),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(side="left")
    
    tk.Label(
        avg_frame,
        text=f"{avg_score:.1f}",
        font=("Arial", 18, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["primary"]
    ).pack(side="left", padx=(5, 0))
    
    tk.Label(
        avg_frame,
        text=" per question",
        font=("Arial", 16),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(side="left", padx=(5, 0))
    
    # Score interpretation
    if avg_score >= 4.0:
        interpretation = "🌟 Excellent emotional awareness and regulation skills!"
        interpretation_color = CURRENT_THEME["success"]
    elif avg_score >= 3.0:
        interpretation = "👍 Good emotional intelligence with solid foundation!"
        interpretation_color = "#FFA000"
    else:
        interpretation = "📈 Great opportunity for emotional intelligence growth!"
        interpretation_color = CURRENT_THEME["warning"]
    
    tk.Label(
        score_inner,
        text=interpretation,
        font=("Arial", 14, "italic"),
        bg=CURRENT_THEME["card_bg"],
        fg=interpretation_color
    ).pack(pady=(20, 0))
    
    # Analysis Options Section
    analysis_header_frame = tk.Frame(main_content, bg=CURRENT_THEME["light_bg"])
    analysis_header_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(
        analysis_header_frame,
        text="📊 Explore Your Results",
        font=("Arial", 26, "bold"),
        bg=CURRENT_THEME["light_bg"],
        fg=CURRENT_THEME["text"]
    ).pack(anchor="w")
    
    tk.Label(
        analysis_header_frame,
        text="Choose from our comprehensive analysis tools to gain deeper insights:",
        font=("Arial", 14),
        bg=CURRENT_THEME["light_bg"],
        fg=CURRENT_THEME["subtext"]
    ).pack(anchor="w", pady=(10, 0))
    
    # Analysis buttons grid - 2 columns
    buttons_container = tk.Frame(main_content, bg=CURRENT_THEME["light_bg"])
    buttons_container.pack(fill="both", expand=True, pady=(0, 30))
    
    # Function definitions for buttons
    def open_dashboard():
        analysis_window.destroy()
        dashboard = AnalyticsDashboard(None, username)
        dashboard.open_dashboard()
        conn.close()
    
    def check_correlation():
        messagebox.showinfo("Correlation Analysis", 
            "This feature analyzes correlations between:\n\n"
            "• Your responses across different emotional domains\n"
            "• Age vs EQ score patterns and trends\n"
            "• Response patterns and emotional regulation\n"
            "• Question clusters and their relationships\n\n"
            "Feature coming in the next update!")
    
    def advanced_analysis():
        messagebox.showinfo("Advanced Analysis",
            "Advanced analysis includes:\n\n"
            "• Pattern recognition in emotional responses\n"
            "• Emotional intelligence sub-domains breakdown\n"
            "• Personalized growth recommendations\n"
            "• Comparative analysis with peer groups\n"
            "• Trend analysis across multiple assessments\n\n"
            "Feature coming soon!")
    
    def generate_report():
        messagebox.showinfo("Insights Report",
            "Your personalized insights report includes:\n\n"
            "• Strengths and areas for improvement\n"
            "• Actionable development recommendations\n"
            "• Progress tracking and milestone planning\n"
            "• Emotional intelligence development roadmap\n"
            "• Resource recommendations for growth\n\n"
            "Feature in development!")
    
    def take_another_test():
        analysis_window.destroy()
        conn.close()
        # Restart application
        main()
    
    def view_history():
        cursor.execute(
            "SELECT id, total_score, timestamp FROM scores WHERE username = ? ORDER BY timestamp DESC LIMIT 10",
            (username,)
        )
        history = cursor.fetchall()
        
        if history:
            history_text = f"Recent Tests for {username}:\n\n"
            for test_id, total_score, timestamp in history:
                try:
                    date_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    date_str = date_obj.strftime("%b %d, %Y")
                except:
                    date_str = timestamp
                history_text += f"• Test #{test_id}: {total_score}/{total_questions*5} points ({date_str})\n"
            
            history_text += f"\nTotal tests completed: {len(history)}"
            messagebox.showinfo("Test History", history_text)
        else:
            messagebox.showinfo("Test History", "No test history found.")
    
    # Define button configurations
    button_configs = [
        {
            "text": "📈 Detailed Dashboard",
            "command": open_dashboard,
            "bg": CURRENT_THEME["primary"],
            "description": "Interactive dashboard with charts, trends, and visual analytics"
        },
        {
            "text": "🔗 Check Correlation",
            "command": check_correlation,
            "bg": CURRENT_THEME["correlation"],
            "description": "Analyze relationships between different emotional factors"
        },
        {
            "text": "📊 Advanced Analysis",
            "command": advanced_analysis,
            "bg": CURRENT_THEME["analytics"],
            "description": "Deep dive into patterns, clusters, and predictive insights"
        },
        {
            "text": "📋 Generate Insights Report",
            "command": generate_report,
            "bg": CURRENT_THEME["insights"],
            "description": "Personalized PDF report with actionable recommendations"
        },
        {
            "text": "🔄 Take Another Test",
            "command": take_another_test,
            "bg": CURRENT_THEME["secondary"],
            "description": "Retake assessment to track progress and improvement"
        },
        {
            "text": "📜 View History",
            "command": view_history,
            "bg": CURRENT_THEME["accent"],
            "description": "View past assessments and track your emotional growth"
        }
    ]
    
    # Create buttons in 2x3 grid
    for i, config in enumerate(button_configs):
        row = i // 2
        col = i % 2
        
        button_frame = tk.Frame(buttons_container, bg=CURRENT_THEME["light_bg"], padx=15, pady=15)
        button_frame.grid(row=row, column=col, sticky="nsew", padx=15, pady=15)
        
        # Configure grid weights
        buttons_container.grid_rowconfigure(row, weight=1)
        buttons_container.grid_columnconfigure(col, weight=1)
        
        # Button
        btn = tk.Button(
            button_frame,
            text=config["text"],
            command=config["command"],
            bg=config["bg"],
            fg="white",
            font=("Arial", 14, "bold"),
            relief="flat",
            padx=30,
            pady=20,
            cursor="hand2",
            wraplength=250
        )
        btn.pack(fill="both", expand=True)
        
        # Description
        tk.Label(
            button_frame,
            text=config["description"],
            font=("Arial", 11),
            bg=CURRENT_THEME["light_bg"],
            fg=CURRENT_THEME["subtext"],
            wraplength=280,
            justify="center"
        ).pack(pady=(10, 0))
    
    # Bottom navigation frame
    bottom_frame = tk.Frame(content_frame, bg=CURRENT_THEME["light_bg"], pady=30)
    bottom_frame.pack(fill="x", pady=(20, 0))
    
    bottom_inner = tk.Frame(bottom_frame, bg=CURRENT_THEME["light_bg"])
    bottom_inner.pack(fill="x", padx=min(80, window_width//12))
    
    def return_to_main():
        analysis_window.destroy()
        conn.close()
        # Restart the main application
        main()
    
    tk.Button(
        bottom_inner,
        text="🏠 Return to Main Menu",
        command=return_to_main,
        bg="#607D8B",
        fg="white",
        font=("Arial", 12),
        relief="flat",
        padx=25,
        pady=12,
        cursor="hand2"
    ).pack(side="left", padx=10)
    
    def close_all():
        analysis_window.destroy()
        conn.close()
        exit()
    
    tk.Button(
        bottom_inner,
        text="Exit Application",
        command=close_all,
        bg="#757575",
        fg="white",
        font=("Arial", 12),
        relief="flat",
        padx=25,
        pady=12,
        cursor="hand2"
    ).pack(side="right", padx=10)
    
    # Add mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Bind mousewheel for scrolling
    analysis_window.bind_all("<MouseWheel>", on_mousewheel)
    
    # Also bind for Linux
    analysis_window.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    analysis_window.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    
    # Clean up bindings when window closes
    def on_close():
        analysis_window.unbind_all("<MouseWheel>")
        analysis_window.unbind_all("<Button-4>")
        analysis_window.unbind_all("<Button-5>")
        analysis_window.destroy()
        conn.close()
    
    analysis_window.protocol("WM_DELETE_WINDOW", on_close)
    
    analysis_window.mainloop()

# USER DETAILS WINDOW
root = tk.Tk()
root.title("SoulSense - User Details")
root.geometry("450x380")
root.resizable(False, False)
root.configure(bg=CURRENT_THEME["light_bg"])

tk.Label(
    root,
    text="SoulSense Assessment",
    font=("Arial", 22, "bold"),
    bg=CURRENT_THEME["light_bg"],
    fg=CURRENT_THEME["text"]
).pack(pady=20)

tk.Label(root, text="Enter your name:", font=("Arial", 13), bg=CURRENT_THEME["light_bg"], fg=CURRENT_THEME["text"]).pack()
name_entry = tk.Entry(root, textvariable=tk.StringVar(), font=("Arial", 13), width=25, bg="white", relief="solid", borderwidth=1)
name_entry.pack(pady=5)

tk.Label(root, text="Enter your age:", font=("Arial", 13), bg=CURRENT_THEME["light_bg"], fg=CURRENT_THEME["text"]).pack()
age_entry = tk.Entry(root, textvariable=tk.StringVar(), font=("Arial", 13), width=25, bg="white", relief="solid", borderwidth=1)
age_entry.pack(pady=5)

def submit_details():
    username = name_entry.get().strip()
    age_str = age_entry.get().strip()
    
    if not username:
        messagebox.showerror("Error", "Please enter your name")
        return
    
    if not age_str.isdigit():
        messagebox.showerror("Error", "Please enter a valid age (numbers only)")
        return
    
    user_age = int(age_str)
    if user_age < 12:
        messagebox.showerror("Error", "Age must be at least 12")
        return

    root.destroy()
    start_quiz(username, user_age)

tk.Button(
    root,
    text="Start Assessment",
    command=submit_details,
    bg=CURRENT_THEME["primary"],
    fg="white",
    font=("Arial", 13, "bold"),
    width=20,
    relief="flat",
    padx=20,
    pady=8,
    cursor="hand2"
).pack(pady=20)

# Initialize features
journal_feature = JournalFeature(root)

# Settings button
tk.Button(
    root,
    text="⚙️ Settings",
    command=open_settings,
    bg=CURRENT_THEME["accent"],
    fg="white",
    font=("Arial", 11),
    width=20,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
).pack(pady=5)

tk.Button(
    root,
    text="📝 Open Journal",
    command=lambda: journal_feature.open_journal_window(name_entry.get() or "Guest"),
    bg=CURRENT_THEME["secondary"],
    fg="white",
    font=("Arial", 11),
    width=20,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
).pack(pady=5)

tk.Button(
    root,
    text="📊 View Dashboard",
    command=lambda: AnalyticsDashboard(root, name_entry.get() or "Guest").open_dashboard(),
    bg=CURRENT_THEME["analytics"],
    fg="white",
    font=("Arial", 11),
    width=20,
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2"
).pack(pady=5)

# QUIZ WINDOW
def start_quiz(username, age):
    # Use filtered questions based on QUESTION_COUNT setting
    filtered_questions = questions[:QUESTION_COUNT]
    
    quiz = tk.Tk()
    quiz.title(f"SoulSense Assessment - {username}")
    quiz.geometry("850x650")
    quiz.configure(bg=CURRENT_THEME["light_bg"])
    
    # Header frame
    header_frame = tk.Frame(quiz, bg=CURRENT_THEME["primary"], height=80)
    header_frame.pack(fill="x", pady=(0, 20))
    header_frame.pack_propagate(False)
    
    tk.Label(
        header_frame,
        text="SoulSense EQ Assessment",
        font=("Arial", 20, "bold"),
        bg=CURRENT_THEME["primary"],
        fg="white"
    ).pack(pady=20)
    
    # Main content frame with card-like appearance
    content_frame = tk.Frame(quiz, bg=CURRENT_THEME["card_bg"], relief="solid", borderwidth=1)
    content_frame.pack(fill="both", expand=True, padx=40, pady=10)
    
    # Progress section
    progress_frame = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"])
    progress_frame.pack(fill="x", pady=(20, 10), padx=30)
    
    quiz_state = {
        "current_q": 0,
        "score": 0,
        "responses": [],
        "username": username,
        "age": age
    }

    var = tk.IntVar()
    
    # Question counter with better styling
    counter_label = tk.Label(
        progress_frame,
        text="",
        font=("Arial", 12, "bold"),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["primary"]
    )
    counter_label.pack(side="left")
    
    # Progress bar
    progress_canvas = tk.Canvas(progress_frame, height=8, width=300, bg=CURRENT_THEME["border"], highlightthickness=0)
    progress_canvas.pack(side="right")
    progress_bar = progress_canvas.create_rectangle(0, 0, 0, 8, fill=CURRENT_THEME["primary"], outline="")
    
    # Question area
    question_area = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"])
    question_area.pack(fill="both", expand=True, padx=30, pady=10)
    
    # Question label with better styling
    question_label = tk.Label(
        question_area,
        text="",
        wraplength=700,
        font=("Arial", 16),
        bg=CURRENT_THEME["card_bg"],
        fg=CURRENT_THEME["text"],
        justify="left"
    )
    question_label.pack(anchor="w", pady=(20, 30))
    
    # Options frame
    options_frame = tk.Frame(question_area, bg=CURRENT_THEME["card_bg"])
    options_frame.pack(fill="both", expand=True, padx=10)
    
    options = [
        ("Strongly Disagree", 1),
        ("Disagree", 2),
        ("Neutral", 3),
        ("Agree", 4),
        ("Strongly Agree", 5)
    ]
    
    # Create radio buttons with better styling
    radio_buttons = []
    for i, (text, val) in enumerate(options):
        rb_frame = tk.Frame(options_frame, bg=CURRENT_THEME["card_bg"])
        rb_frame.pack(fill="x", pady=8)
        
        rb = tk.Radiobutton(
            rb_frame,
            text=text,
            variable=var,
            value=val,
            font=("Arial", 13),
            bg=CURRENT_THEME["card_bg"],
            fg=CURRENT_THEME["text"],
            selectcolor=CURRENT_THEME["primary"],
            activebackground=CURRENT_THEME["card_bg"],
            activeforeground=CURRENT_THEME["text"],
            cursor="hand2"
        )
        rb.pack(side="left")
        radio_buttons.append(rb)
        
        # Add hover effect
        def on_enter(e, rb=rb):
            rb.config(bg="#f5f5f5" if CURRENT_THEME == LIGHT_THEME else "#2a2a2a")
        def on_leave(e, rb=rb):
            rb.config(bg=CURRENT_THEME["card_bg"])
        
        rb.bind("<Enter>", on_enter)
        rb.bind("<Leave>", on_leave)
    
    # Navigation buttons frame
    nav_frame = tk.Frame(content_frame, bg=CURRENT_THEME["card_bg"])
    nav_frame.pack(fill="x", pady=30, padx=30)
    
    def update_progress():
        """Update progress bar and counter"""
        current_q = quiz_state["current_q"]
        total_q = len(filtered_questions)
        
        # Update counter
        counter_label.config(text=f"Question {current_q + 1} of {total_q}")
        
        # Update progress bar
        progress_width = (current_q / total_q) * 300 if total_q > 0 else 0
        progress_canvas.coords(progress_bar, 0, 0, progress_width, 8)
    
    def load_question():
        current_q = quiz_state["current_q"]
        question_label.config(text=filtered_questions[current_q]["text"])
        
        if current_q < len(quiz_state["responses"]):
            var.set(quiz_state["responses"][current_q])
        else:
            var.set(0)
        
        update_progress()
    
    def update_navigation_buttons():
        current_q = quiz_state["current_q"]
        if current_q == 0:
            prev_btn.config(state="disabled", bg="#B0BEC5")
        else:
            prev_btn.config(state="normal", bg=CURRENT_THEME["secondary"])
        
        if current_q == len(filtered_questions) - 1:
            next_btn.config(text="Finish Assessment ✓")
        else:
            next_btn.config(text="Next Question →")
    
    def save_current_answer():
        current_answer = var.get()
        if current_answer > 0:
            current_q = quiz_state["current_q"]
            if current_q < len(quiz_state["responses"]):
                quiz_state["responses"][current_q] = current_answer
            else:
                quiz_state["responses"].append(current_answer)
    
    def previous_question():
        save_current_answer()
        if quiz_state["current_q"] > 0:
            quiz_state["current_q"] -= 1
            load_question()
            update_navigation_buttons()
    
    def next_question():
        current_q = quiz_state["current_q"]

        if var.get() == 0:
            messagebox.showwarning("Selection Required", "Please select an option to continue.")
            return

        save_current_answer()
        var.set(0)
        
        if current_q < len(filtered_questions) - 1:
            quiz_state["current_q"] += 1
            load_question()
            update_navigation_buttons()
        else:
            quiz_state["score"] = sum(quiz_state["responses"])
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO scores (username, age, total_score, timestamp) VALUES (?, ?, ?, ?)",
                (quiz_state["username"], quiz_state["age"], quiz_state["score"], timestamp)
            )
            conn.commit()

            # Store references before destroying quiz window
            username = quiz_state["username"]
            score = quiz_state["score"]
            age = quiz_state["age"]
            total_questions = len(filtered_questions)
            
            # Destroy the quiz window first
            quiz.destroy()
            
            # Now show analysis in a new main window
            show_analysis_complete(username, score, age, total_questions)
    
    # Previous button
    prev_btn = tk.Button(
        nav_frame,
        text="← Previous Question",
        command=previous_question,
        bg="#B0BEC5",
        fg="white",
        font=("Arial", 12, "bold"),
        width=18,
        relief="flat",
        padx=15,
        pady=10,
        cursor="hand2",
        state="disabled"
    )
    prev_btn.pack(side="left", padx=10)
    
    # Next button
    next_btn = tk.Button(
        nav_frame,
        text="Next Question →",
        command=next_question,
        bg=CURRENT_THEME["primary"],
        fg="white",
        font=("Arial", 12, "bold"),
        width=18,
        relief="flat",
        padx=15,
        pady=10,
        cursor="hand2"
    )
    next_btn.pack(side="right", padx=10)
    
    # Add keyboard shortcuts
    def on_key_press(event):
        if event.keysym == 'Left' and quiz_state["current_q"] > 0:
            previous_question()
        elif event.keysym == 'Right' or event.keysym == 'Return':
            next_question()
    
    quiz.bind('<Left>', on_key_press)
    quiz.bind('<Right>', on_key_press)
    quiz.bind('<Return>', on_key_press)
    
    # Initialize
    load_question()
    update_navigation_buttons()
    
    quiz.mainloop()

def main():
    """Main function to start the application"""
    root.mainloop()

if __name__ == "__main__":
    main()