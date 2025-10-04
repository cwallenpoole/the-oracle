"""
Reading routes for The Oracle application.
"""
import base64
import sqlite3
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, session, flash, current_app, jsonify
from logic import iching
from logic.iching_adapter import create_iching_reading_from_legacy
from logic.ai_readers import generate_iching_reading, generate_runic_reading, generate_followup_reading
from models.user import User
from models.history import History
from models.llm_request import LLMRequest
from utils.db_utils import DB_FILE
import os

readings_bp = Blueprint('readings', __name__)

# Constants
PYROMANCY_ROUTE = "nav.pyromancy"


@readings_bp.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    # Get user object (history is lazy-loaded via property)
    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("auth.login"))

    recent_history = []

    if request.method == "POST":
        question = request.form["question"]
        divination_type = request.form.get("divination_type", "iching")  # Default to I Ching

        if divination_type == "iching":
            # Use legacy I Ching system for now
            legacy_reading = iching.cast_hexagrams()  # This returns a Reading object

            # Create new-style reading for future compatibility
            new_reading = create_iching_reading_from_legacy(legacy_reading)

            # Save to history first to get the reading_id
            history_entry = user.history.add_reading(question, new_reading, "", divination_type)

            # Generate the reading using the extracted function with reading_id
            reading_text = generate_iching_reading(question, legacy_reading, user, current_app.logger, history_entry.reading_id)

            # Update the history entry with the actual reading text
            history_entry._reading_string = reading_text
            history_entry.save()

            if history_entry:
                # Redirect to the new reading detail page
                return redirect(url_for('readings.reading_detail', reading_path=history_entry.reading_path))
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

            # Save to history first to get the reading_id
            history_entry = user.history.add_reading(question, runic_reading, "", divination_type)

            # Generate the AI reading with reading_id
            reading_text = generate_runic_reading(question, runic_reading, user, current_app.logger, history_entry.reading_id)

            # Update the history entry with the actual reading text
            history_entry._reading_string = reading_text
            history_entry.save()

            if history_entry:
                # Redirect to the new reading detail page
                return redirect(url_for('readings.reading_detail', reading_path=history_entry.reading_path))
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


@readings_bp.route("/reading/<reading_path>")
def reading_detail(reading_path):
    """Display detailed view of a specific reading"""
    from models.history import History

    # Get the reading entry
    reading_entry = History.get_reading_by_path(reading_path)
    if not reading_entry:
        flash("Reading not found.", "error")
        return redirect(url_for("readings.index"))

    # Check if user has permission to view this reading (must be the owner or logged in as the same user)
    if "username" not in session or session["username"] != reading_entry.username:
        flash("You don't have permission to view this reading.", "error")
        return redirect(url_for("auth.login"))

    # Choose template based on divination type
    if reading_entry.divination_type == "runes":
        template_name = "runic_reading_detail.html"
    elif reading_entry.divination_type == "flame_reading":
        template_name = "flame_reading_detail.html"
    else:
        # Default to I Ching template for backward compatibility
        template_name = "iching_reading_detail.html"

    # Get LLM requests for follow-ups
    llm_requests = LLMRequest.get_by_reading_id(reading_entry.reading_id)

    return render_template(template_name,
                         reading_entry=reading_entry,
                         enhanced_reading=reading_entry.get_enhanced_reading_html(),
                         llm_requests=llm_requests)


@readings_bp.route("/followup/<reading_id>", methods=["POST"])
def submit_followup(reading_id):
    """Handle follow-up question submission"""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("auth.login"))

    # Get the original reading entry
    reading_entry = None
    for entry in user.history.get_all():
        if entry.reading_id == reading_id:
            reading_entry = entry
            break

    if not reading_entry:
        flash("Original reading not found.", "error")
        return redirect(url_for("readings.index"))

    # Get the follow-up question from the form
    followup_question = request.form.get("followup_question", "").strip()
    if not followup_question:
        flash("Please enter a follow-up question.", "error")
        return redirect(url_for('readings.reading_detail', reading_path=reading_entry.reading_path))

    try:
        # Get the original LLM request data
        initial_request = LLMRequest.get_initial_request(reading_id)
        if not initial_request:
            flash("Unable to find original reading context for follow-up.", "error")
            return redirect(url_for('readings.reading_detail', reading_path=reading_entry.reading_path))

        # Generate follow-up reading
        followup_response = generate_followup_reading(
            question=reading_entry.question,
            followup_question=followup_question,
            original_response=initial_request.response_data,
            original_request=initial_request.request_data,
            user=user,
            reading_id=reading_id,
            logger=current_app.logger
        )

        # Create a new history entry for the follow-up
        followup_hexagram = f"follow-up: {reading_id}"
        followup_history_entry = user.history.add_reading(
            question=followup_question,
            hexagram=followup_hexagram,
            reading=followup_response,
            divination_type="follow-up"
        )

        current_app.logger.info(f"Followup history entry: {followup_history_entry}")
        if followup_history_entry:
            flash("Follow-up reading generated successfully!", "success")
            # Redirect to the new follow-up reading's detail page
            return redirect(url_for('readings.reading_detail', reading_path=followup_history_entry.reading_path))
        else:
            flash("Error saving follow-up reading. Please try again.", "error")

    except Exception as e:
        current_app.logger.error(f"Error generating follow-up reading: {e}")
        flash("Error generating follow-up reading. Please try again.", "error")

    return redirect(url_for('readings.reading_detail', reading_path=reading_entry.reading_path))


@readings_bp.route("/delete_reading/<reading_id>", methods=["DELETE"])
def delete_reading(reading_id):
    """Delete a reading and all associated data"""
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = User.get_by_username(session["username"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Verify the reading belongs to the user
        c.execute("SELECT * FROM history WHERE reading_id = ? AND username = ?",
                  (reading_id, session["username"]))
        reading = c.fetchone()

        if not reading:
            conn.close()
            return jsonify({"error": "Reading not found or access denied"}), 404

        # Delete associated LLM requests first (foreign key constraint)
        c.execute("DELETE FROM llm_requests WHERE reading_id = ?", (reading_id,))

        # Delete the reading
        c.execute("DELETE FROM history WHERE reading_id = ? AND username = ?",
                  (reading_id, session["username"]))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error deleting reading: {e}")
        return jsonify({"error": "Failed to delete reading"}), 500


def _load_fire_image(fire_image_data):
    """Helper function to load fire image data from filename or base64"""
    if fire_image_data.endswith('.png') or fire_image_data.endswith('.jpg'):
        # It's a filename - load from server storage
        image_path = os.path.join("static", "fire-captures", fire_image_data)
        if not os.path.exists(image_path):
            return None, "Fire image not found on server. Please capture a new image."

        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            fire_image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            current_app.logger.info(f"Using server-stored image: {image_path}")
            return fire_image_base64, None
    else:
        # It's base64 data - use as is (fallback)
        current_app.logger.info("Using base64 image data directly")
        return fire_image_data, None


def _save_fire_image_for_reading(fire_image_data, fire_image_base64, reading_id):
    """Helper function to save fire image for reading"""
    final_filename = f"fire_{reading_id}.png"
    final_filepath = os.path.join("static", "fire-captures", final_filename)

    if fire_image_data.endswith('.png') or fire_image_data.endswith('.jpg'):
        # Rename server-stored image to final name
        source_path = os.path.join("static", "fire-captures", fire_image_data)
        if os.path.exists(source_path):
            os.rename(source_path, final_filepath)
            current_app.logger.info(f"Renamed {source_path} to {final_filepath}")
    else:
        # Save base64 data as image file (fallback)
        with open(final_filepath, 'wb') as f:
            f.write(base64.b64decode(fire_image_base64))
        current_app.logger.info(f"Saved base64 image to {final_filepath}")


@readings_bp.route("/pyromancy_reading", methods=["POST"])
def pyromancy_reading():
    """Handle pyromancy (fire) reading submission"""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("auth.login"))

    # Get question and fire image data from form
    question = request.form.get("question", "").strip()
    fire_image_data = request.form.get("fire_image_data", "")

    if not fire_image_data:
        flash("No fire image captured. Please capture a fire image first.", "error")
        return redirect(url_for(PYROMANCY_ROUTE))

    try:
        # Import the AI readers functions
        from logic.ai_readers import analyze_fire_image, generate_flame_reading

        # Load fire image data
        fire_image_base64, error_msg = _load_fire_image(fire_image_data)
        if error_msg:
            flash(error_msg, "error")
            return redirect(url_for(PYROMANCY_ROUTE))

        # Analyze the fire image to get vision analysis
        vision_analysis = analyze_fire_image(fire_image_base64, current_app.logger)

        # Save to history first to get the reading_id
        history_entry = user.history.add_reading(
            question=question or "What do the flames reveal?",
            hexagram=vision_analysis,  # Store the vision analysis as hexagram
            reading="",  # Will be filled with the actual reading
            divination_type="flame_reading"
        )

        # Generate the flame reading using the vision analysis
        reading_text = generate_flame_reading(vision_analysis, user, current_app.logger, history_entry.reading_id)

        # Update the history entry with the actual reading text
        history_entry._reading_string = reading_text
        history_entry.save()

        # Handle image storage for the reading
        _save_fire_image_for_reading(fire_image_data, fire_image_base64, history_entry.reading_id)

        if history_entry:
            # Redirect to the new reading detail page
            return redirect(url_for('readings.reading_detail', reading_path=history_entry.reading_path))
        else:
            flash("Error saving flame reading. Please try again.", "error")

    except Exception as e:
        current_app.logger.error(f"Error generating flame reading: {e}")
        flash("Error generating flame reading. Please try again.", "error")

    return redirect(url_for(PYROMANCY_ROUTE))


@readings_bp.route("/drafts")
def drafts():
    """Experimental drafts page - not linked to main navigation"""
    return render_template("drafts.html")
