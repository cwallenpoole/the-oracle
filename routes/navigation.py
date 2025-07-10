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


@nav_bp.route("/pyromancy")
def pyromancy():
    """Pyromancy page - fire divination and flame readings"""
    return render_template("pyromancy.html")


@nav_bp.route("/wiki")
def wiki_list():
    """Display all wiki entries organized by category"""
    from utils.wiki_utils import list_wiki_entries, WikiEntry
    from utils.hexagram_utils import get_all_hexagrams
    from utils.trigram_utils import get_trigram_info
    from logic.runes import RunicSystem

    # Get all wiki entries
    entries_by_category = list_wiki_entries()

    # Add divination types as a special category
    divination_entries = []

    # Add hexagrams
    hexagrams = get_all_hexagrams()
    divination_entries.append({
        'filename': 'hexagrams',
        'title': 'I Ching Hexagrams',
        'url': url_for('nav.hexagrams_list'),
        'is_placeholder': False,
        'description': f'{len(hexagrams)} hexagrams for divination'
    })

    # Add trigrams
    trigrams = get_trigram_info()
    divination_entries.append({
        'filename': 'trigrams',
        'title': 'I Ching Trigrams',
        'url': url_for('nav.trigrams_list'),
        'is_placeholder': False,
        'description': f'{len(trigrams)} trigrams - building blocks of hexagrams'
    })

    # Add runes
    runic_system = RunicSystem()
    runes = runic_system.get_all_elements()
    divination_entries.append({
        'filename': 'runes',
        'title': 'Elder Futhark Runes',
        'url': url_for('nav.runes_list'),
        'is_placeholder': False,
        'description': f'{len(runes)} runes for divination'
    })

    # Enhance with additional metadata
    enhanced_entries = {}
    for category, filenames in entries_by_category.items():
        enhanced_entries[category] = []
        for filename in sorted(filenames):
            entry = WikiEntry(filename, category)
            title = filename.replace('_', ' ').title()
            enhanced_entries[category].append({
                'filename': filename,
                'title': title,
                'url': entry.get_url_path(),
                'is_placeholder': entry.is_placeholder()
            })

    # Add divination types category
    enhanced_entries['divination_types'] = divination_entries

    return render_template("wiki_list.html", entries=enhanced_entries)


@nav_bp.route("/wiki/<filename>")
def wiki_entry(filename):
    """Display a wiki entry"""
    from utils.wiki_utils import get_wiki_entry_content, load_synonyms

    # Check if this is a synonym that should redirect
    synonyms = load_synonyms()
    if filename in synonyms:
        canonical_info = synonyms[filename]
        canonical_filename = canonical_info['canonical']
        # Redirect to the canonical entry
        return redirect(url_for('nav.wiki_entry', filename=canonical_filename))

    # Get the content (searches across all categories)
    result = get_wiki_entry_content(filename)

    if result is None:
        flash("Wiki entry not found.", "error")
        return redirect(url_for("readings.index"))

    content, category = result

    # Extract title from filename (convert underscores to spaces and title case)
    title = filename.replace('_', ' ').title()

    return render_template("wiki_entry.html",
                         content=content,
                         title=title,
                         category=category.title(),
                         filename=filename)
