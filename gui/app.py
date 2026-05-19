import tkinter as tk
from tkinter import ttk, simpledialog
import csv
from pathlib import Path
import requests


class CourseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Course App - Alexandros Dimitrakopoulos - AM: 12345")
        self.root.geometry("1250x720")

        self.base_dir = Path(__file__).resolve().parent.parent
        self.csv_path = self.base_dir / "data" / "courses_12345.csv"
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        self.setup_variables()
        self.setup_layout()

        self.sample_courses = [
            {
                "title": "Python Basics",
                "provider": "OpenLearn",
                "category": "Computer Science",
                "difficulty": "Beginner",
                "cost": 0.0,
                "duration": 12.0,
                "language": "English",
            },
            {
                "title": "AI Fundamentals",
                "provider": "Coursera",
                "category": "Artificial Intelligence",
                "difficulty": "Intermediate",
                "cost": 49.0,
                "duration": 20.0,
                "language": "English",
            },
            {
                "title": "Web Development 101",
                "provider": "edX",
                "category": "Web Development",
                "difficulty": "Beginner",
                "cost": 0.0,
                "duration": 15.0,
                "language": "English",
            },
            {
                "title": "Data Science Intro",
                "provider": "FutureLearn",
                "category": "Data Science",
                "difficulty": "Beginner",
                "cost": 30.0,
                "duration": 18.0,
                "language": "English",
            },
            {
                "title": "Algorithms",
                "provider": "UniPatras",
                "category": "Computer Science",
                "difficulty": "Advanced",
                "cost": 0.0,
                "duration": 30.0,
                "language": "Greek",
            },
        ]

        self.current_courses = self.sample_courses.copy()
        self.populate_table(self.current_courses)
        self.update_filter_values(self.current_courses)

    def setup_variables(self):
        self.category_var = tk.StringVar(value="All")
        self.difficulty_var = tk.StringVar(value="All")
        self.cost_var = tk.StringVar(value="All")
        self.language_var = tk.StringVar(value="All")

    def setup_layout(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Button(top_frame, text="Collect API Data", command=self.collect_api_data).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Collect Scraping Data", command=self.collect_scraping_data).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Load CSV", command=self.load_csv).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(side="left", padx=5)

        filter_frame = ttk.LabelFrame(self.root, text="Filters", padding=10)
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

        table_frame = ttk.LabelFrame(self.root, text="Courses", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("title", "provider", "category", "difficulty", "cost", "duration", "language")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.tree.heading("title", text="Title")
        self.tree.heading("provider", text="Provider")
        self.tree.heading("category", text="Category")
        self.tree.heading("difficulty", text="Difficulty")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("language", text="Language")

        self.tree.column("title", width=260)
        self.tree.column("provider", width=150)
        self.tree.column("category", width=190)
        self.tree.column("difficulty", width=120)
        self.tree.column("cost", width=80)
        self.tree.column("duration", width=90)
        self.tree.column("language", width=100)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        chart_frame = ttk.LabelFrame(self.root, text="Charts", padding=10)
        chart_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(chart_frame, text="Bar Chart", command=self.show_bar_chart).pack(side="left", padx=5)
        ttk.Button(chart_frame, text="Pie Chart", command=self.show_pie_chart).pack(side="left", padx=5)
        ttk.Button(chart_frame, text="Line Plot", command=self.show_line_plot).pack(side="left", padx=5)

        recommendation_frame = ttk.LabelFrame(self.root, text="Recommendations", padding=10)
        recommendation_frame.pack(fill="x", padx=10, pady=5)

        self.recommendation_label = ttk.Label(
            recommendation_frame,
            text="Top 3 course suggestions will appear here"
        )
        self.recommendation_label.pack(anchor="w")

        self.status_label = ttk.Label(self.root, text="Ready", padding=10)
        self.status_label.pack(fill="x")

    def normalize_text(self, value, default="Unknown"):
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def normalize_cost(self, value):
        if value in [None, "", "null"]:
            return 0.0
        try:
            return float(value)
        except Exception:
            text = str(value).strip().lower()
            if "free" in text:
                return 0.0
            return 0.0

    def normalize_duration(self, value):
        if value in [None, "", "null"]:
            return 0.0
        try:
            return float(value)
        except Exception:
            return 0.0

    def pick_value(self, item, possible_keys, default=None):
        for key in possible_keys:
            if key in item and item[key] not in [None, ""]:
                return item[key]
        return default

    def map_api_item_to_course(self, item):
        title = self.pick_value(item, ["title", "name", "course_title", "label"], "Unknown Title")
        provider = self.pick_value(item, ["provider", "university", "institution", "source", "organization"], "Unknown Provider")
        category = self.pick_value(item, ["category", "subject", "topic", "domain", "field"], "General")
        difficulty = self.pick_value(item, ["difficulty", "level", "skill_level"], "Unknown")
        cost = self.pick_value(item, ["cost", "price", "fee"], 0.0)
        duration = self.pick_value(item, ["duration", "duration_hours", "hours", "length"], 0.0)
        language = self.pick_value(item, ["language", "lang", "locale"], "Unknown")

        return {
            "title": self.normalize_text(title, "Unknown Title"),
            "provider": self.normalize_text(provider, "Unknown Provider"),
            "category": self.normalize_text(category, "General"),
            "difficulty": self.normalize_text(difficulty, "Unknown"),
            "cost": self.normalize_cost(cost),
            "duration": self.normalize_duration(duration),
            "language": self.normalize_text(language, "Unknown"),
        }

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
                    course["cost"],
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

    def collect_api_data(self):
        api_url = simpledialog.askstring("API URL", "Enter API URL:")

        if not api_url:
            self.status_label.config(text="API collection cancelled")
            return

        try:
            self.status_label.config(text="Fetching API data...")
            self.root.update_idletasks()

            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            mapped_courses = []

            if "learn.microsoft.com/api/catalog" in api_url:
                raw_items = []
                raw_items.extend(data.get("modules", []))
                raw_items.extend(data.get("learningPaths", []))
                raw_items.extend(data.get("courses", []))

                for item in raw_items:
                    products = item.get("products", [])
                    subjects = item.get("subjects", [])
                    levels = item.get("levels", [])

                    category_value = "General"
                    if products and len(products) > 0:
                        category_value = products[0]
                    elif subjects and len(subjects) > 0:
                        category_value = subjects[0]

                    difficulty_value = levels[0] if levels and len(levels) > 0 else "Unknown"

                    duration_minutes = item.get("durationInMinutes", 0)
                    duration_hours = round(float(duration_minutes) / 60, 2) if duration_minutes else 0.0

                    mapped_courses.append({
                        "title": self.normalize_text(item.get("title"), "Unknown Title"),
                        "provider": "Microsoft Learn",
                        "category": self.normalize_text(category_value, "General"),
                        "difficulty": self.normalize_text(difficulty_value, "Unknown"),
                        "cost": 0.0,
                        "duration": duration_hours,
                        "language": self.normalize_text(item.get("locale"), "Unknown"),
                    })
            else:
                raw_items = self.extract_list_from_json(data)

                for item in raw_items:
                    if isinstance(item, dict):
                        mapped_courses.append(self.map_api_item_to_course(item))

            if not mapped_courses:
                self.status_label.config(text="No valid course-like records found from API")
                return

            self.current_courses = mapped_courses
            self.populate_table(self.current_courses)
            self.update_filter_values(self.current_courses)
            self.export_csv(silent=True)

            self.status_label.config(text=f"Loaded {len(mapped_courses)} API records and saved to {self.csv_path.name}")

        except Exception as e:
            self.status_label.config(text=f"API load failed: {e}")

    def collect_scraping_data(self):
        self.status_label.config(text="Collect Scraping Data clicked")

    def load_csv(self):
        if not self.csv_path.exists():
            self.status_label.config(text=f"CSV file not found: {self.csv_path}")
            return

        try:
            loaded_courses = []

            with open(self.csv_path, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    loaded_courses.append({
                        "title": row.get("Title") or row.get("title", ""),
                        "provider": row.get("Provider") or row.get("provider", ""),
                        "category": row.get("Category") or row.get("category", ""),
                        "difficulty": row.get("Difficulty") or row.get("difficulty", ""),
                        "cost": float(row.get("Cost") or row.get("cost", 0) or 0),
                        "duration": float(row.get("Duration") or row.get("duration", 0) or 0),
                        "language": row.get("Language") or row.get("language", ""),
                    })

            self.current_courses = loaded_courses
            self.populate_table(self.current_courses)
            self.update_filter_values(self.current_courses)
            self.status_label.config(text=f"Loaded {len(self.current_courses)} course(s) from {self.csv_path.name}")

        except Exception as e:
            self.status_label.config(text=f"Load failed: {e}")

    def export_csv(self, silent=False):
        headers = ["Title", "Provider", "Category", "Difficulty", "Cost", "Duration", "Language"]

        try:
            with open(self.csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)

                for row_id in self.tree.get_children():
                    row_values = self.tree.item(row_id)["values"]
                    writer.writerow(row_values)

            if not silent:
                self.status_label.config(text=f"CSV exported successfully to {self.csv_path}")

        except Exception as e:
            self.status_label.config(text=f"Export failed: {e}")

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

    def show_bar_chart(self):
        self.status_label.config(text="Bar Chart clicked")

    def show_pie_chart(self):
        self.status_label.config(text="Pie Chart clicked")

    def show_line_plot(self):
        self.status_label.config(text="Line Plot clicked")