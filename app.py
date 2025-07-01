### app.py
from flask import Flask, request, render_template, redirect, url_for, session, flash
from logic import iching
from logic import divination  # Initialize the new divination system
from logic.base import DivinationType
from logic.iching_adapter import create_iching_reading_from_legacy, get_legacy_reading_from_iching
from logic.ai_readers import generate_iching_reading, generate_runic_reading
from dotenv import load_dotenv
import os, sqlite3
import pdb
import markdown
import re

# Import our new models
from models.user import User
from models.history import History

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")



# Context processor to make hexagram symbols and utility functions available to all templates
@app.context_processor
def inject_hexagram_symbols():
    return {
        'hexagram_symbols': get_hexagram_symbols(),
        'create_hexagram_url_name': create_hexagram_url_name
    }

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

def get_hexagram_symbols():
    """Get mapping of hexagram numbers to their Unicode symbols"""
    symbols = {}
    for i in range(1, 65):
        hex_obj = iching.get_hexagram_section(i)
        if hex_obj and hex_obj.Symbol:
            symbols[i] = hex_obj.Symbol
    return symbols

def get_trigram_info():
    """Get information about the 8 trigrams"""
    trigrams = [
        {
            'id': 'heaven',
            'name': 'Heaven',
            'chinese': '干 | qián',
            'symbol': '☰',
            'lines': '≡',
            'attributes': ['Creative', 'Strong', 'Active', 'Light-giving', 'Warming', 'Summer'],
            'description': 'The Creative principle, representing pure yang energy, strength, and the power of heaven. '
                + 'It embodies the primal creative force of the universe, the father archetype, and divine '
                + 'inspiration. One of the three powers of Taoist cosmology. Associated with leadership, '
                + 'authority, and the drive to achieve. In the body, it governs the head and lungs. Its season '
                + 'is late autumn/early winter, direction is northwest, and it represents the time from 9-11 PM. '
                + 'This trigram speaks of perseverance, determination, and the courage to initiate new ventures. '
                + 'When prominent in a reading, it suggests taking charge, being proactive, and trusting in '
                + 'your natural leadership abilities.'
        },
        {
            'id': 'earth',
            'name': 'Earth',
            'chinese': '坤 | kūn',
            'symbol': '☷',
            'lines': '☷',
            'attributes': ['Receptive', 'Yielding', 'Nurturing', 'Devoted', 'Resting', 'Winter'],
            'description': 'The Receptive principle, representing pure yin energy, yielding strength, and the '
               + 'power of earth. It embodies the nurturing mother archetype, unconditional support, and the '
               + 'fertile ground from which all life springs. One of the three powers of Taoist cosmology. '
               + 'Associated with patience, devotion, and the wisdom of knowing when to yield. In the body, '
               + 'it governs the belly and reproductive organs. Its season is late summer, direction is '
               + 'southwest, and it represents the time from 1-3 PM. This trigram teaches the power of '
               + 'receptivity, the strength found in gentleness, and the importance of providing stable '
               + 'foundations. When prominent in a reading, it suggests embracing supportive roles, '
               + 'practicing patience, and trusting in the natural flow of events.'
        },
        {
            'id': 'thunder',
            'name': 'Thunder',
            'chinese': '震 | zhèn',
            'symbol': '☳',
            'lines': '☳',
            'attributes': ['Arousing', 'Movement', 'Initiative', 'Eldest Son', 'Storming', 'Winter'],
            'description': 'The Arousing, representing movement, initiative, and the power of thunder and '
                + 'lightning. It embodies sudden awakening, decisive action, and the explosive energy that '
                + 'breaks through stagnation. As the eldest son, it carries the pioneering spirit and the '
                + 'courage to forge new paths. In the body, it governs the feet and liver. Its season is '
                + 'spring, direction is east, and it represents the time from 5-7 AM. This trigram speaks '
                + 'of breakthrough moments, the power of righteous action, and the energy needed to '
                + 'overcome obstacles. When prominent in a reading, it suggests bold moves, embracing '
                + 'change, and acting on sudden inspirations with confidence.'
        },
        {
            'id': 'water',
            'name': 'Water',
            'chinese': '坎 | kǎn',
            'symbol': '☵',
            'lines': '☵',
            'attributes': ['Abysmal', 'Dangerous', 'Flowing', 'Middle Son', 'Pooling', 'Autumn'],
            'description': 'The Abysmal, representing danger, flowing water, and the power of the deep. '
                + 'It embodies the middle son\'s role as mediator, the wisdom gained through hardship, and '
                + 'the persistence of water that eventually wears down stone. One of the three powers of '
                + 'Taoist cosmology. Associated with intuition, adaptability, and the courage to navigate '
                + 'difficult situations. In the body, it governs the kidneys and ears. Its season is winter, '
                + 'direction is north, and it represents the time from 11 PM-1 AM. This trigram teaches '
                + 'about resilience in adversity, the power of consistency, and finding opportunity within '
                + 'challenge. When prominent in a reading, it suggests careful navigation of difficulties, '
                + 'trusting your intuition, and maintaining steady progress despite obstacles.'
        },
        {
            'id': 'mountain',
            'name': 'Mountain',
            'chinese': '艮 | gèn',
            'symbol': '☶',
            'lines': '☶',
            'attributes': ['Keeping Still', 'Meditation', 'Youngest Son', 'Stillness', 'Jutting', 'Autumn'],
            'description': 'Keeping Still, representing meditation, stillness, and the immovable power of '
                + 'mountains. It embodies the youngest son\'s wisdom of knowing when to stop, the power of '
                + 'contemplation, and the strength found in inner peace. Associated with boundaries, '
                + 'self-reflection, and the ability to remain centered amidst chaos. In the body, it governs '
                + 'the hands and stomach. Its season is late winter/early spring, direction is northeast, '
                + 'and it represents the time from 3-5 AM. This trigram teaches the value of restraint, '
                + 'the importance of timing, and the profound wisdom that comes from stillness. When '
                + 'prominent in a reading, it suggests taking time for reflection, establishing healthy '
                + 'boundaries, and finding strength through inner stability.'
        },
        {
            'id': 'wind',
            'name': 'Wind',
            'chinese': '巽 | xùn',
            'symbol': '☴',
            'lines': '☴',
            'attributes': ['Gentle', 'Penetrating', 'Eldest Daughter', 'Wood', 'Dispersing', 'Summer'],
            'description': 'The Gentle, representing penetration, flexibility, and the power of wind and wood. '
                + 'It embodies the eldest daughter\'s role as gentle leader, the persistence that eventually '
                + 'penetrates all obstacles, and the wisdom of adapting to circumstances. Associated with '
                + 'influence, communication, and the ability to work with others harmoniously. In the body, '
                + 'it governs the thighs and gallbladder. Its season is late spring/early summer, direction '
                + 'is southeast, and it represents the time from 7-9 AM. This trigram teaches about subtle '
                + 'influence, the power of consistency, and achieving goals through gentle persistence rather '
                + 'than force. When prominent in a reading, it suggests working with others, using gentle '
                + 'persuasion, and allowing your influence to grow naturally over time.'
        },
        {
            'id': 'fire',
            'name': 'Fire',
            'chinese': '离 | lí',
            'symbol': '☲',
            'lines': '☲',
            'attributes': ['Clinging', 'Light', 'Middle Daughter', 'Brightness', 'Dancing', 'Spring'],
            'description': 'The Clinging, representing light, beauty, and the illuminating power of fire. '
                + 'It embodies the middle daughter\'s role as illuminator, the power of clarity and insight, '
                + 'and the warm energy that brings people together. Associated with intelligence, creativity, '
                + 'and the ability to see truth clearly. In the body, it governs the eyes and heart. Its '
                + 'season is summer, direction is south, and it represents the time from 11 AM-1 PM. This '
                + 'trigram teaches about clarity of vision, the importance of maintaining inner light, and '
                + 'the power of truth to transform situations. When prominent in a reading, it suggests '
                + 'seeking clarity, embracing your creative gifts, and allowing your inner light to guide '
                + 'both yourself and others.'
        },
        {
            'id': 'lake',
            'name': 'Lake',
            'chinese': '兑 | duì',
            'symbol': '☱',
            'lines': '☱',
            'attributes': ['Joyous', 'Youngest Daughter', 'Pleasure', 'Marsh', 'Engulfing', 'Spring'],
            'description': 'The Joyous, representing joy, pleasure, and the reflective power of lakes and '
                + 'marshes. It embodies the youngest daughter\'s gift of bringing happiness, the power of '
                + 'authentic expression, and the wisdom found in celebration. Associated with communication, '
                + 'social harmony, and the ability to find joy even in simple moments. In the body, it '
                + 'governs the mouth and lungs. Its season is autumn, direction is west, and it represents '
                + 'the time from 5-7 PM. This trigram teaches about the importance of joy, the power of '
                + 'words to heal or harm, and the value of maintaining an open, receptive heart. When '
                + 'prominent in a reading, it suggests embracing joy, expressing yourself authentically, '
                + 'and creating harmony through positive communication.'
        }
    ]
    return trigrams

def enhance_reading_with_links(reading_text):
    """Enhance reading text by adding links to hexagrams and styling transitions"""
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
                    reading_id TEXT,
                    divination_type TEXT DEFAULT 'iching'
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

    try:
        c.execute("ALTER TABLE history ADD COLUMN divination_type TEXT DEFAULT 'iching'")
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

@app.route("/runes")
def runes_list():
    """Display all Elder Futhark runes"""
    from logic.runes import RunicSystem

    runic_system = RunicSystem()
    runes = runic_system.get_all_elements()

    return render_template("runes_list.html", runes=runes)

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

    # Choose template based on divination type
    if reading_entry.divination_type == "runes":
        template_name = "runic_reading_detail.html"
    else:
        # Default to I Ching template for backward compatibility
        template_name = "iching_reading_detail.html"

    return render_template(template_name,
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
        divination_type = request.form.get("divination_type", "iching")  # Default to I Ching

        if divination_type == "iching":
            # Use legacy I Ching system for now
            legacy_reading = iching.cast_hexagrams()  # This returns a Reading object

            # Create new-style reading for future compatibility
            new_reading = create_iching_reading_from_legacy(legacy_reading)

            # Generate the reading using the extracted function
            reading_text = generate_iching_reading(question, legacy_reading, user, app.logger)

            # Save to history using the new system
            history_entry = user.history.add_reading(question, new_reading, reading_text, divination_type)

            if history_entry:
                # Redirect to the new reading detail page
                return redirect(url_for('reading_detail', reading_path=history_entry.reading_path))
            else:
                flash("Error saving reading. Please try again.", "error")

        elif divination_type == "runes":
            # Get spread type from form, default to single rune
            spread_type = request.form.get("spread_type", "single")

            # Import runic system
            from logic.runes import RunicSystem

            # Create runic reading
            runic_system = RunicSystem()
            runic_reading = runic_system.create_reading(spread_type)

            # Generate the AI reading
            reading_text = generate_runic_reading(question, runic_reading, user, app.logger)

            # Save to history using the new system
            history_entry = user.history.add_reading(question, runic_reading, reading_text, divination_type)

            if history_entry:
                # Redirect to the new reading detail page
                return redirect(url_for('reading_detail', reading_path=history_entry.reading_path))
            else:
                flash("Error saving reading. Please try again.", "error")

        else:
            flash(f"Divination type '{divination_type}' is not yet supported.", "error")

    # Get recent history for display using the lazy-loaded history property
    recent_history = user.history.get_formatted_recent(limit=5, render_markdown=True, enhance_links=True)

    return render_template("index.html",
                         history=recent_history,
                         reading=None,
                         user_birthdate=user.birthdate,
                         user_about_me=user.about_me,
                         username=user.username)

if __name__ == "__main__":
    app.run(debug=True)
