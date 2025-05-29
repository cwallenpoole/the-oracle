### app.py
from flask import Flask, request, render_template, redirect, url_for, session
from logic import iching
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os, sqlite3

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

# Set your OpenAI API key here or use an environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

DB_FILE = "data/users.db"

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    username TEXT,
                    question TEXT,
                    hexagram TEXT,
                    reading TEXT,
                    reading_dt TEXT
                 )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            return render_template("register.html", error="Username already exists.")

        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    reading = None
    recent_history = None
    if request.method == "POST":
        question = request.form["question"]
        (hexagram, secondary) = iching.cast_hexagrams()
        hex_text = iching.get_text(hexagram)

        s = ''
        future = 'Your current casting does not have a separate future.'
        if secondary:
            s = 's'
            secondary_text = iching.get_text(secondary)
            future = '''
            The hexagram had transitional forms. The hexagram for the future is {secondary} 

            Here is the traditional text:
            {secondary_text}

            '''
        # Fetch last 3 readings
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT question, hexagram, reading FROM history WHERE username = ? ORDER BY rowid DESC LIMIT 3", (session["username"],))
        recent_history = c.fetchall()
        conn.close()

        history_text = ''
        if recent_history: 
            history_text = 'Here is the user\'s recent reading history:' + "\n".join([f"Q: {q}\nHex: {h}\nReading: {r}\n" for q, h, r in reversed(recent_history)])

        prompt = f"""
        You are a wise I Ching diviner.

        The user has asked a new question: \"{question}\".
        The newly cast hexagram is {hexagram}.

        Here is the traditional text:
        {hex_text} {future}

        {history_text}

        Based on this history and the new hexagram{s}, offer a deep, poetic, and contextually insightful reading.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a mystical I Ching oracle."},
                {"role": "user", "content": prompt},
            ]
        )

        reading = response.choices[0].message.content

        if secondary:
            hexagram += ' transitioning to ' + secondary

        # Save history to database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO history (username, question, hexagram, reading, reading_dt) VALUES (?, ?, ?, ?, current_timestamp)",
                  (session["username"], question, hexagram, reading))
        conn.commit()
        conn.close()

    return render_template("index.html", history=recent_history or [], reading=reading or '')

if __name__ == "__main__":
    app.run(debug=True)
