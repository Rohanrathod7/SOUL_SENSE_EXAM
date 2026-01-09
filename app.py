import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from journal_feature import JournalFeature
from analytics_dashboard import AnalyticsDashboard
from i18n_manager import get_i18n, I18nManager

#DATABASE SETUP
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

# Add age column if it doesn't exist
try:
    cursor.execute("ALTER TABLE scores ADD COLUMN age INTEGER")
except sqlite3.OperationalError:
    pass  # Column already exists

conn.commit()

# Initialize i18n
i18n = get_i18n()

#QUESTIONS
#QUESTIONS - Now loaded from translation files
def get_questions():
    """Get questions in current language"""
    question_texts = i18n.get_all_questions()
    return [
        {"text": question_texts[0] if len(question_texts) > 0 else "Question 1", "age_min": 12, "age_max": 25},
        {"text": question_texts[1] if len(question_texts) > 1 else "Question 2", "age_min": 14, "age_max": 30},
        {"text": question_texts[2] if len(question_texts) > 2 else "Question 3", "age_min": 15, "age_max": 35},
        {"text": question_texts[3] if len(question_texts) > 3 else "Question 4", "age_min": 13, "age_max": 28},
        {"text": question_texts[4] if len(question_texts) > 4 else "Question 5", "age_min": 16, "age_max": 40}
    ]

questions = get_questions()

#USER DETAILS WINDOW
root = tk.Tk()
root.title(i18n.get("user_details_title"))
root.geometry("450x450")
root.resizable(False, False)

username = tk.StringVar()
age = tk.StringVar()

# Language selector frame
lang_frame = tk.Frame(root)
lang_frame.pack(pady=10)

tk.Label(lang_frame, text=i18n.get("settings.language") + ":", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

current_lang = tk.StringVar(value=i18n.current_language)
lang_selector = ttk.Combobox(
    lang_frame, 
    textvariable=current_lang,
    values=list(I18nManager.SUPPORTED_LANGUAGES.keys()),
    state="readonly",
    width=10
)
lang_selector.pack(side=tk.LEFT, padx=5)

# Title label (will be updated on language change)
title_label = tk.Label(
    root,
    text=i18n.get("app_title"),
    font=("Arial", 20, "bold")
)
title_label.pack(pady=20)

# Name label and entry
name_label = tk.Label(root, text=i18n.get("enter_name"), font=("Arial", 15))
name_label.pack()
tk.Entry(root, textvariable=username, font=("Arial", 15), width=25).pack(pady=8)

# Age label and entry
age_label = tk.Label(root, text=i18n.get("enter_age"), font=("Arial", 15))
age_label.pack()
tk.Entry(root, textvariable=age, font=("Arial", 15), width=25).pack(pady=8)

def update_ui_language():
    """Update all UI elements when language changes"""
    global questions
    root.title(i18n.get("user_details_title"))
    title_label.config(text=i18n.get("app_title"))
    name_label.config(text=i18n.get("enter_name"))
    age_label.config(text=i18n.get("enter_age"))
    start_btn.config(text=i18n.get("start_assessment"))
    journal_btn.config(text=i18n.get("open_journal"))
    dashboard_btn.config(text=i18n.get("view_dashboard"))
    # Reload questions in new language
    questions = get_questions()

def on_language_change(event):
    """Handle language selection change"""
    new_lang = current_lang.get()
    if i18n.switch_language(new_lang):
        update_ui_language()

lang_selector.bind('<<ComboboxSelected>>', on_language_change)

def submit_details():
    if not username.get():
        messagebox.showerror(i18n.get("errors.empty_name"), i18n.get("errors.empty_name"))
        return
    
    if not age.get().isdigit():
        messagebox.showerror(i18n.get("errors.invalid_age"), i18n.get("errors.invalid_age"))
        return
    
    user_age = int(age.get())
    if user_age < 12:
        messagebox.showerror(i18n.get("errors.minimum_age"), i18n.get("errors.minimum_age"))
        return

    root.destroy()
    start_quiz(username.get(), user_age)

start_btn = tk.Button(
    root,
    text=i18n.get("start_assessment"),
    command=submit_details,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 14, "bold"),
    width=20
)
start_btn.pack(pady=15)

# Initialize features
journal_feature = JournalFeature(root)

journal_btn = tk.Button(
    root,
    text=i18n.get("open_journal"),
    command=lambda: journal_feature.open_journal_window(username.get() or "Guest"),
    bg="#2196F3",
    fg="white",
    font=("Arial", 12),
    width=20
)
journal_btn.pack(pady=5)

dashboard_btn = tk.Button(
    root,
    text=i18n.get("view_dashboard"),
    command=lambda: AnalyticsDashboard(root, username.get() or "Guest").open_dashboard(),
    bg="#FF9800",
    fg="white",
    font=("Arial", 12),
    width=20
)
dashboard_btn.pack(pady=5)

#QUIZ WINDOW
def start_quiz(username, age):
    # Get fresh i18n instance
    quiz_i18n = get_i18n()
    
    # Show ALL questions to EVERYONE, regardless of age
    # We ignore the age_min and age_max filters
    filtered_questions = questions  # All 5 questions for everyone
    
    # If you want MORE questions, add them to the questions list above
    # For example, add these additional questions:
    # questions.append({"text": "You can easily put yourself in someone else's shoes.", "age_min": 12, "age_max": 100})
    # questions.append({"text": "You stay calm under pressure.", "age_min": 12, "age_max": 100})
    # etc.

    quiz = tk.Tk()
    quiz.title(quiz_i18n.get("app_title"))
    quiz.geometry("750x550")

    # Store quiz state in a dictionary to avoid nonlocal issues
    quiz_state = {
        "current_q": 0,
        "score": 0,
        "responses": [],  # Store all responses
        "username": username,
        "age": age
    }

    var = tk.IntVar()

    question_label = tk.Label(
        quiz,
        text="",
        wraplength=700,
        font=("Arial", 16)
    )
    question_label.pack(pady=25)

    options = [
        (quiz_i18n.get("quiz.strongly_disagree"), 1),
        (quiz_i18n.get("quiz.disagree"), 2),
        (quiz_i18n.get("quiz.neutral"), 3),
        (quiz_i18n.get("quiz.agree"), 4),
        (quiz_i18n.get("quiz.strongly_agree"), 5)
    ]

    for text, val in options:
        tk.Radiobutton(
            quiz,
            text=text,
            variable=var,
            value=val,
            font=("Arial", 14)
        ).pack(anchor="w", padx=60, pady=2)

    # Question counter
    counter_label = tk.Label(
        quiz,
        text=quiz_i18n.get("quiz.question_counter", current=1, total=len(filtered_questions)),
        font=("Arial", 12, "bold"),
        fg="gray"
    )
    counter_label.pack(pady=5)

    def load_question():
        """Load the current question"""
        current_q = quiz_state["current_q"]
        question_label.config(text=filtered_questions[current_q]["text"])
        counter_label.config(text=quiz_i18n.get("quiz.question_counter", 
                                                 current=current_q + 1, 
                                                 total=len(filtered_questions)))
        
        # Set the radio button to previous response if available
        if current_q < len(quiz_state["responses"]):
            var.set(quiz_state["responses"][current_q])
        else:
            var.set(0)

    def update_navigation_buttons():
        """Update button states based on current question"""
        current_q = quiz_state["current_q"]
        if current_q == 0:
            prev_btn.config(state="disabled")
        else:
            prev_btn.config(state="normal")
        
        if current_q == len(filtered_questions) - 1:
            next_btn.config(text=quiz_i18n.get("quiz.finish"))
        else:
            next_btn.config(text=quiz_i18n.get("quiz.next"))

    def save_current_answer():
        """Save the current answer before navigating"""
        current_answer = var.get()
        if current_answer > 0:  # Only save if an answer was selected
            current_q = quiz_state["current_q"]
            if current_q < len(quiz_state["responses"]):
                quiz_state["responses"][current_q] = current_answer
            else:
                quiz_state["responses"].append(current_answer)

    def previous_question():
        """Go to previous question"""
        # Save current answer before moving back
        save_current_answer()
        
        # Move to previous question
        if quiz_state["current_q"] > 0:
            quiz_state["current_q"] -= 1
            load_question()
            update_navigation_buttons()

    def next_question():
        """Go to next question or finish"""
        current_q = quiz_state["current_q"]

        if var.get() == 0:
            messagebox.showwarning(quiz_i18n.get("quiz.warning"), 
                                  quiz_i18n.get("errors.select_option"))
            return

        # Save current answer
        save_current_answer()
        
        # Clear radio button for next question
        var.set(0)
        
        # Move to next question or finish
        if current_q < len(filtered_questions) - 1:
            quiz_state["current_q"] += 1
            load_question()
            update_navigation_buttons()
        else:
            # Calculate final score from all responses
            quiz_state["score"] = sum(quiz_state["responses"])
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO scores (username, age, total_score, timestamp) VALUES (?, ?, ?, ?)",
                (quiz_state["username"], quiz_state["age"], quiz_state["score"], timestamp)
            )
            conn.commit()

            # Show completion message with options
            max_score = len(filtered_questions) * 5
            avg_score = quiz_state['score']/len(filtered_questions)
            
            result = messagebox.askyesno(
                quiz_i18n.get("results.completed"),
                f"{quiz_i18n.get('results.thank_you', username=quiz_state['username'])}\n"
                f"{quiz_i18n.get('results.your_score', score=quiz_state['score'], max_score=max_score)}\n"
                f"{quiz_i18n.get('results.average', average=f'{avg_score:.1f}')}\n\n"
                f"{quiz_i18n.get('results.view_dashboard_prompt')}"
            )
            
            if result:
                quiz.destroy()
                dashboard = AnalyticsDashboard(None, quiz_state["username"])
                dashboard.open_dashboard()
            else:
                quiz.destroy()
            conn.close()

    # Navigation buttons frame
    nav_frame = tk.Frame(quiz)
    nav_frame.pack(pady=20)

    # Previous button (initially disabled)
    prev_btn = tk.Button(
        nav_frame,
        text=quiz_i18n.get("quiz.previous"),
        command=previous_question,
        bg="#70CFFF",
        fg="white",
        font=("Arial", 12),
        width=12,
        state="disabled"  # Disabled on first question
    )
    prev_btn.pack(side="left", padx=10)

    # Next/Finish button
    next_btn = tk.Button(
        nav_frame,
        text=quiz_i18n.get("quiz.next"),
        command=next_question,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 12, "bold"),
        width=12
    )
    next_btn.pack(side="left", padx=10)

    # Initialize first question
    load_question()
    update_navigation_buttons()

    quiz.mainloop()

root.mainloop()