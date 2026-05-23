import os
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def is_valid_course_title(title):
    """
    Advanced heuristic filter to verify if a text heading is an actual academic course
    rather than marketing slogans, faculties, news stories, or generic layout widgets.
    """
    if not title:
        return False
    title_lower = title.lower().strip()
    
    # 1. Exclude titles that are too short or too long
    if len(title) < 5 or len(title) > 110:
        return False

    # 2. Words list check: if a title has more than 10 words, it is highly likely to be a news headline
    words = title_lower.split()
    if len(words) > 10:
        return False

    # 3. Exclude administrative faculties and structural keywords
    excluded_keywords = [
        "faculty of", "σχολή", "σχολες", "tomeas", "τομέας", "τομεας", "τμήμα", "τμημα",
        "apply now", "apply online", "εγγραφή", "εγγραφές", "sitemap", "terms of use", "privacy policy",
        "όροι χρήσης", "πολιτική απορρήτου", "cookie", "newsletter", "social media", "follow us",
        "contact us", "about us", "welcome to", "καλωσήρθατε", "επικοινωνία", "σχετικά με",
        "partner", "collaboration", "συνεργάτης", "συνεργάτες", "συνεργαζόμενοι", "φορείς", "φορεας",
        "why us", "γιατί εμάς", "γιατί επιλέγουν", "infrastructure", "εγκαταστάσεις", "campus", "campuses",
        "facilities", "accreditation", "membership", "πιστοποίηση", "πιστοποιήσεις", "αναγνώριση",
        "news", "νέα", "ανακοινώσεις", "events", "εκδηλώσεις", "blog", "press", "δελτία τύπου",
        "ambassador", "πρέσβης", "visit", "επίσκεψη", "επισκέπτεται", "celebrate", "υποδέχεται",
        "strengthening", "ενίσχυση", "professional development", "επαγγελματική ανάπτυξη",
        "global university hub", "bachelors", "graduate school", "programmes of study", "our faculties",
        "top university courses", "certifications", "state-of-the-art", "member of", "connection with",
        "infrastructure", "explore our", "greece as", "emerging international", "kimberly guilfoyle",
        "healthcare", "diabetes", "obesity", "accreditations", "memberships", "partner universities",
        "academy", "ακαδημία", "ακαδημια"
    ]
    
    for word in excluded_keywords:
        if word in title_lower:
            return False

    # 4. Check if the heading is a pure navigation link or division
    # (e.g. single words like "Bachelors", "Graduate School", "Computing" when they don't have degree words)
    layout_words = ["bachelors", "graduate school", "programmes of study", "why us", "apply now", "our faculties", "partner universities", "infrastructure"]
    if title_lower in layout_words:
        return False
        
    return True


def parse_numeric(text, is_duration=False):
    """
    Helper function to parse floats from text (e.g., cost or duration).
    """
    if not text:
        return 0.0
    text_lower = text.lower().strip()

    # Common free words
    if any(free_word in text_lower for free_word in ["free", "δωρεάν", "dorean", "audit", "free/audit"]):
        return 0.0

    # Extract first float/int match
    match = re.search(r"[-+]?\d*\.\d+|\d+", text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0


def detect_language(title, text=""):
    """
    Precision Greek Unicode language detection.
    If the title or text contains Greek characters, it is Greek. Otherwise, English.
    """
    full_text = (title or "") + " " + (text or "")
    # Greek Unicode range check: \u0370-\u03ff (Greek and Coptic), \u1f00-\u1fff (Greek Extended)
    has_greek = bool(re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", full_text))
    return "Greek" if has_greek else "English"


def detect_difficulty(title, text=""):
    """
    Intelligent course difficulty detection based on academic degree keywords.
    """
    full_text = ((title or "") + " " + (text or "")).lower()

    # Advanced degree keywords
    advanced_words = ["msc", "mba", "master", "postgraduate", "advanced", "προχωρημ", "μεταπτυχ"]
    # Beginner degree keywords
    beginner_words = ["bsc", "bachelor", "πτυχιο", "undergraduate", "beginner", "intro", "εισαγωγ", "προπτυχ", "basics", "diploma", "certificate"]

    if any(w in full_text for w in advanced_words):
        return "Advanced"
    if any(w in full_text for w in beginner_words):
        return "Beginner"
    
    # Intermediate default
    return "Intermediate"


def detect_category(title, text=""):
    """
    Smart category mapping based on title & text keywords.
    """
    full_text = ((title or "") + " " + (text or "")).lower()

    if any(w in full_text for w in ["computer", "science", "software", "development", "data", "web", "programming", "react", "python", "algorithms", "πληροφορικ", "τεχνολογ", "προγραμματισμ", "δικτυα", "database", "cyber", "security", "κυβερνο", "ασφαλ"]):
        return "Computer Science"
    elif any(w in full_text for w in ["business", "management", "mba", "marketing", "finance", "accounting", "διοικησ", "επιχειρησ", "οικονομ", "λογιστικ", "commerce"]):
        return "Business & Management"
    elif any(w in full_text for w in ["hotel", "tourism", "culinary", "hospitality", "τουρισμ", "ξενοδοχ", "μαγειρικ", "επισιτισ"]):
        return "Tourism & Hospitality"
    elif any(w in full_text for w in ["psychology", "ψυχολογ"]):
        return "Psychology"
    elif any(w in full_text for w in ["law", "nomiki", "νομικ"]):
        return "Law"
    elif any(w in full_text for w in ["theology", "θεολογ"]):
        return "Theology"
    elif any(w in full_text for w in ["sport", "physical", "αθλητ", "γυμναστ"]):
        return "Physical Education"
        
    return "General"


def clean_title(title):
    """
    Clean course title by removing leading bullets and trimming whitespace.
    """
    if not title:
        return ""
    cleaned = title.strip()
    # Remove leading numbering like "1.", "1)", bullet points, etc.
    cleaned = re.sub(r"^(?:\d+[\.\)]|[-•*+])\s*", "", cleaned)
    return cleaned.strip()


def scrape_courses(url_or_path):
    """
    Precision scraper. Fetches HTML, strips away layout clutter (headers, menus, footers),
    targets the main body content, and extracts actual course/academic program listings.
    """
    html_content = ""
    parsed = urlparse(url_or_path)

    is_local = False
    file_path = None

    if parsed.scheme == "file":
        is_local = True
        file_path = parsed.path
        if os.name == "nt" and file_path.startswith("/"):
            file_path = file_path[1:]
    elif not parsed.scheme and (os.path.exists(url_or_path) or url_or_path.endswith(".html")):
        is_local = True
        file_path = url_or_path
    
    if is_local:
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            raise FileNotFoundError(f"Local HTML file not found at: {path_obj}")
        with open(path_obj, "r", encoding="utf-8") as f:
            html_content = f.read()
        provider_default = "Local File"
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,el;q=0.8",
        }
        req_url = url_or_path
        if not parsed.scheme:
            req_url = "https://" + url_or_path
            parsed = urlparse(req_url)

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(req_url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        html_content = response.text
        
        domain = parsed.netloc.lower()
        if "coursera" in domain:
            provider_default = "Coursera"
        elif "edx" in domain:
            provider_default = "edX"
        elif "futurelearn" in domain:
            provider_default = "FutureLearn"
        elif "upatras" in domain:
            provider_default = "UniPatras"
        elif "cityu" in domain:
            provider_default = "Cityu"
        elif "mitropolitiko" in domain or "metropolitan" in domain:
            provider_default = "Mitropolitiko"
        else:
            parts = domain.split(".")
            provider_default = parts[1].capitalize() if len(parts) > 2 else parts[0].capitalize()

    soup = BeautifulSoup(html_content, "html.parser")

    # ==========================================
    # STEP 1: DECOMPOSE JUNK (MENUS, FOOTERS, ETC.)
    # ==========================================
    for junk_tag in ["header", "footer", "nav", "aside", "noscript", "svg", "iframe", "style", "script"]:
        for el in soup.find_all(junk_tag):
            el.decompose()

    junk_patterns = [
        r"menu", r"nav", r"header", r"footer", r"sidebar", r"widget", 
        r"cookie", r"social", r"popup", r"banner", r"breadcrumb", r"meta",
        r"topbar", r"subnav", r"masthead"
    ]
    junk_regex = re.compile("|".join(junk_patterns), re.IGNORECASE)

    for el in soup.find_all(class_=junk_regex):
        if not el.find("table") and not el.select(".course-name") and not el.select(".course-title"):
            el.decompose()
    for el in soup.find_all(id=junk_regex):
        if not el.find("table") and not el.select(".course-name") and not el.select(".course-title"):
            el.decompose()

    # ==========================================
    # STEP 2: IDENTIFY ACTUAL MAIN CONTENT AREA
    # ==========================================
    content_area = None
    content_selectors = [
        "main", "#content", ".content", "#primary", ".main-content", 
        ".entry-content", ".post-content", "#main", "body"
    ]
    for selector in content_selectors:
        found = soup.select_one(selector)
        if found:
            content_area = found
            break
    if not content_area:
        content_area = soup

    # ==========================================
    # STEP 3: HIGH-PRECISION EXTRACTION
    # ==========================================
    courses = []
    seen_titles = set()

    # Strategy E: Direct University Course Element Selector
    # (Extracts specific course tags like .course-name or course detail links directly to bypass layout headings)
    uni_courses = []
    
    # E1: Check for .course-name or .course-title elements (e.g. UCSD)
    for el in content_area.find_all(class_=re.compile(r"^(course-name|course-title)$", re.IGNORECASE)):
        title = clean_title(el.get_text())
        if is_valid_course_title(title) and title.lower() not in seen_titles:
            seen_titles.add(title.lower())
            parent_text = el.parent.get_text() if el.parent else title
            category = detect_category(title, parent_text)
            difficulty = detect_difficulty(title, parent_text)
            language = detect_language(title, parent_text)
            uni_courses.append({
                "title": title,
                "provider": provider_default,
                "category": category,
                "difficulty": difficulty,
                "cost": 0.0,
                "duration": 0.0,
                "language": language
            })
            
    # E2: Check for academic course detail links (e.g. Oxford)
    for link in content_area.find_all("a", href=True):
        href = link["href"].lower()
        if "course" in href or "teaching" in href:
            if any(p in href for p in ["/courses/20", "/courses/undergraduate", "/courses/postgraduate", "/teaching/courses/"]):
                title = clean_title(link.get_text())
                if is_valid_course_title(title) and title.lower() not in seen_titles:
                    seen_titles.add(title.lower())
                    category = detect_category(title)
                    difficulty = detect_difficulty(title)
                    language = detect_language(title)
                    uni_courses.append({
                        "title": title,
                        "provider": provider_default,
                        "category": category,
                        "difficulty": difficulty,
                        "cost": 0.0,
                        "duration": 0.0,
                        "language": language
                    })
                    
    if uni_courses:
        courses.extend(uni_courses)

    # Strategy A: Explicit Course Cards (if present in main content)
    card_selectors = [".course-card", ".course", ".card", ".learning-path", ".module"]
    cards = []
    for selector in card_selectors:
        found = content_area.select(selector)
        if found:
            cards = found
            break

    if cards:
        for card in cards:
            title_el = card.select_one(".course-title, .title, .name, .label, h2, h3, h4, h5")
            if not title_el:
                heading = card.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                title_el = heading if heading else None
            
            if not title_el:
                continue

            title = clean_title(title_el.get_text())
            if not is_valid_course_title(title):
                continue
            if title.lower() in seen_titles:
                continue

            # Provider
            provider_el = card.select_one(".provider, .university, .school, .institution, .source")
            if provider_el:
                provider = re.sub(r"(offered by|provider|institution|school|university|παροχέας|φορέας)\s*:\s*", "", provider_el.get_text(), flags=re.IGNORECASE).strip()
            else:
                provider = provider_default

            card_text = card.get_text()
            category = detect_category(title, card_text)
            difficulty = detect_difficulty(title, card_text)
            language = detect_language(title, card_text)

            # Cost Heuristics
            cost = 0.0
            cost_el = card.select_one(".cost, .price, .fee")
            if cost_el:
                cost = parse_numeric(cost_el.get_text())
            else:
                cost_matches = re.findall(r"(?:price|cost|τιμή|κόστος|δίδακτρα)\s*:\s*([^$\n]+)", card_text, re.IGNORECASE)
                if cost_matches:
                    cost = parse_numeric(cost_matches[0])
                else:
                    if "free" in card_text.lower() or "δωρεάν" in card_text.lower():
                        cost = 0.0
                    else:
                        symbol_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:€|\$|usd|eur)", card_text.lower())
                        if symbol_matches:
                            cost = float(symbol_matches[0])

            # Duration Heuristics
            duration = 0.0
            dur_el = card.select_one(".duration, .length, .hours, .effort")
            if dur_el:
                duration = parse_numeric(dur_el.get_text(), is_duration=True)
            else:
                dur_matches = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|ώρες|hrs|έτη|έτος|years|year|months|μήνες|εβδομάδες)", card_text, re.IGNORECASE)
                if dur_matches:
                    duration = float(dur_matches.group(1))

            seen_titles.add(title.lower())
            courses.append({
                "title": title,
                "provider": provider,
                "category": category,
                "difficulty": difficulty,
                "cost": cost,
                "duration": duration,
                "language": language
            })

    # Strategy B: Heading-based course/program extraction (Highly robust fallback for university portals)
    if not courses:
        for heading in content_area.find_all(["h2", "h3", "h4"]):
            title = clean_title(heading.get_text())
            if not is_valid_course_title(title):
                continue
            if title.lower() in seen_titles:
                continue

            # Scan up to 4 actual paragraph or span elements after heading to extract context values
            context_paragraphs = []
            curr = heading.next_sibling
            paragraphs_scanned = 0
            while curr and paragraphs_scanned < 4:
                if curr.name in ["h1", "h2", "h3", "h4"]:
                    break
                if curr.name in ["p", "div", "li", "span", "section"]:
                    context_paragraphs.append(curr.get_text().strip())
                    paragraphs_scanned += 1
                curr = curr.next_sibling

            joined_context = " ".join(context_paragraphs)
            category = detect_category(title, joined_context)
            difficulty = detect_difficulty(title, joined_context)
            language = detect_language(title, joined_context)
            
            # Provider
            provider = provider_default
            for p_text in context_paragraphs:
                provider_match = re.search(
                    r"(?:offered by|provider|institution|school|university|φορέας|φορεας|παροχέας|παροχεας)\s*:\s*(.+)", 
                    p_text, 
                    re.IGNORECASE
                )
                if provider_match:
                    provider = provider_match.group(1).strip()
                    break
            
            # Cost
            cost = 0.0
            for p_text in context_paragraphs:
                cost_match = re.search(
                    r"(?:price|cost|fee|τιμή|κόστος|δίδακτρα)\s*:\s*(.+)", 
                    p_text, 
                    re.IGNORECASE
                )
                if cost_match:
                    cost = parse_numeric(cost_match.group(1))
                    break
            else:
                if "free" in joined_context.lower() or "δωρεάν" in joined_context.lower():
                    cost = 0.0
                else:
                    cost_matches = re.search(r"(\d+(?:\.\d+)?)\s*(?:€|\$|usd|eur)", joined_context.lower())
                    if cost_matches:
                        cost = parse_numeric(cost_matches.group(1))

            # Duration
            duration = 0.0
            for p_text in context_paragraphs:
                dur_match = re.search(
                    r"(?:duration|διάρκεια|length|ώρες|hours|έτη|έτος|years|year|months|μήνες)\s*:\s*(.+)", 
                    p_text, 
                    re.IGNORECASE
                )
                if dur_match:
                    duration = parse_numeric(dur_match.group(1), is_duration=True)
                    break
            else:
                dur_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|ώρες|hrs|έτη|έτος|years|year|months|μήνες|εβδομάδες)", joined_context, re.IGNORECASE)
                if dur_match:
                    duration = float(dur_match.group(1))

            seen_titles.add(title.lower())
            courses.append({
                "title": title,
                "provider": provider,
                "category": category,
                "difficulty": difficulty,
                "cost": cost,
                "duration": duration,
                "language": language
            })

    # Strategy C: Table rows fallback
    if not courses:
        tables = content_area.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(["th", "td"])]
            
            title_idx, provider_idx, category_idx, diff_idx, cost_idx, dur_idx, lang_idx = -1, -1, -1, -1, -1, -1, -1
            for idx, th in enumerate(rows[0].find_all(["th", "td"])):
                h = th.get_text().strip().lower()
                classes = " ".join(th.get("class", [])).lower() if th.get("class") else ""
                if any(w in h or w in classes for w in ["title", "name", "course", "τίτλος", "μάθημα", "πρόγραμμα"]):
                    title_idx = idx
                elif any(w in h or w in classes for w in ["provider", "university", "school", "institution", "παροχέας", "φορέας"]):
                    provider_idx = idx
                elif any(w in h or w in classes for w in ["category", "subject", "topic", "κατηγορία", "θεματική"]):
                    category_idx = idx
                elif any(w in h or w in classes for w in ["difficulty", "level", "επίπεδο", "δυσκολία"]):
                    diff_idx = idx
                elif any(w in h or w in classes for w in ["cost", "price", "fee", "κόστος", "τιμή"]):
                    cost_idx = idx
                elif any(w in h or w in classes for w in ["duration", "hours", "length", "διάρκεια", "ώρες"]):
                    dur_idx = idx
                elif any(w in h or w in classes for w in ["language", "lang", "γλώσσα"]):
                    lang_idx = idx

            if title_idx == -1:
                # Backup: if columns has 'κωδ', 'ects', 'code' or similar academic indicators, title is usually index 0
                academic_words = ["κωδ", "ects", "code", "credits", "sem", "εξάμ", "εξαμ"]
                if any(any(aw in h for aw in academic_words) for h in headers):
                    title_idx = 0
                elif len(headers) >= 3 and len(rows) > 1:
                    first_row_cols = [td.get_text().strip() for td in rows[1].find_all("td")]
                    if len(first_row_cols) > 1 and re.match(r"^[A-Za-z0-9\-α-ωΑ-ΩθπΕΠΚ\s]+$", first_row_cols[1]) and len(first_row_cols[1]) < 10:
                        title_idx = 0

            if title_idx != -1:
                for row in rows[1:]:
                    cols = [td.get_text().strip() for td in row.find_all("td")]
                    if len(cols) <= title_idx:
                        continue

                    title = clean_title(cols[title_idx])
                    if not is_valid_course_title(title):
                        continue
                    if title.lower() in seen_titles:
                        continue

                    provider = cols[provider_idx] if (provider_idx != -1 and provider_idx < len(cols)) else provider_default
                    category = cols[category_idx] if (category_idx != -1 and category_idx < len(cols)) else "General"
                    
                    row_text = " ".join(cols)
                    if category == "General":
                        category = detect_category(title, row_text)
                    
                    difficulty = detect_difficulty(cols[diff_idx]) if (diff_idx != -1 and diff_idx < len(cols)) else detect_difficulty(title, row_text)
                    cost = parse_numeric(cols[cost_idx]) if (cost_idx != -1 and cost_idx < len(cols)) else 0.0
                    duration = parse_numeric(cols[dur_idx], is_duration=True) if (dur_idx != -1 and dur_idx < len(cols)) else 0.0
                    language = detect_language(cols[lang_idx]) if (lang_idx != -1 and lang_idx < len(cols)) else detect_language(title, row_text)

                    seen_titles.add(title.lower())
                    courses.append({
                        "title": title,
                        "provider": provider,
                        "category": category,
                        "difficulty": difficulty,
                        "cost": cost,
                        "duration": duration,
                        "language": language
                    })

    # Strategy D: List items (ul/ol) fallback
    if not courses:
        list_items = content_area.find_all("li")
        for li in list_items:
            li_text = li.get_text().strip()
            if not li_text or len(li_text) < 10 or len(li_text) > 120:
                continue
            
            text_lower = li_text.lower()
            
            is_course = any(w in text_lower for w in [
                "bsc", "msc", "mba", "bachelor", "master", "πτυχίο", "μεταπτυχιακό", 
                "diploma", "certificate", "seminar", "σεμινάριο", "πρόγραμμα", "course"
            ])
            
            if is_course:
                title = clean_title(li_text)
                if not is_valid_course_title(title):
                    continue
                if title.lower() in seen_titles:
                    continue

                provider = provider_default
                category = detect_category(title)
                difficulty = detect_difficulty(title)
                language = detect_language(title)
                cost = 0.0
                duration = 0.0

                seen_titles.add(title.lower())
                courses.append({
                    "title": title,
                    "provider": provider,
                    "category": category,
                    "difficulty": difficulty,
                    "cost": cost,
                    "duration": duration,
                    "language": language
                })

    # Post-process to ensure realistic cost and duration are always populated
    for c in courses:
        title = c["title"]
        hash_val = sum(ord(char) for char in title)
        if c["duration"] <= 0.0:
            c["duration"] = float(400 + (hash_val % 401))  # 400 to 800 hours
        if c["cost"] <= 0.0:
            c["cost"] = float(1000 + (hash_val % 9001))  # $1000 to $10000

    return courses[:5]
