### app.py
from flask import Flask, request, render_template, redirect, url_for, session, flash
from logic import iching
from openai import OpenAI
from dotenv import load_dotenv
import os, sqlite3
from llm.memory import search
import pdb
import markdown
import re

# Import our new models
from models.user import User
from models.history import History

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

# Set your OpenAI API key here or use an environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

DB_FILE = "data/users.db"

# Hexagram utility functions
def get_all_hexagrams():
    """Get all 64 hexagrams with their basic info"""
    hexagrams = []
    for i in range(1, 65):
        hex_obj = iching.get_hexagram_section(i)
        if hex_obj:
            hexagrams.append({
                'number': hex_obj.Number,
                'title': hex_obj.Title,
                'symbol': hex_obj.Symbol,
                'url_name': create_hexagram_url_name(hex_obj.Title),
                'description': hex_obj.About.Description[:100] + '...' if len(hex_obj.About.Description) > 100 else hex_obj.About.Description
            })
    return hexagrams

def create_hexagram_url_name(title):
    """Create URL-friendly name from hexagram title"""
    # Remove Chinese characters and extract English name
    # Pattern: "Ch'ien / The Creative" -> "the_creative"
    # Pattern: "Kuan / Contemplation (View)" -> "contemplation"

    # Split by / and take the second part (English name)
    parts = title.split('/')
    if len(parts) > 1:
        english_name = parts[1].strip()
    else:
        english_name = parts[0].strip()

    # Remove parenthetical sections
    english_name = re.sub(r'\([^)]*\)', '', english_name).strip()

    # Convert to lowercase, replace spaces with underscores
    url_name = english_name.lower().replace(' ', '_')

    # Remove any remaining special characters except underscores
    url_name = re.sub(r'[^a-z0-9_]', '', url_name)

    return url_name

def parse_hexagram_url(url_path):
    """Parse hexagram URL and return number and canonical URL name"""
    # URL format: "20-contemplation" or "20-this_%38_rAnD0m"
    parts = url_path.split('-', 1)
    if len(parts) != 2:
        return None, None

    try:
        number = int(parts[0])
        if number < 1 or number > 64:
            return None, None

        # Get the canonical URL name
        hex_obj = iching.get_hexagram_section(number)
        if hex_obj:
            canonical_name = create_hexagram_url_name(hex_obj.Title)
            return number, canonical_name

        return None, None
    except ValueError:
        return None, None

def get_trigram_info():
    """Get information about the 8 trigrams"""
    trigrams = [
        {
            'id': 'heaven',
            'name': 'Heaven',
            'chinese': 'Ch\'ien',
            'symbol': '☰',
            'lines': '≡',
            'attributes': ['Creative', 'Strong', 'Active', 'Light-giving'],
            'description': 'The Creative principle, representing pure yang energy, strength, and the power of heaven.'
        },
        {
            'id': 'earth',
            'name': 'Earth',
            'chinese': 'K\'un',
            'symbol': '☷',
            'lines': '☷',
            'attributes': ['Receptive', 'Yielding', 'Nurturing', 'Devoted'],
            'description': 'The Receptive principle, representing pure yin energy, yielding strength, and the power of earth.'
        },
        {
            'id': 'thunder',
            'name': 'Thunder',
            'chinese': 'Chen',
            'symbol': '☳',
            'lines': '☳',
            'attributes': ['Arousing', 'Movement', 'Initiative', 'Eldest Son'],
            'description': 'The Arousing, representing movement, initiative, and the power of thunder and lightning.'
        },
        {
            'id': 'water',
            'name': 'Water',
            'chinese': 'K\'an',
            'symbol': '☵',
            'lines': '☵',
            'attributes': ['Abysmal', 'Dangerous', 'Flowing', 'Middle Son'],
            'description': 'The Abysmal, representing danger, flowing water, and the power of the deep.'
        },
        {
            'id': 'mountain',
            'name': 'Mountain',
            'chinese': 'Ken',
            'symbol': '☶',
            'lines': '☶',
            'attributes': ['Keeping Still', 'Meditation', 'Youngest Son', 'Stillness'],
            'description': 'Keeping Still, representing meditation, stillness, and the immovable power of mountains.'
        },
        {
            'id': 'wind',
            'name': 'Wind',
            'chinese': 'Sun',
            'symbol': '☴',
            'lines': '☴',
            'attributes': ['Gentle', 'Penetrating', 'Eldest Daughter', 'Wood'],
            'description': 'The Gentle, representing penetration, flexibility, and the power of wind and wood.'
        },
        {
            'id': 'fire',
            'name': 'Fire',
            'chinese': 'Li',
            'symbol': '☲',
            'lines': '☲',
            'attributes': ['Clinging', 'Light', 'Middle Daughter', 'Brightness'],
            'description': 'The Clinging, representing light, beauty, and the illuminating power of fire.'
        },
        {
            'id': 'lake',
            'name': 'Lake',
            'chinese': 'Tui',
            'symbol': '☱',
            'lines': '☱',
            'attributes': ['Joyous', 'Youngest Daughter', 'Pleasure', 'Marsh'],
            'description': 'The Joyous, representing joy, pleasure, and the reflective power of lakes and marshes.'
        }
    ]
    return trigrams

def enhance_reading_with_links(reading_text):
    """Enhance reading text by adding links to hexagrams"""
    if not reading_text:
        return reading_text

    # Pattern to match hexagram references like "Hexagram 20" or "20: Kuan"
    def replace_hexagram_ref(match):
        number = int(match.group(1))
        if 1 <= number <= 64:
            hex_obj = iching.get_hexagram_section(number)
            if hex_obj:
                url_name = create_hexagram_url_name(hex_obj.Title)
                return f'<a href="{url_for("hexagram_detail", number=number, name=url_name)}" class="hexagram-link">{hex_obj.Number}: {hex_obj.Title}</a>'
        return match.group(0)

    # Replace patterns like "Hexagram 20", "hexagram 20", "20: Title"
    enhanced = re.sub(r'[Hh]exagram (\d+)', replace_hexagram_ref, reading_text)
    enhanced = re.sub(r'(\d+):\s*[A-Za-z\']+', replace_hexagram_ref, enhanced)

    return enhanced

def sanitize_css_selector(text):
    """Convert trigram text to a valid CSS selector ID that matches the trigram list"""
    if not text:
        return ""

        # Mapping from hexagram trigram descriptions to trigram IDs
    trigram_mapping = {
        "ch'ien": "heaven",
        "chien": "heaven",
        "k'un": "earth",
        "kun": "earth",
        "chen": "thunder",
        "k'an": "water",
        "kan": "water",
        "ken": "mountain",
        "kên": "mountain",  # Handle accent
        "sun": "wind",
        "li": "fire",
        "tui": "lake"
    }

    # Extract the first word and clean it
    first_word = text.split()[0].lower()
    # Remove apostrophes and special characters
    clean_word = re.sub(r"[^a-z0-9]", "", first_word)

    # Check if it maps to a known trigram
    if clean_word in trigram_mapping:
        return trigram_mapping[clean_word]

    # If we find "heaven", "earth", etc. in the text, use those directly
    text_lower = text.lower()
    for keyword in ["heaven", "earth", "thunder", "water", "mountain", "wind", "fire", "lake"]:
        if keyword in text_lower:
            return keyword

    # Fallback: return the cleaned first word
    return clean_word

# Add the filter to Jinja2
app.jinja_env.filters['sanitize_css_selector'] = sanitize_css_selector

# Add markdown filter
import markdown
def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ""
    return markdown.markdown(text)

app.jinja_env.filters['markdown'] = markdown_filter

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    birthdate TEXT,
                    about_me TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    username TEXT,
                    question TEXT,
                    hexagram TEXT,
                    reading TEXT,
                    reading_dt TEXT,
                    reading_id TEXT
                 )''')

    # Add new columns to existing users table if they don't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN birthdate TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE users ADD COLUMN about_me TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE history ADD COLUMN reading_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()

init_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.authenticate(username, password)
        if user:
            session["username"] = user.username
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.", "error")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        user = User.create(username, password)
        if user:
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already exists.", "error")
            return render_template("register.html")
    return render_template("register.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        birthdate = request.form["birthdate"]
        about_me = request.form["about_me"]
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        # Handle password change
        if current_password and new_password:
            if new_password != confirm_new_password:
                flash("New passwords do not match.", "error")
                return render_template("profile.html",
                                     username=user.username,
                                     user_birthdate=user.birthdate,
                                     user_about_me=user.about_me)

            if not user.change_password(current_password, new_password):
                flash("Current password is incorrect.", "error")
                return render_template("profile.html",
                                     username=user.username,
                                     user_birthdate=user.birthdate,
                                     user_about_me=user.about_me)

        if user.update_profile(birthdate=birthdate, about_me=about_me):
            flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Failed to update profile.", "error")

    return render_template("profile.html",
                         username=user.username,
                         user_birthdate=user.birthdate,
                         user_about_me=user.about_me)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# Hexagram navigation routes
@app.route("/hexagrams")
def hexagrams_list():
    hexagrams = get_all_hexagrams()
    return render_template("hexagrams_list.html", hexagrams=hexagrams)

@app.route("/hexagram/<int:number>-<name>")
def hexagram_detail(number, name):
    # Validate and get canonical name
    parsed_number, canonical_name = parse_hexagram_url(f"{number}-{name}")

    if not parsed_number:
        flash("Hexagram not found.", "error")
        return redirect(url_for("hexagrams_list"))

    # Redirect to canonical URL if name doesn't match
    if name.lower() != canonical_name.lower():
        return redirect(url_for("hexagram_detail", number=parsed_number, name=canonical_name))

    # Get hexagram data
    hex_obj = iching.get_hexagram_section(number)
    if not hex_obj:
        flash("Hexagram not found.", "error")
        return redirect(url_for("hexagrams_list"))

    # Get return_to parameter for trigram links
    return_to = request.args.get('return_to', url_for('hexagrams_list'))

    return render_template("hexagram_detail.html",
                         hexagram=hex_obj,
                         return_to=return_to)

@app.route("/trigrams")
def trigrams_list():
    trigrams = get_trigram_info()
    return_to = request.args.get('return_to', url_for('hexagrams_list'))

    return render_template("trigrams_list.html",
                         trigrams=trigrams,
                         return_to=return_to)

@app.route("/reading/<reading_path>")
def reading_detail(reading_path):
    """Display detailed view of a specific reading"""
    from models.history import History

    # Get the reading entry
    reading_entry = History.get_reading_by_path(reading_path)
    if not reading_entry:
        flash("Reading not found.", "error")
        return redirect(url_for("index"))

    # Check if user has permission to view this reading (must be the owner or logged in as the same user)
    if "username" not in session or session["username"] != reading_entry.username:
        flash("You don't have permission to view this reading.", "error")
        return redirect(url_for("login"))

    return render_template("reading_detail.html",
                         reading_entry=reading_entry,
                         enhanced_reading=reading_entry.get_enhanced_reading_html())

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    # Get user object (history is lazy-loaded via property)
    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("login"))

    reading = None
    recent_history = []

    if request.method == "POST":
        question = request.form["question"]
        hexagram_reading = iching.cast_hexagrams()  # This returns a Reading object

        # Get vector database content
        vector_results = search(str(hexagram_reading))
        vector_context = "\n\n".join([str(result['metadata']) for result in vector_results])

        print(vector_context)
        s = ''
        future = 'Your current casting does not have a transition.'
        if hexagram_reading.has_transition():
            s = 's'
            secondary_text = iching.get_hgram_text(hexagram_reading.Future)
            future = f'''
            The hexagram had transitional form{s}. The hexagram for the future is {secondary_text}
            '''

        hex_text = iching.get_hgram_text(hexagram_reading.Current)

        # Get history text for AI prompt using the lazy-loaded history property
        history_text = user.history.get_history_text_for_prompt(limit=3)

        prompt = f"""
        You are a wise I Ching diviner with access to comprehensive knowledge.

        The user has asked: "{question}"
        The newly cast hexagram is {hexagram_reading}.

        Traditional hexagram text:
        {hex_text}

        Relevant knowledge from the I Ching corpus:
        {vector_context}

        {future}

        {history_text}

        Based on all this information, provide a deep, insightful reading that connects the traditional wisdom with the user's specific question. When mentioning hexagrams, use the format "Hexagram [number]" or "[number]: [Title]" so they can be properly linked.
        """
        app.logger.info(prompt)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a mystical I Ching oracle with deep knowledge of the classic text and its interpretations."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
            temperature=0.8,        # Slightly creative for mystical feel
            frequency_penalty=0.2,  # Reduce repetition
            presence_penalty=0.1,   # Encourage diverse topics
        )

        reading = response.choices[0].message.content

        # Save to history using the lazy-loaded history property
        # Now we can pass the Reading object directly
        user.history.add_reading(question, hexagram_reading, reading)

    # Get recent history for display using the lazy-loaded history property
    recent_history = user.history.get_formatted_recent(limit=3, render_markdown=True, enhance_links=True)

    # Enhance reading with hexagram links
    if reading:
        reading_html = markdown.markdown(reading)
        reading_html = enhance_reading_with_links(reading_html)
    else:
        reading_html = None

    return render_template("index.html",
                         history=recent_history,
                         reading=reading_html,
                         user_birthdate=user.birthdate,
                         user_about_me=user.about_me,
                         username=user.username)

if __name__ == "__main__":
    app.run(debug=True)
