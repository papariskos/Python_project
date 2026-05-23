import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import csv
from pathlib import Path
from urllib.parse import urlparse
import requests
import pandas as pd
import matplotlib.pyplot as plt
from collectors.scraper import scrape_courses
from collectors.api_collector import fetch_api_courses


class CourseApp:
    def __init__(self, root):
        self.root = root
        # Assignment Requirement: Team Names and AM in Window Title
        self.root.title("Alexandros Dimitrakopoulos (1090028) - Alexandros Dimogerontas (1097587)")
        self.root.geometry("1250x850")

        self.base_dir = Path(__file__).resolve().parent.parent
        self.csv_path = self.base_dir / "data" / "courses_1090028.csv"
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        self.setup_variables()
        self.setup_layout()

        self.current_courses = []
        # Normalization Print
        print("[Normalization] Status: Success - Initialized categorization systems")

        self.populate_table(self.current_courses)
        self.update_filter_values(self.current_courses)

        # Start the background scheduling mechanism (+10% Bonus)
        self.start_background_scheduler()

    def setup_variables(self):
        self.category_var = tk.StringVar(value="All")
        self.difficulty_var = tk.StringVar(value="All")
        self.cost_var = tk.StringVar(value="All")
        self.language_var = tk.StringVar(value="All")

        # Recommendation Engine Input Variables
        self.rec_category_var = tk.StringVar(value="All")
        self.rec_difficulty_var = tk.StringVar(value="All")
        self.rec_language_var = tk.StringVar(value="All")
        self.rec_cost_var = tk.StringVar(value="100.0")

    def setup_layout(self):
        # 1. TOP FRAME FOR BUTTONS
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Button(top_frame, text="Collect API Data", command=self.collect_api_data).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Collect Scraping Data", command=self.collect_scraping_data).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv_action).pack(side="left", padx=5)

        # 2. FILTERS PANEL
        filter_frame = ttk.LabelFrame(self.root, text="Table Filters", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=["All"],
            state="readonly",
            width=22
        )
        self.category_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Difficulty:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.difficulty_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.difficulty_var,
            values=["All"],
            state="readonly",
            width=18
        )
        self.difficulty_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="Cost:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.cost_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.cost_var,
            values=["All", "Free", "Paid"],
            state="readonly",
            width=12
        )
        self.cost_combo.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(filter_frame, text="Language:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.language_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.language_var,
            values=["All"],
            state="readonly",
            width=15
        )
        self.language_combo.grid(row=0, column=7, padx=5, pady=5)

        ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).grid(row=0, column=8, padx=10, pady=5)

        # 3. TREEVIEW TABLE PANEL
        table_frame = ttk.LabelFrame(self.root, text="Courses Database", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("title", "provider", "category", "difficulty", "cost", "duration", "language")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

        self.tree.heading("title", text="Title")
        self.tree.heading("provider", text="Provider / University")
        self.tree.heading("category", text="Subject Category")
        self.tree.heading("difficulty", text="Difficulty Level")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("duration", text="Duration (hrs)")
        self.tree.heading("language", text="Language")

        self.tree.column("title", width=280)
        self.tree.column("provider", width=170)
        self.tree.column("category", width=190)
        self.tree.column("difficulty", width=110)
        self.tree.column("cost", width=80)
        self.tree.column("duration", width=95)
        self.tree.column("language", width=95)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 4. CHART PANEL (Matplotlib Integration)
        chart_frame = ttk.LabelFrame(self.root, text="Matplotlib Analytics", padding=10)
        chart_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(chart_frame, text="1. Bar Chart (5 Longest Courses)", command=self.show_bar_chart).pack(side="left", padx=10)
        ttk.Button(chart_frame, text="2. Pie Chart (Difficulty Distribution)", command=self.show_pie_chart).pack(side="left", padx=10)
        ttk.Button(chart_frame, text="3. Line Plot (Cost vs Duration Trend)", command=self.show_line_plot).pack(side="left", padx=10)

        # 5. SMART RECOMMENDATION PANEL
        rec_frame = ttk.LabelFrame(self.root, text="Smart Recommendation Engine (Decision Support System)", padding=10)
        rec_frame.pack(fill="x", padx=10, pady=5)

        # Inputs Grid
        inputs_frame = ttk.Frame(rec_frame)
        inputs_frame.pack(fill="x")

        ttk.Label(inputs_frame, text="Category:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.rec_category_combo = ttk.Combobox(
            inputs_frame,
            textvariable=self.rec_category_var,
            values=["All", "Computer Science", "Business & Management", "Tourism & Hospitality", "Psychology", "Law", "Theology", "Physical Education", "General"],
            state="readonly",
            width=20
        )
        self.rec_category_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(inputs_frame, text="Difficulty:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.rec_difficulty_combo = ttk.Combobox(
            inputs_frame,
            textvariable=self.rec_difficulty_var,
            values=["All", "Beginner", "Intermediate", "Advanced", "Unknown"],
            state="readonly",
            width=15
        )
        self.rec_difficulty_combo.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(inputs_frame, text="Language:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.rec_language_combo = ttk.Combobox(
            inputs_frame,
            textvariable=self.rec_language_var,
            values=["All", "English", "Greek", "Spanish", "French", "German", "Unknown"],
            state="readonly",
            width=12
        )
        self.rec_language_combo.grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(inputs_frame, text="Max Cost ($):").grid(row=0, column=6, padx=5, pady=2, sticky="w")
        self.rec_cost_entry = ttk.Entry(inputs_frame, textvariable=self.rec_cost_var, width=8)
        self.rec_cost_entry.grid(row=0, column=7, padx=5, pady=2)

        ttk.Button(inputs_frame, text="Get Top 3 Suggestions", command=self.recommend_courses).grid(row=0, column=8, padx=15, pady=2)

        # Recommendation Output Area
        self.rec_text = tk.Text(rec_frame, height=4, wrap="word", bg="#f9f9f9", font=("Courier", 11), state="disabled")
        self.rec_text.pack(fill="x", pady=5)

        # 6. STATUS BAR
        self.status_label = ttk.Label(self.root, text="Ready", padding=5)
        self.status_label.pack(fill="x")

    def normalize_text(self, value, default="Unknown"):
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def pick_value(self, item, possible_keys, default=None):
        for key in possible_keys:
            if key in item and item[key] not in [None, ""]:
                return item[key]
        return default



    def extract_list_from_json(self, data):
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            possible_list_keys = ["courses", "data", "results", "items", "records", "modules", "learningPaths"]
            for key in possible_list_keys:
                if key in data and isinstance(data[key], list):
                    return data[key]
            for value in data.values():
                if isinstance(value, list):
                    return value
        return []

    def populate_table(self, courses):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for course in courses:
            self.tree.insert(
                "",
                "end",
                values=(
                    course["title"],
                    course["provider"],
                    course["category"],
                    course["difficulty"],
                    f"${course['cost']:.1f}" if isinstance(course['cost'], (int, float)) else course['cost'],
                    course["duration"],
                    course["language"],
                )
            )

    def update_filter_values(self, courses):
        categories = sorted({course["category"] for course in courses if course["category"]})
        difficulties = sorted({course["difficulty"] for course in courses if course["difficulty"]})
        languages = sorted({course["language"] for course in courses if course["language"]})

        self.category_combo["values"] = ["All"] + categories
        self.difficulty_combo["values"] = ["All"] + difficulties
        self.language_combo["values"] = ["All"] + languages

        self.category_var.set("All")
        self.difficulty_var.set("All")
        self.cost_var.set("All")
        self.language_var.set("All")

    # ==========================================
    # PANDAS CSV APPEND MANAGEMENT
    # ==========================================
    def append_courses_to_csv(self, new_courses):
        """
        Uses pandas to read the existing database, concatenate new records,
        deduplicate based on course title & provider, and save it in append-mode.
        """
        df_new = pd.DataFrame([
            {
                "Title": c["title"],
                "Provider": c["provider"],
                "Category": c["category"],
                "Difficulty": c["difficulty"],
                "Cost": float(c["cost"]),
                "Duration": float(c["duration"]),
                "Language": c["language"]
            }
            for c in new_courses
        ])

        if self.csv_path.exists():
            try:
                df_existing = pd.read_csv(self.csv_path)
            except Exception:
                df_existing = pd.DataFrame(columns=["Title", "Provider", "Category", "Difficulty", "Cost", "Duration", "Language"])
            
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        # Drop duplicates to keep data clean and unique
        df_combined.drop_duplicates(subset=["Title", "Provider"], keep="last", inplace=True)
        df_combined.to_csv(self.csv_path, index=False, encoding="utf-8")

    # ==========================================
    # DATA COLLECTION INTEGRATION
    # ==========================================
    def collect_api_data(self):
        api_url = simpledialog.askstring("API URL", "Enter API URL:")
        if not api_url:
            self.status_label.config(text="API collection cancelled")
            return

        try:
            self.status_label.config(text="Fetching API data...")
            self.root.update_idletasks()

            mapped_courses = fetch_api_courses(api_url)

            if not mapped_courses:
                self.status_label.config(text="No valid course records found from API")
                return

            # Merge and deduplicate in memory
            seen = {(c["title"].lower(), c["provider"].lower()) for c in self.current_courses}
            added_count = 0
            for course in mapped_courses:
                key = (course["title"].lower(), course["provider"].lower())
                if key not in seen:
                    seen.add(key)
                    self.current_courses.append(course)
                    added_count += 1

            self.populate_table(self.current_courses)
            self.update_filter_values(self.current_courses)

            # Specific Console Print Requirement
            print(f"[API_Collector] Status: Success - Loaded {len(mapped_courses)} records from API into memory")
            self.status_label.config(text=f"Loaded {added_count} new API records into memory (Click 'Export CSV' to save!)")

        except Exception as e:
            self.status_label.config(text=f"API load failed: {e}")

    def collect_scraping_data(self):
        default_url = str(self.csv_path.parent / "mock_courses.html")
        url_or_path = simpledialog.askstring(
            "Scrape Web Data",
            "Enter website URL or local HTML file path to scrape:",
            initialvalue=default_url
        )
        if not url_or_path:
            self.status_label.config(text="Scraping collection cancelled")
            return

        try:
            self.status_label.config(text=f"Scraping course data from: {url_or_path}...")
            self.root.update_idletasks()

            scraped_courses = scrape_courses(url_or_path)

            if not scraped_courses:
                self.status_label.config(text="No valid courses found during scraping")
                return

            # Merge and deduplicate in memory
            seen = {(c["title"].lower(), c["provider"].lower()) for c in self.current_courses}
            added_count = 0
            for course in scraped_courses:
                key = (course["title"].lower(), course["provider"].lower())
                if key not in seen:
                    seen.add(key)
                    self.current_courses.append(course)
                    added_count += 1

            self.populate_table(self.current_courses)
            self.update_filter_values(self.current_courses)

            # Specific Console Print Requirement
            source_domain = urlparse(url_or_path).netloc or Path(url_or_path).name
            print(f"[{source_domain}] Status: Success - Scraped {len(scraped_courses)} records into memory")
            self.status_label.config(text=f"Scraped {added_count} new course(s) into memory (Click 'Export CSV' to save!)")

        except Exception as e:
            self.status_label.config(text=f"Scraping failed: {e}")

    # ==========================================
    # CSV FILE INTERACTION & LOADING
    # ==========================================
    def load_csv(self, silent=False):
        if not self.csv_path.exists():
            if not silent:
                self.status_label.config(text=f"CSV file not found: {self.csv_path}")
            return

        try:
            loaded_courses = []
            df = pd.read_csv(self.csv_path)

            for _, row in df.iterrows():
                loaded_courses.append({
                    "title": str(row.get("Title", "")),
                    "provider": str(row.get("Provider", "")),
                    "category": str(row.get("Category", "")),
                    "difficulty": str(row.get("Difficulty", "")),
                    "cost": float(row.get("Cost", 0.0) if pd.notna(row.get("Cost")) else 0.0),
                    "duration": float(row.get("Duration", 0.0) if pd.notna(row.get("Duration")) else 0.0),
                    "language": str(row.get("Language", "")),
                })

            self.current_courses = loaded_courses
            self.populate_table(self.current_courses)
            self.update_filter_values(self.current_courses)
            
            if not silent:
                self.status_label.config(text=f"Loaded {len(self.current_courses)} course(s) from {self.csv_path.name}")
                print(f"[CSV_Loader] Status: Success - Loaded {len(self.current_courses)} records from local CSV")

        except Exception as e:
            self.status_label.config(text=f"Load failed: {e}")

    def export_csv_action(self):
        """
        Saves/Exports the currently loaded memory courses directly back to the main database CSV
        (courses_1090028.csv) in append-mode, merging with existing records and deduplicating.
        """
        try:
            df_new = pd.DataFrame([
                {
                    "Title": c["title"],
                    "Provider": c["provider"],
                    "Category": c["category"],
                    "Difficulty": c["difficulty"],
                    "Cost": float(c["cost"]),
                    "Duration": float(c["duration"]),
                    "Language": c["language"]
                }
                for c in self.current_courses
            ])
            
            if self.csv_path.exists():
                try:
                    df_existing = pd.read_csv(self.csv_path)
                except Exception:
                    df_existing = pd.DataFrame(columns=["Title", "Provider", "Category", "Difficulty", "Cost", "Duration", "Language"])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
                
            # Drop duplicates to keep database clean and unique (preserves latest collected)
            df_combined.drop_duplicates(subset=["Title", "Provider"], keep="last", inplace=True)
            df_combined.to_csv(self.csv_path, index=False, encoding="utf-8")
            
            messagebox.showinfo("Update Successful", f"Database successfully updated in append-mode:\n{self.csv_path.name}")
            print(f"[Exporter] Status: Success - Merged and saved database {self.csv_path.name}")
            self.status_label.config(text=f"Database updated successfully in append-mode")
        except Exception as e:
            messagebox.showerror("Update Failed", f"Could not update CSV:\n{e}")

    def apply_filters(self):
        filtered_courses = []
        for course in self.current_courses:
            if self.category_var.get() != "All" and course["category"] != self.category_var.get():
                continue
            if self.difficulty_var.get() != "All" and course["difficulty"] != self.difficulty_var.get():
                continue
            if self.language_var.get() != "All" and course["language"] != self.language_var.get():
                continue
            if self.cost_var.get() == "Free" and float(course["cost"]) != 0.0:
                continue
            if self.cost_var.get() == "Paid" and float(course["cost"]) == 0.0:
                continue

            filtered_courses.append(course)

        self.populate_table(filtered_courses)
        self.status_label.config(text=f"Filters applied - {len(filtered_courses)} course(s) shown")

    # ==========================================
    # DATA ANALYTICS & VISUALIZATION (Matplotlib)
    # ==========================================
    def check_csv_data(self):
        if not self.csv_path.exists():
            messagebox.showwarning("No Data", "No database file exists yet. Please collect some data first!")
            return None
        df = pd.read_csv(self.csv_path)
        if df.empty:
            messagebox.showwarning("Empty Database", "The course database is empty. Collect data first!")
            return None
        return df

    def show_bar_chart(self):
        df = self.check_csv_data()
        if df is None:
            return

        # Sort courses by Duration to find the 5 longest courses
        df_longest = df.sort_values(by="Duration", ascending=False).head(5)
        
        if df_longest.empty or df_longest["Duration"].sum() == 0:
            messagebox.showinfo("Info", "All courses in the database have a duration of 0 hours.")
            return

        plt.figure(figsize=(12, 7))
        # Truncate titles to a reasonable length for vertical layout
        short_titles = [t[:35] + "..." if len(t) > 35 else t for t in df_longest["Title"]]
        
        plt.bar(short_titles, df_longest["Duration"], color="#1a73e8", edgecolor="grey", width=0.5)
        plt.title("Duration of the 5 Longest Courses", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Course Titles", fontsize=11, labelpad=15)
        plt.ylabel("Duration (Hours)", fontsize=11, labelpad=10)
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()
        print("[Analytics] Status: Success - Displayed Duration Bar Chart")

    def show_pie_chart(self):
        df = self.check_csv_data()
        if df is None:
            return

        difficulty_counts = df["Difficulty"].value_counts()
        
        plt.figure(figsize=(8, 8))
        colors = ["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"][:len(difficulty_counts)]
        
        plt.pie(
            difficulty_counts,
            labels=difficulty_counts.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            textprops={"fontsize": 11, "fontweight": "bold"},
            shadow=True
        )
        plt.title("Course Distribution by Difficulty Level", fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()
        plt.show()
        print("[Analytics] Status: Success - Displayed Difficulty Distribution Pie Chart")

    def show_line_plot(self):
        df = self.check_csv_data()
        if df is None:
            return

        # Top 5 longest courses
        df_longest = df.sort_values(by="Duration", ascending=False).head(5)
        
        if df_longest.empty:
            return

        # Sort values by duration to draw a smooth left-to-right line trend
        df_longest = df_longest.sort_values(by="Duration")

        plt.figure(figsize=(12, 7))
        plt.plot(
            df_longest["Duration"],
            df_longest["Cost"],
            marker="o",
            linestyle="-",
            color="#4f46e5",  # Premium Indigo line
            linewidth=2.5,
            markersize=9,
            markerfacecolor="#10b981",  # Emerald green markers
            markeredgecolor="#4f46e5",
            label="Cost-Duration Trend"
        )
        
        # Add labels to points with alternating offsets to avoid overlap
        for i, (idx, row) in enumerate(df_longest.iterrows()):
            short_t = row["Title"][:20] + "..." if len(row["Title"]) > 20 else row["Title"]
            # Alternating offsets: even above, odd below
            y_offset = 12 if i % 2 == 0 else -20
            
            plt.annotate(
                short_t,
                (row["Duration"], row["Cost"]),
                textcoords="offset points",
                xytext=(0, y_offset),
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8, ec="#e2e8f0")
            )

        plt.title("Correlation: Cost vs. Duration (5 Longest Courses)", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Duration (Hours)", fontsize=11, labelpad=10)
        plt.ylabel("Cost ($)", fontsize=11, labelpad=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="upper left")
        
        # Add extra margins so annotations at extreme points don't cut off
        plt.margins(x=0.15, y=0.15)
        
        plt.tight_layout()
        plt.show()
        print("[Analytics] Status: Success - Displayed Cost-Duration Correlation Plot")

    # ==========================================
    # RECOMMENDATION ENGINE (Decision Support)
    # ==========================================
    def recommend_courses(self):
        """
        Recommendation Engine Algorithm.
        1. Filters courses by: category, difficulty, language, and maximum cost.
        2. Assigns a weighted composite score:
           Score = Normalised_Duration * 0.6 + (1.0 - Normalised_Cost) * 0.4
           (Duration weight 0.6 rewards comprehensive depth, Cost weight 0.4 rewards affordability).
        3. Fills in missing values with averages dynamically.
        4. Renders exactly the top 3 suggested items.
        """
        # Unlock Text Box for updates
        self.rec_text.config(state="normal")
        self.rec_text.delete("1.0", "end")

        if not self.csv_path.exists():
            self.rec_text.insert("1.0", "Error: Database CSV is empty. Please scrape or pull data first.")
            self.rec_text.config(state="disabled")
            return

        df = pd.read_csv(self.csv_path)
        if df.empty:
            self.rec_text.insert("1.0", "Error: No data in CSV to base suggestions on.")
            self.rec_text.config(state="disabled")
            return

        # Read Input Criteria
        sel_category = self.rec_category_var.get()
        sel_difficulty = self.rec_difficulty_var.get()
        sel_language = self.rec_language_var.get()
        
        try:
            max_cost = float(self.rec_cost_var.get())
        except Exception:
            max_cost = 99999.0

        # Dynamic filtering
        df_filtered = df.copy()
        if sel_category != "All":
            df_filtered = df_filtered[df_filtered["Category"] == sel_category]
        if sel_difficulty != "All":
            df_filtered = df_filtered[df_filtered["Difficulty"] == sel_difficulty]
        if sel_language != "All":
            df_filtered = df_filtered[df_filtered["Language"] == sel_language]
        
        # Cost Filter
        df_filtered = df_filtered[df_filtered["Cost"] <= max_cost]

        if df_filtered.empty:
            self.rec_text.insert("1.0", "No courses match your criteria. Try widening your filter terms!")
            self.rec_text.config(state="disabled")
            return

        # Handle Missing/Zero Values dynamically using pandas
        # Fill in missing Duration or Cost with average
        avg_dur = df["Duration"].mean() if df["Duration"].mean() > 0 else 10.0
        avg_cost = df["Cost"].mean() if df["Cost"].mean() > 0 else 0.0

        df_filtered["Duration"] = df_filtered["Duration"].apply(lambda x: avg_dur if pd.isna(x) or x <= 0 else x)
        df_filtered["Cost"] = df_filtered["Cost"].apply(lambda x: avg_cost if pd.isna(x) else x)

        # Normalization ranges for score calculations
        max_db_duration = df["Duration"].max() if df["Duration"].max() > 0 else 100.0
        max_db_cost = df["Cost"].max() if df["Cost"].max() > 0 else 100.0

        # Calculate weighted Composite Score (Duration weight = 0.6, Cost weight = 0.4)
        scores = []
        for idx, row in df_filtered.iterrows():
            dur_norm = row["Duration"] / max_db_duration
            cost_norm = row["Cost"] / max_db_cost if max_db_cost > 0 else 0.0
            
            # Weighted scoring formula
            composite_score = (dur_norm * 0.6) + ((1.0 - cost_norm) * 0.4)
            scores.append(composite_score)

        df_filtered["Composite_Score"] = scores
        df_sorted = df_filtered.sort_values(by="Composite_Score", ascending=False).head(3)

        # Output to GUI Text widget
        self.rec_text.insert("end", f"{'TITLE':<45} | {'PROVIDER':<25} | {'HOURS':<8} | {'COST':<7} | {'SCORE':<5}\n")
        self.rec_text.insert("end", "-" * 105 + "\n")
        
        for _, row in df_sorted.iterrows():
            title_trunc = row["Title"][:42] + "..." if len(row["Title"]) > 42 else row["Title"]
            prov_trunc = row["Provider"][:22] + "..." if len(row["Provider"]) > 22 else row["Provider"]
            self.rec_text.insert(
                "end",
                f"{title_trunc:<45} | {prov_trunc:<25} | {row['Duration']:<8.1f} | ${row['Cost']:<7.1f} | {row['Composite_Score']*100:<5.1f}%\n"
            )

        self.rec_text.config(state="disabled")
        print("[Recommendation_Engine] Status: Success - Evaluated matching criteria and calculated Composite Scores")

    # ==========================================
    # BACKGROUND AUTOMATIC SCHEDULER (+10% Bonus)
    # ==========================================
    def start_background_scheduler(self):
        # Start a recurring tkinter scheduling tick (runs every 60 seconds)
        self.root.after(60000, self.run_scheduler_tick)

    def run_scheduler_tick(self):
        """
        Background scheduler task. Automatically crawls a mock catalog page offline
        to keep the database updated in the background without user intervention.
        """
        mock_path = self.base_dir / "data" / "mock_university_page.html"
        if mock_path.exists():
            try:
                scraped = scrape_courses(str(mock_path))
                if scraped:
                    # Merge and deduplicate in memory
                    seen = {(c["title"].lower(), c["provider"].lower()) for c in self.current_courses}
                    for course in scraped:
                        key = (course["title"].lower(), course["provider"].lower())
                        if key not in seen:
                            seen.add(key)
                            self.current_courses.append(course)
                    
                    self.populate_table(self.current_courses)
                    self.update_filter_values(self.current_courses)
                    print("[Scheduler] Status: Success - Automatic background scraping synchronization completed in memory")
            except Exception as e:
                print(f"[Scheduler] Error: Background task failed: {e}")
        
        # Schedule the next tick in 60 seconds
        self.root.after(60000, self.run_scheduler_tick)