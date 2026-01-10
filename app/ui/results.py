import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime
import random
from app.db import get_connection
from app.constants import BENCHMARK_DATA
try:
    from app.pdf_generator import generate_pdf_report
except ImportError:
    generate_pdf_report = None

class ResultsManager:
    def __init__(self, app):
        self.app = app

    # ---------- BENCHMARKING FUNCTIONS ----------
    def calculate_percentile(self, score, avg_score, std_dev):
        """Calculate percentile based on normal distribution"""
        if std_dev == 0:
            return 50 if score == avg_score else (100 if score > avg_score else 0)
        
        # Z-score calculation
        z_score = (score - avg_score) / std_dev
        
        # Convert Z-score to percentile (simplified approximation)
        if z_score <= -2.5:
            percentile = 1
        elif z_score <= -2.0:
            percentile = 2
        elif z_score <= -1.5:
            percentile = 7
        elif z_score <= -1.0:
            percentile = 16
        elif z_score <= -0.5:
            percentile = 31
        elif z_score <= 0:
            percentile = 50
        elif z_score <= 0.5:
            percentile = 69
        elif z_score <= 1.0:
            percentile = 84
        elif z_score <= 1.5:
            percentile = 93
        elif z_score <= 2.0:
            percentile = 98
        elif z_score <= 2.5:
            percentile = 99
        else:
            percentile = 99.5
            
        return percentile

    def get_benchmark_comparison(self):
        """Get benchmark comparisons for the current score"""
        comparisons = {}
        
        # Global comparison
        global_bench = BENCHMARK_DATA["global"]
        comparisons["global"] = {
            "your_score": self.app.current_score,
            "avg_score": global_bench["avg_score"],
            "difference": self.app.current_score - global_bench["avg_score"],
            "percentile": self.calculate_percentile(self.app.current_score, global_bench["avg_score"], global_bench["std_dev"]),
            "sample_size": global_bench["sample_size"]
        }
        
        # Age group comparison
        if self.app.age_group and self.app.age_group in BENCHMARK_DATA["age_groups"]:
            age_bench = BENCHMARK_DATA["age_groups"][self.app.age_group]
            comparisons["age_group"] = {
                "group": self.app.age_group,
                "your_score": self.app.current_score,
                "avg_score": age_bench["avg_score"],
                "difference": self.app.current_score - age_bench["avg_score"],
                "percentile": self.calculate_percentile(self.app.current_score, age_bench["avg_score"], age_bench["std_dev"]),
                "sample_size": age_bench["sample_size"]
            }
        
        # Profession comparison
        if self.app.profession and self.app.profession in BENCHMARK_DATA["professions"]:
            prof_bench = BENCHMARK_DATA["professions"][self.app.profession]
            comparisons["profession"] = {
                "profession": self.app.profession,
                "your_score": self.app.current_score,
                "avg_score": prof_bench["avg_score"],
                "difference": self.app.current_score - prof_bench["avg_score"],
                "percentile": self.calculate_percentile(self.app.current_score, prof_bench["avg_score"], prof_bench["std_dev"])
            }
        
        return comparisons

    def get_benchmark_interpretation(self, comparisons):
        """Get interpretation text based on benchmark comparisons"""
        interpretations = []
        
        if "global" in comparisons:
            comp = comparisons["global"]
            if comp["difference"] > 5:
                interpretations.append(f"Your score is significantly higher than the global average ({comp['avg_score']}).")
            elif comp["difference"] > 2:
                interpretations.append(f"Your score is above the global average ({comp['avg_score']}).")
            elif comp["difference"] < -5:
                interpretations.append(f"Your score is significantly lower than the global average ({comp['avg_score']}).")
            elif comp["difference"] < -2:
                interpretations.append(f"Your score is below the global average ({comp['avg_score']}).")
            else:
                interpretations.append(f"Your score is close to the global average ({comp['avg_score']}).")
            
            interpretations.append(f"You scored higher than {comp['percentile']:.1f}% of test-takers globally.")
        
        if "age_group" in comparisons:
            comp = comparisons["age_group"]
            if comp["difference"] > 0:
                interpretations.append(f"You scored above average for your age group ({comp['group']}).")
            elif comp["difference"] < 0:
                interpretations.append(f"You scored below average for your age group ({comp['group']}).")
            else:
                interpretations.append(f"You scored average for your age group ({comp['group']}).")
            
            interpretations.append(f"You're in the {comp['percentile']:.0f}th percentile for your age group.")
        
        if "profession" in comparisons:
            comp = comparisons["profession"]
            if comp["difference"] > 0:
                interpretations.append(f"You scored above average for {comp['profession']} professionals.")
            elif comp["difference"] < 0:
                interpretations.append(f"You scored below average for {comp['profession']} professionals.")
            else:
                interpretations.append(f"You scored average for {comp['profession']} professionals.")
        
        return interpretations

    def create_benchmark_chart(self, parent, comparisons):
        """Create a visual benchmark comparison chart"""
        chart_frame = self.app.create_widget(tk.Frame, parent)
        chart_frame.pack(fill="x", pady=10)
        
        self.app.create_widget(
            tk.Label,
            chart_frame,
            text="Benchmark Comparison",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=5)
        
        # Create canvas for benchmark bars
        chart_canvas = tk.Canvas(chart_frame, height=150, bg=self.app.colors["chart_bg"], highlightthickness=0)
        chart_canvas.pack(fill="x", pady=10)
        
        # Prepare data for chart
        chart_data = []
        if "global" in comparisons:
            chart_data.append(("Global", comparisons["global"]))
        if "age_group" in comparisons:
            chart_data.append((comparisons["age_group"]["group"], comparisons["age_group"]))
        if "profession" in comparisons:
            chart_data.append((comparisons["profession"]["profession"], comparisons["profession"]))
        
        if not chart_data:
            return chart_frame
        
        # Calculate chart dimensions
        num_bars = len(chart_data)
        chart_width = 500
        bar_width = 80
        spacing = 30
        start_x = 100
        max_score = max([max(d["your_score"], d["avg_score"]) for _, d in chart_data])
        scale_factor = 100 / max(1, max_score)
        
        # Draw bars for each comparison
        for i, (label, data) in enumerate(chart_data):
            x = start_x + i * (bar_width + spacing)
            
            # Your score bar
            your_height = data["your_score"] * scale_factor
            y_your = 130 - your_height
            your_color = self.app.colors["benchmark_better"] if data["difference"] > 0 else self.app.colors["benchmark_worse"] if data["difference"] < 0 else self.app.colors["benchmark_same"]
            
            chart_canvas.create_rectangle(x, y_your, x + bar_width/2, 130, 
                                         fill=your_color, outline="black")
            chart_canvas.create_text(x + bar_width/4, y_your - 10, 
                                    text=f"You: {data['your_score']}", 
                                    fill=self.app.colors["chart_fg"], font=("Arial", 8, "bold"))
            
            # Average score bar
            avg_height = data["avg_score"] * scale_factor
            y_avg = 130 - avg_height
            
            chart_canvas.create_rectangle(x + bar_width/2, y_avg, x + bar_width, 130, 
                                         fill="#888888", outline="black")
            chart_canvas.create_text(x + bar_width * 0.75, y_avg - 10, 
                                    text=f"Avg: {data['avg_score']}", 
                                    fill=self.app.colors["chart_fg"], font=("Arial", 8, "bold"))
            
            # Label
            chart_canvas.create_text(x + bar_width/2, 145, text=label, 
                                    fill=self.app.colors["chart_fg"], font=("Arial", 9))
            
            # Difference indicator
            diff = data["difference"]
            if diff != 0:
                diff_text = f"{'+' if diff > 0 else ''}{diff:.1f}"
                diff_color = self.app.colors["benchmark_better"] if diff > 0 else self.app.colors["benchmark_worse"]
                chart_canvas.create_text(x + bar_width/2, y_your - 25, text=diff_text, 
                                        fill=diff_color, font=("Arial", 9, "bold"))
        
        # Y-axis labels
        for score in [0, max_score//2, max_score]:
            y = 130 - (score * scale_factor)
            chart_canvas.create_text(80, y, text=str(score), fill=self.app.colors["chart_fg"], font=("Arial", 8))
        
        chart_canvas.create_text(50, 65, text="Score", fill=self.app.colors["chart_fg"], angle=90)
        
        # Legend
        legend_frame = self.app.create_widget(tk.Frame, chart_frame)
        legend_frame.pack(pady=5)
        
        # Your score legend
        your_legend = tk.Canvas(legend_frame, width=20, height=20, bg=self.app.colors["chart_bg"], highlightthickness=0)
        your_legend.create_rectangle(0, 0, 20, 20, fill=self.app.colors["benchmark_better"], outline="black")
        your_legend.pack(side="left", padx=5)
        tk.Label(legend_frame, text="Your Score", bg=self.app.colors["chart_bg"], fg=self.app.colors["chart_fg"]).pack(side="left", padx=5)
        
        # Average score legend
        avg_legend = tk.Canvas(legend_frame, width=20, height=20, bg=self.app.colors["chart_bg"], highlightthickness=0)
        avg_legend.create_rectangle(0, 0, 20, 20, fill="#888888", outline="black")
        avg_legend.pack(side="left", padx=20)
        tk.Label(legend_frame, text="Average Score", bg=self.app.colors["chart_bg"], fg=self.app.colors["chart_fg"]).pack(side="left", padx=5)
        
        return chart_frame

    def export_results_pdf(self):
        """Export current results to PDF"""
        if not generate_pdf_report:
            messagebox.showerror("Error", "PDF Generator module not available.")
            return

        try:
            # Prepare data for report
            filename = generate_pdf_report(
                self.app.username,
                self.app.current_score,
                self.app.current_max_score,
                self.app.current_percentage,
                self.app.age,
                self.app.responses,
                self.app.questions,
                self.app.sentiment_score if hasattr(self.app, 'sentiment_score') else None
            )
            
            messagebox.showinfo("Success", f"Report saved successfully:\n{filename}")
            
            # Optional: Open the file
            # import os
            # os.startfile(filename) 
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to generate PDF:\n{str(e)}")
            logging.error(f"PDF Export failed: {e}")

    def show_visual_results(self):
        """Show visual results with charts and graphs"""
        self.app.clear_screen()
        
        # Get benchmark comparisons
        comparisons = self.get_benchmark_comparison()
        benchmark_interpretations = self.get_benchmark_interpretation(comparisons)
        
        # Create scrollable frame for results
        canvas = tk.Canvas(self.app.root, bg=self.app.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.app.root, orient="vertical", command=canvas.yview)
        scrollable_frame = self.app.create_widget(tk.Frame, canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        header_frame.pack(fill="x", pady=10, padx=20)
        
        self.app.create_widget(
            tk.Label,
            header_frame,
            text=f"Test Results for {self.app.username}",
            font=("Arial", 22, "bold")
        ).pack()
        
        # Score Summary
        summary_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        summary_frame.pack(fill="x", pady=20, padx=20)
        
        # Create visual score display
        score_display_frame = self.app.create_widget(tk.Frame, summary_frame)
        score_display_frame.pack(pady=10)
        
        # Large score display
        score_text = f"{self.app.current_score}/{self.app.current_max_score}"
        score_label = self.app.create_widget(
            tk.Label,
            score_display_frame,
            text=score_text,
            font=("Arial", 36, "bold")
        )
        score_label.pack()
        
        # Percentage display
        percentage_text = f"{self.app.current_percentage:.1f}%"
        percentage_label = self.app.create_widget(
            tk.Label,
            score_display_frame,
            text=percentage_text,
            font=("Arial", 24)
        )
        percentage_label.pack()
        
        # Sentiment Score display (if available)
        if hasattr(self.app, 'sentiment_score') and self.app.sentiment_score is not None:
            sentiment_frame = self.app.create_widget(tk.Frame, score_display_frame)
            sentiment_frame.pack(pady=10)
            
            # Sentiment label
            self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text="Emotional Sentiment:",
                font=("Arial", 12, "bold")
            ).pack()
            
            # Sentiment score with color coding
            if self.app.sentiment_score < -20:
                sentiment_color = "#D32F2F"  # Red for negative
                sentiment_label_text = "Negative"
            elif self.app.sentiment_score > 20:
                sentiment_color = "#388E3C"  # Green for positive
                sentiment_label_text = "Positive"
            else:
                sentiment_color = "#FBC02D"  # Yellow for neutral
                sentiment_label_text = "Neutral"
            
            sentiment_score_label = self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text=f"{self.app.sentiment_score:+.1f} ({sentiment_label_text})",
                font=("Arial", 18, "bold"),
                fg=sentiment_color
            )
            sentiment_score_label.pack()
            
            # Sentiment explanation
            sentiment_desc = ""
            if self.app.sentiment_score < -60:
                sentiment_desc = "Your reflection shows significant distress"
            elif self.app.sentiment_score < -20:
                sentiment_desc = "Your reflection indicates some negative emotion"
            elif self.app.sentiment_score > 60:
                sentiment_desc = "Your reflection shows strong positive emotion"
            elif self.app.sentiment_score > 20:
                sentiment_desc = "Your reflection indicates positive feelings"
            else:
                sentiment_desc = "Your reflection shows balanced emotions"
            
            self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text=sentiment_desc,
                font=("Arial", 10),
                fg=self.app.colors["fg"]
            ).pack()
        
        
        # Progress bar visualization
        progress_frame = self.app.create_widget(tk.Frame, summary_frame)
        progress_frame.pack(pady=20)
        
        self.app.create_widget(
            tk.Label,
            progress_frame,
            text="Your EQ Score Progress:",
            font=("Arial", 12, "bold")
        ).pack(pady=5)
        
        # Create progress bar canvas
        progress_canvas = tk.Canvas(progress_frame, width=400, height=30, bg=self.app.colors["bg"], highlightthickness=0)
        progress_canvas.pack()
        
        # Draw progress bar
        progress_width = 400
        fill_width = (self.app.current_percentage / 100) * progress_width
        
        # Determine color based on score
        if self.app.current_percentage >= 80:
            bar_color = self.app.colors["excellent"]
            level = "Excellent"
        elif self.app.current_percentage >= 65:
            bar_color = self.app.colors["good"]
            level = "Good"
        elif self.app.current_percentage >= 50:
            bar_color = self.app.colors["average"]
            level = "Average"
        else:
            bar_color = self.app.colors["needs_work"]
            level = "Needs Work"
        
        # Draw background
        progress_canvas.create_rectangle(0, 0, progress_width, 30, fill="#e0e0e0", outline="")
        # Draw fill
        progress_canvas.create_rectangle(0, 0, fill_width, 30, fill=bar_color, outline="")
        # Draw text
        progress_canvas.create_text(progress_width/2, 15, text=f"{level} - {self.app.current_percentage:.1f}%", 
                                  fill="white" if self.app.current_percentage > 50 else "black",
                                  font=("Arial", 10, "bold"))
        
        # Score markers
        markers_frame = self.app.create_widget(tk.Frame, progress_frame)
        markers_frame.pack(fill="x", pady=5)
        
        for i in range(0, 101, 25):
            marker_label = self.app.create_widget(
                tk.Label,
                markers_frame,
                text=f"{i}%",
                font=("Arial", 8)
            )
            marker_label.pack(side="left", expand=True)
        
        # --- SENTIMENT ANALYSIS DISPLAY ---
        if hasattr(self.app, 'sentiment_score') and self.app.sentiment_score is not None:
            sentiment_frame = self.app.create_widget(tk.Frame, summary_frame)
            sentiment_frame.pack(fill="x", pady=20, padx=20)
            
            self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text="Emotional Sentiment:",
                font=("Arial", 14, "bold")
            ).pack(anchor="w")
            
            # Color coding
            if self.app.sentiment_score > 20:
                s_color = "green"
                s_text = "Positive Outlook"
            elif self.app.sentiment_score < -20:
                s_color = "red"
                s_text = "Negative Emotion"
            else:
                s_color = "#FFC107" # Amber
                s_text = "Neutral/Balanced"
                
            self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text=f"{self.app.sentiment_score:+.1f} ({s_text})",
                font=("Arial", 18, "bold"),
                fg=s_color
            ).pack(anchor="w", pady=5)
            
            # Description
            if self.app.sentiment_score < -60:
                desc = "Your reflection shows significant distress."
            elif self.app.sentiment_score < -20:
                desc = "Your reflection indicates some negative emotion."
            elif self.app.sentiment_score > 60:
                desc = "Your reflection shows strong positive emotion!"
            elif self.app.sentiment_score > 20:
                desc = "Your reflection indicates positive feelings."
            else:
                desc = "Your reflection shows balanced emotions."
                
            self.app.create_widget(
                tk.Label,
                sentiment_frame,
                text=desc,
                font=("Arial", 11, "italic"),
                wraplength=400
            ).pack(anchor="w")
        # ----------------------------------
        
        # BENCHMARK SECTION
        benchmark_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        benchmark_frame.pack(fill="x", pady=20, padx=20)
        
        self.app.create_widget(
            tk.Label,
            benchmark_frame,
            text="Benchmark Analysis",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=10)
        
        # Benchmark interpretations
        if benchmark_interpretations:
            interpretation_frame = self.app.create_widget(tk.Frame, benchmark_frame)
            interpretation_frame.pack(fill="x", pady=10)
            
            for interpretation in benchmark_interpretations:
                self.app.create_widget(
                    tk.Label,
                    interpretation_frame,
                    text=f"ΓÇó {interpretation}",
                    font=("Arial", 10),
                    anchor="w"
                ).pack(anchor="w", pady=2)
        
        # Benchmark chart
        if comparisons:
            self.create_benchmark_chart(benchmark_frame, comparisons)
        
        # Detailed benchmark stats
        if "global" in comparisons:
            stats_frame = self.app.create_widget(tk.Frame, benchmark_frame)
            stats_frame.pack(fill="x", pady=10)
            
            comp = comparisons["global"]
            stats_text = f"""
            Global Comparison:
            ΓÇó Your Score: {comp['your_score']}
            ΓÇó Global Average: {comp['avg_score']} (based on {comp['sample_size']:,} people)
            ΓÇó Difference: {comp['difference']:+.1f}
            ΓÇó Percentile Rank: {comp['percentile']:.1f}th percentile
            """
            
            self.app.create_widget(
                tk.Label,
                stats_frame,
                text=stats_text.strip(),
                font=("Arial", 10),
                justify="left",
                anchor="w"
            ).pack(anchor="w")
        
        # EQ Category Analysis (simulated)
        categories_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        categories_frame.pack(fill="x", pady=20, padx=20)
        
        self.app.create_widget(
            tk.Label,
            categories_frame,
            text="EQ Category Analysis",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=10)
        
        categories = ["Self-Awareness", "Self-Regulation", "Motivation", "Empathy", "Social Skills"]
        for category in categories:
            cat_frame = self.app.create_widget(tk.Frame, categories_frame)
            cat_frame.pack(fill="x", pady=2)
            
            self.app.create_widget(
                tk.Label,
                cat_frame,
                text=category,
                font=("Arial", 10),
                width=15,
                anchor="w"
            ).pack(side="left")
            
            # Simulated category score
            cat_score = min(100, self.app.current_percentage + random.uniform(-10, 10))
            cat_canvas = tk.Canvas(cat_frame, width=200, height=15, bg=self.app.colors["bg"], highlightthickness=0)
            cat_canvas.pack(side="left", padx=10)
            
            cat_fill_width = (cat_score / 100) * 200
            cat_color = self.app.colors["good"] if cat_score >= 70 else self.app.colors["average"] if cat_score >= 50 else self.app.colors["needs_work"]
            
            cat_canvas.create_rectangle(0, 0, 200, 15, fill="#e0e0e0", outline="")
            cat_canvas.create_rectangle(0, 0, cat_fill_width, 15, fill=cat_color, outline="")
            cat_canvas.create_text(100, 7, text=f"{cat_score:.0f}%", fill="white" if cat_score > 50 else "black", font=("Arial", 8))
        
        # Test summary
        summary_text_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        summary_text_frame.pack(fill="x", pady=20, padx=20)
        
        summary_text = f"""
        Test Summary:
        ΓÇó Questions Answered: {len(self.app.responses)}/{len(self.app.questions)}
        ΓÇó Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        ΓÇó Age Group: {self.app.age_group if self.app.age_group else 'Not specified'}
        ΓÇó Profession: {self.app.profession if self.app.profession else 'Not specified'}
        ΓÇó Average Response: {self.app.current_score/len(self.app.responses):.1f} out of 4 if self.app.responses else 0
        """
        
        self.app.create_widget(
            tk.Label,
            summary_text_frame,
            text=summary_text.strip(),
            font=("Arial", 10),
            justify="left",
            anchor="w"
        ).pack(anchor="w")
        
        # Buttons frame
        button_frame = self.app.create_widget(tk.Frame, scrollable_frame)
        button_frame.pack(pady=20, padx=20)
        
        # Grid Layout for Buttons
        # Row 0: AI Analysis (Center, Prominent)
        if self.app.ml_predictor:
            btn_ai = tk.Button(
                button_frame,
                text="≡ƒñû AI Analysis",
                command=self.show_ml_analysis,
                font=("Segoe UI", 12, "bold"),
                bg="#1976D2",
                fg="white",
                activebackground="#1565C0",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=20,
                pady=8
            )
            btn_ai.grid(row=0, column=0, columnspan=2, pady=(0, 15))
            
            def on_enter(e): btn_ai['bg'] = "#2196F3"
            def on_leave(e): btn_ai['bg'] = "#1976D2"
            btn_ai.bind("<Enter>", on_enter)
            btn_ai.bind("<Leave>", on_leave)

        # Row 1: Comparison & History
        row1_frame = tk.Frame(button_frame)
        row1_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if user has previous attempts
        cursor.execute(
            "SELECT COUNT(*) FROM scores WHERE username = ?",
            (self.app.username,)
        )
        previous_count = cursor.fetchone()[0]
        
        if previous_count > 1:
            self.app.create_widget(
                tk.Button,
                row1_frame,
                text="Compare Previous",
                command=self.show_comparison_screen,
                font=("Arial", 11),
                width=16
            ).pack(side="left", padx=5)
        
        # Export PDF Button
        if generate_pdf_report:
            self.app.create_widget(
                tk.Button,
                row1_frame,
                text="📄 Export Report",
                command=self.export_results_pdf,
                font=("Arial", 11),
                bg=self.app.colors["button_bg"], # Use standard or specific? Let's use standard but distinct if possible.
                fg=self.app.colors["button_fg"],
                width=16
            ).pack(side="left", padx=5)
        
        self.app.create_widget(
            tk.Button,
            row1_frame,
            text="View History",
            command=self.show_history_screen,
            font=("Arial", 11),
            width=16
        ).pack(side="left", padx=5)
        
        # Row 2: Standard Actions
        row2_frame = tk.Frame(button_frame)
        row2_frame.grid(row=2, column=0, columnspan=2, pady=5)

        self.app.create_widget(
            tk.Button,
            row2_frame,
            text="Take Another",
            command=self.reset_test,
            font=("Arial", 11),
            width=16
        ).pack(side="left", padx=5)
        
        self.app.create_widget(
            tk.Button,
            row2_frame,
            text="Main Menu",
            command=self.app.create_welcome_screen,
            font=("Arial", 11),
            width=16
        ).pack(side="left", padx=5)
        
        # Pack canvas and scrollbar (unchanged)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_ml_analysis(self):
        """Show AI-powered analysis in a popup window"""
        if not self.app.ml_predictor:
            messagebox.showerror("Error", "AI Model not loaded.")
            return
            
        try:
            # 1. Get Prediction
            result = self.app.ml_predictor.predict_with_explanation(
                self.app.responses,
                self.app.age,
                self.app.current_score,
                sentiment_score=self.app.sentiment_score
            )
            
            # 2. Create Layout
            popup = tk.Toplevel(self.app.root)
            popup.title("≡ƒñû SoulSense AI Analysis")
            popup.geometry("650x750")
            popup.configure(bg="#F5F5F5")

            # Main Scrollable Frame
            canvas = tk.Canvas(popup, bg="#F5F5F5")
            scrollbar = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#F5F5F5")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # --- CARD 1: OVERVIEW ---
            risk_color = "#D32F2F" if result['prediction'] == 2 else "#FBC02D" if result['prediction'] == 1 else "#388E3C"
            bg_color = "#FFEBEE" if result['prediction'] == 2 else "#FFFDE7" if result['prediction'] == 1 else "#E8F5E9"
            
            card1 = tk.Frame(scrollable_frame, bg="white", bd=1, relief="solid")
            card1.pack(fill="x", padx=20, pady=10)
            
            # Header
            header_frame = tk.Frame(card1, bg=risk_color, height=80)
            header_frame.pack(fill="x")
            
            tk.Label(
                header_frame, 
                text=result['prediction_label'].upper(), 
                font=("Arial", 18, "bold"),
                bg=risk_color,
                fg="white"
            ).pack(pady=10)
            
            tk.Label(
                header_frame,
                text=f"Confidence: {result['confidence']:.1%}",
                font=("Arial", 12),
                bg=risk_color,
                fg="white"
            ).pack(pady=(0, 10))

            tk.Label(
                card1, 
                text="Based on your inputs, the AI model suggests:", 
                font=("Arial", 11, "italic"),
                bg="white",
                fg="#555"
            ).pack(pady=15)

            # --- CARD 2: ACTION PLAN ---
            tk.Label(scrollable_frame, text="Γ£à RECOMMENDED ACTIONS", font=("Arial", 14, "bold"), bg="#F5F5F5", fg="#333").pack(anchor="w", padx=25, pady=(15,5))
            
            card2 = tk.Frame(scrollable_frame, bg="white", bd=0, highlightbackground="#ddd", highlightthickness=1)
            card2.pack(fill="x", padx=20)

            if 'recommendations' in result and result['recommendations']:
                for tip in result['recommendations']:
                    row = tk.Frame(card2, bg="white")
                    row.pack(fill="x", pady=10, padx=15)
                    
                    tk.Label(row, text="≡ƒö╣", font=("Arial", 12), bg="white", fg=risk_color).pack(side="left", anchor="n")
                    tk.Label(
                        row, 
                        text=tip, 
                        font=("Arial", 11), 
                        bg="white", 
                        fg="#333", 
                        wraplength=500, 
                        justify="left"
                    ).pack(side="left", padx=10)
            else:
                tk.Label(card2, text="No specific recommendations available.", bg="white").pack(pady=20)

            # --- CARD 3: TOP FACTORS ---
            tk.Label(scrollable_frame, text="≡ƒöì INFLUENCING FACTORS", font=("Arial", 14, "bold"), bg="#F5F5F5", fg="#333").pack(anchor="w", padx=25, pady=(20,5))
            
            card3 = tk.Frame(scrollable_frame, bg="white", bd=0, highlightbackground="#ddd", highlightthickness=1)
            card3.pack(fill="x", padx=20, pady=10)

            # Filter out non-5-point scale features for clean visualization
            visual_features = {k: v for k, v in result['features'].items() 
                             if k not in ['total_score', 'age', 'average_score']}
            
            sorted_features = sorted(visual_features.items(), key=lambda x: result['feature_importance'].get(x[0], 0), reverse=True)[:3]
            
            for feature, value in sorted_features:
                imp = result['feature_importance'].get(feature, 0)
                f_name = feature.replace('_', ' ').title()
                
                f_row = tk.Frame(card3, bg="white")
                f_row.pack(fill="x", pady=8, padx=15)
                
                # Label Row (Name + Value)
                label_row = tk.Frame(f_row, bg="white")
                label_row.pack(fill="x", pady=(0, 2))
                
                tk.Label(
                    label_row, 
                    text=f_name, 
                    font=("Segoe UI", 11, "bold"), 
                    bg="white", 
                    fg="#444"
                ).pack(side="left")
                
                # Format Score
                if feature == 'sentiment_score':
                    score_text = f"{value:+.1f}"
                elif feature == 'total_score':
                    score_text = f"{value/25*100:.0f}/100"
                else:
                    # Assume 5-point scale
                    score_text = f"{value*20:.0f}/100"
                
                tk.Label(
                    label_row, 
                    text=score_text, 
                    font=("Segoe UI", 11, "bold"), 
                    bg="white", 
                    fg="#666"
                ).pack(side="right")
                
                # Progress Bar
                bar_bg = tk.Frame(f_row, bg="#F0F2F5", height=12, width=400)
                bar_bg.pack(fill="x", pady=2)
                bar_bg.pack_propagate(False)
                
                fill_width = int(520 * imp * 3.5) # Scale to available width
                # Note: fill_width is relative to parent, simplified here as frame width isn't fixed yet
                # We use a fractional width approach or fixed max
                
                tk.Frame(
                    bar_bg, 
                    bg="#4CAF50" if imp < 0.1 else "#2196F3" if imp < 0.3 else "#FF9800", # Color by impact
                    height=12, 
                    width=fill_width
                ).pack(side="left")

            # Close Button
            btn_close = tk.Button(
                scrollable_frame,
                text="Close Analysis",
                command=popup.destroy,
                font=("Segoe UI", 12, "bold"),
                bg="#546E7A", # Blue Grey
                fg="white", 
                activebackground="#455A64",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=20,
                pady=10
            )
            btn_close.pack(pady=30)
            
            # Hover for close
            btn_close.bind("<Enter>", lambda e: btn_close.configure(bg="#455A64"))
            btn_close.bind("<Leave>", lambda e: btn_close.configure(bg="#546E7A"))
            
        except Exception as e:
            logging.error("AI Analysis failed", exc_info=True)
            messagebox.showerror("Analysis Error", f"Could not generate AI report.\n{e}")

    def show_history_screen(self):
        """Show history of all tests for the current user"""
        self.app.clear_screen()
        
        # Header with back button
        header_frame = self.app.create_widget(tk.Frame, self.app.root)
        header_frame.pack(pady=10, fill="x")
        
        self.app.create_widget(
            tk.Button,
            header_frame,
            text="ΓåÉ Back",
            command=self.app.create_welcome_screen,
            font=("Arial", 10)
        ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Label,
            header_frame,
            text="Test History" + (f" for {self.app.username}" if self.app.username else ""),
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=50)
        
        conn = get_connection()
        cursor = conn.cursor()

        # Get history data
        if not self.app.username:
            cursor.execute(
                """
                SELECT DISTINCT username FROM scores 
                ORDER BY timestamp DESC 
                LIMIT 5
                """
            )
            users = cursor.fetchall()
            
            if not users:
                self.app.create_widget(
                    tk.Label,
                    self.app.root,
                    text="No test history found. Please take a test first.",
                    font=("Arial", 12)
                ).pack(pady=50)
                
                self.app.create_widget(
                    tk.Button,
                    self.app.root,
                    text="Back to Main",
                    command=self.app.create_welcome_screen,
                    font=("Arial", 12)
                ).pack(pady=20)
                return
            
            # Show user selection
            user_frame = self.app.create_widget(tk.Frame, self.app.root)
            user_frame.pack(pady=20)
            
            self.app.create_widget(
                tk.Label,
                user_frame,
                text="Select a user to view their history:",
                font=("Arial", 12)
            ).pack(pady=10)
            
            for user in users:
                username = user[0]
                user_btn = self.app.create_widget(
                    tk.Button,
                    user_frame,
                    text=username,
                    command=lambda u=username: self.view_user_history(u),
                    font=("Arial", 12),
                    width=20
                )
                user_btn.pack(pady=5)
            
            return
        
        # If username is set, show that user's history
        self.display_user_history(self.app.username)

    def view_user_history(self, username):
        """View history for a specific user"""
        self.app.username = username
        self.display_user_history(username)

    def display_user_history(self, username):
        """Display history for a specific user"""
        self.app.clear_screen()
        
        conn = get_connection()
        cursor = conn.cursor()

        # Get history data
        cursor.execute(
            """
            SELECT id, total_score, age, timestamp 
            FROM scores 
            WHERE username = ? 
            ORDER BY timestamp DESC
            """,
            (username,)
        )
        history = cursor.fetchall()
        
        # Header with back button
        header_frame = self.app.create_widget(tk.Frame, self.app.root)
        header_frame.pack(pady=10, fill="x")
        
        self.app.create_widget(
            tk.Button,
            header_frame,
            text="ΓåÉ Back",
            command=self.show_history_screen,
            font=("Arial", 10)
        ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Label,
            header_frame,
            text=f"Test History for {username}",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=50)
        
        if not history:
            self.app.create_widget(
                tk.Label,
                self.app.root,
                text="No test history found.",
                font=("Arial", 12)
            ).pack(pady=50)
            
            self.app.create_widget(
                tk.Button,
                self.app.root,
                text="Back to History",
                command=self.show_history_screen,
                font=("Arial", 12)
            ).pack(pady=20)
            return
        
        # Create scrollable frame for history
        canvas = tk.Canvas(self.app.root, bg=self.app.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.app.root, orient="vertical", command=canvas.yview)
        scrollable_frame = self.app.create_widget(tk.Frame, canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display each test result
        for idx, (test_id, score, age, timestamp) in enumerate(history):
            # Calculate percentage (assuming 4 points per question)
            max_score = len(self.app.questions) * 4
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            test_frame = self.app.create_widget(tk.Frame, scrollable_frame, relief="groove", borderwidth=2)
            test_frame.pack(fill="x", padx=20, pady=5)
            
            # Format date
            try:
                date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
            except:
                date_str = str(timestamp)
            
            # Test info
            info_frame = self.app.create_widget(tk.Frame, test_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            self.app.create_widget(
                tk.Label,
                info_frame,
                text=f"Test #{test_id}",
                font=("Arial", 11, "bold"),
                anchor="w"
            ).pack(side="left", padx=5)
            
            self.app.create_widget(
                tk.Label,
                info_frame,
                text=f"Score: {score}/{max_score} ({percentage:.1f}%)",
                font=("Arial", 10),
                anchor="w"
            ).pack(side="left", padx=20)
            
            if age:
                self.app.create_widget(
                    tk.Label,
                    info_frame,
                    text=f"Age: {age}",
                    font=("Arial", 10),
                    anchor="w"
                ).pack(side="left", padx=20)
            
            self.app.create_widget(
                tk.Label,
                info_frame,
                text=date_str,
                font=("Arial", 9),
                anchor="w"
            ).pack(side="right", padx=5)
            
            # Progress bar visualization
            progress_frame = self.app.create_widget(tk.Frame, test_frame)
            progress_frame.pack(fill="x", padx=10, pady=2)
            
            # Progress bar using tkinter canvas
            bar_canvas = tk.Canvas(progress_frame, height=20, bg=self.app.colors["bg"], highlightthickness=0)
            bar_canvas.pack(fill="x")
            
            # Draw progress bar
            bar_width = 300
            fill_width = (percentage / 100) * bar_width
            
            # Background
            bar_canvas.create_rectangle(0, 0, bar_width, 20, fill="#cccccc", outline="")
            # Fill (green for current/latest test, blue for others)
            fill_color = "#4CAF50" if idx == 0 else "#2196F3"
            bar_canvas.create_rectangle(0, 0, fill_width, 20, fill=fill_color, outline="")
            # Percentage text
            text_color = "black" if self.app.current_theme == "light" else "white"
            bar_canvas.create_text(bar_width/2, 10, text=f"{percentage:.1f}%", fill=text_color)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = self.app.create_widget(tk.Frame, self.app.root)
        button_frame.pack(pady=20)
        
        if len(history) >= 2:
            self.app.create_widget(
                tk.Button,
                button_frame,
                text="Compare All Tests",
                command=self.show_comparison_screen,
                font=("Arial", 12)
            ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Button,
            button_frame,
            text="Back to Main",
            command=self.app.create_welcome_screen,
            font=("Arial", 12)
        ).pack(side="left", padx=10)

    def show_comparison_screen(self):
        """Show visual comparison of current test with previous attempts"""
        self.app.clear_screen()
        
        conn = get_connection()
        cursor = conn.cursor()

        # Get all test data for the current user
        cursor.execute(
            """
            SELECT id, total_score, timestamp 
            FROM scores 
            WHERE username = ? 
            ORDER BY timestamp ASC
            """,
            (self.app.username,)
        )
        all_tests = cursor.fetchall()
        
        if len(all_tests) < 2:
            messagebox.showinfo("No Comparison", "You need at least 2 tests to compare.")
            self.app.create_welcome_screen()
            return
        
        # Header with back button
        header_frame = self.app.create_widget(tk.Frame, self.app.root)
        header_frame.pack(pady=10, fill="x")
        
        self.app.create_widget(
            tk.Button,
            header_frame,
            text="ΓåÉ Back",
            command=self.show_history_screen,
            font=("Arial", 10)
        ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Label,
            header_frame,
            text=f"Test Comparison for {self.app.username}",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=50)
        
        self.app.create_widget(
            tk.Label,
            self.app.root,
            text=f"Showing {len(all_tests)} tests over time",
            font=("Arial", 12)
        ).pack(pady=5)
        
        # Prepare data for visualization
        test_numbers = list(range(1, len(all_tests) + 1))
        scores = [test[1] for test in all_tests]
        max_score = len(self.app.questions) * 4
        percentages = [(score / max_score) * 100 for score in scores]
        
        # Create main comparison frame
        comparison_frame = self.app.create_widget(tk.Frame, self.app.root)
        comparison_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Left side: Bar chart visualization
        left_frame = self.app.create_widget(tk.Frame, comparison_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        self.app.create_widget(
            tk.Label,
            left_frame,
            text="Score Comparison",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Create bar chart using tkinter canvas
        chart_canvas = tk.Canvas(left_frame, bg=self.app.colors["chart_bg"], height=300)
        chart_canvas.pack(fill="both", expand=True, pady=10)
        
        # Draw bar chart
        chart_width = 400
        chart_height = 250
        bar_width = 30
        spacing = 20
        
        # Find max value for scaling
        max_value = max(scores)
        scale_factor = chart_height * 0.8 / max_value if max_value > 0 else 1
        
        # Draw bars
        for i, (test_num, score, percentage) in enumerate(zip(test_numbers, scores, percentages)):
            x = i * (bar_width + spacing) + 50
            bar_height = score * scale_factor
            y = chart_height - bar_height
            
            # Color: green for current/latest test, blue for others
            color = self.app.colors["improvement_good"] if i == len(test_numbers) - 1 else "#2196F3"
            
            # Draw bar
            chart_canvas.create_rectangle(x, y, x + bar_width, chart_height, fill=color, outline="black")
            
            # Draw test number below bar
            chart_canvas.create_text(x + bar_width/2, chart_height + 15, 
                                   text=f"Test {test_num}", 
                                   fill=self.app.colors["chart_fg"])
            
            # Draw score above bar
            chart_canvas.create_text(x + bar_width/2, y - 15, 
                                   text=f"{score}", 
                                   fill=self.app.colors["chart_fg"], 
                                   font=("Arial", 10, "bold"))
            
            # Draw percentage inside bar
            chart_canvas.create_text(x + bar_width/2, y + bar_height/2, 
                                   text=f"{percentage:.0f}%", 
                                   fill="white", 
                                   font=("Arial", 9, "bold"))
        
        # Draw Y-axis labels
        for i in range(0, max_score + 1, 10):
            y = chart_height - (i * scale_factor)
            chart_canvas.create_text(30, y, text=str(i), fill=self.app.colors["chart_fg"])
            chart_canvas.create_line(40, y, 45, y, fill=self.app.colors["chart_fg"])
        
        chart_canvas.create_text(20, 15, text="Score", fill=self.app.colors["chart_fg"], angle=90)
        
        # Right side: Statistics and improvement
        right_frame = self.app.create_widget(tk.Frame, comparison_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        self.app.create_widget(
            tk.Label,
            right_frame,
            text="Statistics & Improvement",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Calculate statistics
        first_score = scores[0]
        last_score = scores[-1]
        best_score = max(scores)
        worst_score = min(scores)
        avg_score = sum(scores) / len(scores)
        improvement = last_score - first_score
        improvement_percent = ((last_score - first_score) / first_score * 100) if first_score > 0 else 0
        
        # Display statistics
        stats_text = f"""
        First Test: {first_score} ({percentages[0]:.1f}%)
        Latest Test: {last_score} ({percentages[-1]:.1f}%)
        Best Score: {best_score} ({max(percentages):.1f}%)
        Worst Score: {worst_score} ({min(percentages):.1f}%)
        Average: {avg_score:.1f} ({(sum(percentages)/len(percentages)):.1f}%)
        """
        
        stats_label = self.app.create_widget(
            tk.Label,
            right_frame,
            text=stats_text.strip(),
            font=("Arial", 12),
            justify="left"
        )
        stats_label.pack(pady=10, padx=20, anchor="w")
        
        # Improvement indicator
        improvement_frame = self.app.create_widget(tk.Frame, right_frame)
        improvement_frame.pack(pady=20, padx=20, fill="x")
        
        improvement_color = self.app.colors["improvement_good"] if improvement > 0 else self.app.colors["improvement_bad"] if improvement < 0 else self.app.colors["improvement_neutral"]
        improvement_symbol = "Γåæ" if improvement > 0 else "Γåô" if improvement < 0 else "ΓåÆ"
        
        self.app.create_widget(
            tk.Label,
            improvement_frame,
            text="Overall Improvement:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        improvement_text = f"{improvement_symbol} {improvement:+.1f} points ({improvement_percent:+.1f}%)"
        improvement_label = self.app.create_widget(
            tk.Label,
            improvement_frame,
            text=improvement_text,
            font=("Arial", 12, "bold"),
            fg=improvement_color
        )
        improvement_label.pack(pady=5)
        
        # Interpretation of improvement
        if improvement > 10:
            interpretation = "Excellent progress! Keep up the good work."
        elif improvement > 5:
            interpretation = "Good improvement. You're getting better!"
        elif improvement > 0:
            interpretation = "Slight improvement. Every bit counts!"
        elif improvement == 0:
            interpretation = "Consistent performance. Try to push further next time."
        else:
            interpretation = "Need to focus on improvement. Review your responses."
        
        self.app.create_widget(
            tk.Label,
            improvement_frame,
            text=interpretation,
            font=("Arial", 10),
            wraplength=200
        ).pack(pady=10)
        
        # Trend visualization (simple arrow indicators)
        trend_frame = self.app.create_widget(tk.Frame, right_frame)
        trend_frame.pack(pady=10)
        
        self.app.create_widget(
            tk.Label,
            trend_frame,
            text="Score Trend:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        # Create simple trend line
        trend_canvas = tk.Canvas(trend_frame, width=200, height=80, bg=self.app.colors["chart_bg"])
        trend_canvas.pack(pady=10)
        
        # Draw trend line
        points = []
        for i, percentage in enumerate(percentages):
            x = i * (180 / (len(percentages) - 1)) + 10 if len(percentages) > 1 else 100
            y = 70 - (percentage * 60 / 100)
            points.append((x, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                color = self.app.colors["improvement_good"] if y2 < y1 else self.app.colors["improvement_bad"] if y2 > y1 else self.app.colors["improvement_neutral"]
                trend_canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
        
        for i, (x, y) in enumerate(points):
            color = self.app.colors["improvement_good"] if i == len(points) - 1 else "#2196F3"
            trend_canvas.create_oval(x-3, y-3, x+3, y+3, fill=color, outline="black")
        
        # Buttons at bottom
        button_frame = self.app.create_widget(tk.Frame, self.app.root)
        button_frame.pack(pady=20)
        
        self.app.create_widget(
            tk.Button,
            button_frame,
            text="View Detailed History",
            command=self.show_history_screen,
            font=("Arial", 12)
        ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Button,
            button_frame,
            text="Take Another Test",
            command=self.reset_test,
            font=("Arial", 12)
        ).pack(side="left", padx=10)
        
        self.app.create_widget(
            tk.Button,
            button_frame,
            text="Back to Main",
            command=self.app.create_welcome_screen,
            font=("Arial", 12)
        ).pack(side="left", padx=10)

    def reset_test(self):
        """Reset test variables and start over"""
        self.app.username = ""
        self.app.age = None
        self.app.age_group = None
        self.app.profession = None
        self.app.current_question = 0
        self.app.responses = []
        self.app.current_score = 0
        self.app.current_max_score = 0
        self.app.current_percentage = 0
        self.app.auth.create_username_screen()
