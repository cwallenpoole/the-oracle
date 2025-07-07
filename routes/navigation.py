"""
Navigation routes for The Oracle application.
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash
from logic import iching
from logic.iching_cache import get_hexagram_section_cached
from utils.hexagram_utils import get_all_hexagrams, parse_hexagram_url
from utils.trigram_utils import get_trigram_info

nav_bp = Blueprint('nav', __name__)


@nav_bp.route("/hexagrams")
def hexagrams_list():
    hexagrams = get_all_hexagrams()
    return render_template("hexagrams_list.html", hexagrams=hexagrams)


@nav_bp.route("/hexagram/<int:number>-<name>")
def hexagram_detail(number, name):
    # Validate and get canonical name
    parsed_number, canonical_name = parse_hexagram_url(f"{number}-{name}")

    if not parsed_number:
        flash("Hexagram not found.", "error")
        return redirect(url_for("nav.hexagrams_list"))

    # Redirect to canonical URL if name doesn't match
    if name.lower() != canonical_name.lower():
        return redirect(url_for("nav.hexagram_detail", number=parsed_number, name=canonical_name))

    # Get hexagram data using cached version
    hex_obj = get_hexagram_section_cached(number)
    if not hex_obj:
        flash("Hexagram not found.", "error")
        return redirect(url_for("nav.hexagrams_list"))

    # Get return_to parameter for trigram links
    return_to = request.args.get('return_to', url_for('nav.hexagrams_list'))

    return render_template("hexagram_detail.html",
                         hexagram=hex_obj,
                         return_to=return_to)


@nav_bp.route("/trigrams")
def trigrams_list():
    trigrams = get_trigram_info()
    return_to = request.args.get('return_to', url_for('nav.hexagrams_list'))

    return render_template("trigrams_list.html",
                         trigrams=trigrams,
                         return_to=return_to)


@nav_bp.route("/runes")
def runes_list():
    """Display all Elder Futhark runes"""
    from logic.runes import RunicSystem

    runic_system = RunicSystem()
    runes = runic_system.get_all_elements()

    return render_template("runes_list.html", runes=runes)


@nav_bp.route("/demo-fire")
def demo_fire():
    """Demo Fire page - showcasing Oracle features and capabilities"""
    return render_template("demo-fire.html")
