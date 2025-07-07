"""
The Oracle - A Flask application for divination readings.
"""
from flask import Flask
from dotenv import load_dotenv
import os

# Import utility modules
from utils.db_utils import init_db
from utils.hexagram_utils import get_hexagram_symbols, create_hexagram_url_name
from utils.template_utils import register_template_filters
from logic.iching_cache import get_hexagram_symbols_cached

# Import route blueprints
from routes.auth import auth_bp
from routes.navigation import nav_bp
from routes.readings import readings_bp
from routes.api import api_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

# Initialize database
init_db()

# Register template filters
register_template_filters(app)

# Context processor to make hexagram symbols and utility functions available to all templates
@app.context_processor
def inject_hexagram_symbols():
    return {
        'hexagram_symbols': get_hexagram_symbols_cached(),
        'create_hexagram_url_name': create_hexagram_url_name
    }

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(nav_bp)
app.register_blueprint(readings_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(debug=True)
