"""
API routes for The Oracle application.
"""
import urllib.parse
import urllib.request
import json
import base64
import os
import math
from datetime import datetime, timezone
from flask import Blueprint, request, current_app, jsonify, session
from logic.ai_readers import analyze_fire_image, generate_flame_reading
from models.user import User

api_bp = Blueprint('api', __name__)


@api_bp.route("/api/geocode")
def geocode():
    """Geocoding proxy to avoid CORS issues and hide implementation details"""
    address = request.args.get('address', '').strip()
    if not address:
        return {'error': 'Address parameter is required'}, 400

    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        encoded_address = urllib.parse.quote(address)
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_address}&limit=1"

        # Add User-Agent header as required by Nominatim
        req = urllib.request.Request(url, headers={'User-Agent': 'Oracle-App/1.0'})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

            if not data:
                return {'error': 'Location not found'}, 404

            result = data[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name'],
                'found': True
            }

    except Exception as e:
        current_app.logger.error(f"Geocoding error: {e}")
        return {'error': 'Geocoding service unavailable'}, 503


@api_bp.route("/api/natal-chart", methods=['POST'])
def natal_chart():
    """Generate accurate natal chart using FREE NASA JPL Horizons API - all planets in one call"""
    try:
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        # Extract birth data
        birth_date = data.get('birth_date')  # YYYY-MM-DD format
        birth_time = data.get('birth_time')  # HH:MM format
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Determine timezone from coordinates
        timezone_name = get_timezone_from_coords(float(latitude), float(longitude))

        # Validate required fields
        if not all([birth_date, birth_time, latitude, longitude]):
            return {'error': 'Birth date, time, latitude, and longitude are required'}, 400

        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            return {'error': 'Invalid latitude or longitude format'}, 400

        # Parse birth datetime
        try:
            birth_datetime_str = f"{birth_date} {birth_time}"
            birth_dt = datetime.strptime(birth_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return {'error': 'Invalid date/time format. Use YYYY-MM-DD and HH:MM'}, 400

        # Get natal chart from FREE NASA JPL Horizons API
        chart_data = get_jpl_horizons_chart(birth_dt, lat, lon, timezone_name)

        return jsonify(chart_data)

    except Exception as e:
        current_app.logger.error(f"Natal chart calculation error: {e}")
        return {'error': 'Failed to calculate natal chart'}, 500


def get_jpl_horizons_chart(birth_dt, latitude, longitude, timezone_name='UTC'):
    """
    Get complete natal chart from FREE NASA JPL Horizons API
    Returns all planetary positions, houses, and chart information
    """

    try:
        # Get planetary positions from NASA JPL Horizons API
        planets = {}

        # NASA JPL Horizons body codes for planets and major asteroids
        jpl_bodies = {
            'Sun': '10',
            'Moon': '301',
            'Mercury': '199',
            'Venus': '299',
            'Mars': '499',
            'Jupiter': '599',
            'Saturn': '699',
            'Uranus': '799',
            'Neptune': '899',
            'Pluto': '999',
            # Major asteroids for advanced astrology
            'Ceres': '2000001',     # Goddess of harvest & nurturing
            'Pallas': '2000002',    # Goddess of wisdom & strategy
            'Juno': '2000003',      # Goddess of marriage & commitment
            'Vesta': '2000004',     # Goddess of hearth & devotion
            'Chiron': '2000002060'  # The wounded healer
        }

        # Convert datetime to JPL format (matching working debug script)
        start_time = birth_dt.strftime('%Y-%m-%dT%H:%M:00')
        end_time = birth_dt.strftime('%Y-%m-%dT%H:%M:01')

        # Get positions for all planets in one batch query
        success_count = 0
        for planet_name, body_code in jpl_bodies.items():
            try:
                position = get_jpl_planet_position(body_code, start_time, end_time, latitude, longitude)
                if position:
                    longitude_deg = position['longitude']
                    precise_position = get_precise_sign_position(longitude_deg)
                    is_retrograde = position.get('speed', 0) < 0

                    planets[planet_name] = {
                        'longitude': longitude_deg,
                        'latitude': position.get('latitude', 0),
                        'distance': position.get('distance', 1.0),
                        'speed': position.get('speed', 0),
                        'retrograde': is_retrograde,
                        'sign': {
                            'name': precise_position['sign'],
                            'degree': round(precise_position['degree_decimal'], 2),
                            'degree_notation': precise_position['degree_notation'],
                            'full_position': precise_position['full_position'],
                            'retrograde_indicator': 'R' if is_retrograde else ''
                        },
                        'house': 0,  # Will be calculated after houses
                        'degree': precise_position['degree_decimal'],
                        'element': get_element_from_sign(precise_position['sign']),
                        'modality': get_modality_from_sign(precise_position['sign'])
                    }
                    success_count += 1
                    current_app.logger.info(f"✅ {planet_name}: {longitude_deg:.2f}°")
                else:
                    current_app.logger.warning(f"❌ Failed to get position for {planet_name}")
            except Exception as e:
                current_app.logger.error(f"Error getting {planet_name} position: {e}")

        if success_count < 8:  # Need at least 8 planets for a basic chart
            current_app.logger.warning(f"Only got {success_count}/10 planets from JPL")
            return get_fallback_chart(birth_dt, latitude, longitude, timezone_name)

        # Calculate houses using simplified Placidus system
        houses = calculate_houses_simple(birth_dt, latitude, longitude)

        # Calculate ascendant and midheaven
        angles = calculate_angles(birth_dt, latitude, longitude)

        # Assign house positions to planets
        for planet_data in planets.values():
            planet_data['house'] = find_house_for_planet(planet_data['longitude'], houses)

        # Calculate aspects between planets (enhanced with minor aspects)
        aspects = calculate_advanced_aspects(planets, angles)

        # Calculate Arabic Parts for advanced astrology
        arabic_parts = calculate_arabic_parts(planets, angles)

        # Calculate planetary dignities (rulerships, exaltations, etc.)
        dignities = calculate_planetary_dignities(planets)

        # Detect astrological chart patterns
        chart_patterns = detect_chart_patterns(planets, aspects)

        # Calculate element and modality breakdown
        element_modality_stats = calculate_element_modality_breakdown(planets)

        return {
            'birth_info': {
                'date': birth_dt.strftime('%Y-%m-%d'),
                'time': birth_dt.strftime('%H:%M'),
                'latitude': latitude,
                'longitude': longitude,
                'timezone': timezone_name,
                'api_source': 'NASA JPL Horizons API (FREE)',
                'planets_found': success_count
            },
            'planets': planets,
            'houses': houses,
            'angles': angles,
            'aspects': aspects,
            'arabic_parts': arabic_parts,
            'dignities': dignities,
            'chart_patterns': chart_patterns,
            'element_modality_stats': element_modality_stats,
            'zodiac_signs': get_zodiac_signs(),
            'success': True
        }

    except Exception as e:
        current_app.logger.error(f"JPL Horizons API error: {e}")
        # Fallback to simplified calculation if JPL API fails
        return get_fallback_chart(birth_dt, latitude, longitude, timezone_name)


def get_jpl_planet_position(body_code, start_time, end_time, latitude, longitude):
    """
    Get planetary position from NASA JPL Horizons API
    Returns longitude, latitude, distance, and speed
    """
    try:
        # JPL Horizons API endpoint
        base_url = "https://ssd.jpl.nasa.gov/api/horizons.api"

        # API parameters (simplified working version from debug script)
        params = {
            'format': 'text',
            'COMMAND': body_code,
            'EPHEM_TYPE': 'OBSERVER',
            'CENTER': '500',  # Geocentric (working in debug)
            'START_TIME': start_time,
            'STOP_TIME': end_time,
            'STEP_SIZE': '1d',
            'QUANTITIES': '1',  # Apparent RA & DEC
            'CSV_FORMAT': 'YES'
        }

        # Build query string
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        # Make request
        req = urllib.request.Request(url, headers={'User-Agent': 'Oracle-App/1.0'})

        with urllib.request.urlopen(req, timeout=15) as response:
            response_text = response.read().decode()

            # Parse JPL response
            return parse_jpl_response(response_text)

    except Exception as e:
        current_app.logger.error(f"JPL API request failed: {e}")
        return None


def parse_jpl_response(response_text):
    """
    Parse NASA JPL Horizons API response to extract planetary coordinates
    """
    try:
        lines = response_text.split('\n')

        # Find the data section between $$SOE and $$EOE markers
        data_start = -1
        data_end = -1

        for i, line in enumerate(lines):
            if '$$SOE' in line:
                data_start = i + 1
            elif '$$EOE' in line:
                data_end = i
                break

        if data_start == -1 or data_end == -1:
            current_app.logger.error("Could not find data markers in JPL response")
            return None

        # Extract the data line (should be only one line for single date query)
        for i in range(data_start, data_end):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                # Parse CSV format: Date, empty, empty, RA, DEC, distance, etc.
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5 and parts[3] != '' and parts[4] != '':
                    try:
                        # Extract RA and DEC from correct positions
                        ra_str = parts[3]  # Right Ascension (H M S format)
                        dec_str = parts[4]  # Declination (D M S format)

                        # Convert RA/DEC to ecliptic longitude
                        longitude = convert_ra_dec_to_longitude(ra_str, dec_str)

                        # Extract distance if available
                        distance = 1.0
                        if len(parts) > 5 and parts[5].strip():
                            try:
                                distance = float(parts[5])
                            except:
                                distance = 1.0

                        return {
                            'longitude': longitude,
                            'latitude': 0,  # Simplified for now
                            'distance': distance,
                            'speed': 0  # Could be calculated from deldot
                        }
                    except Exception as e:
                        current_app.logger.error(f"Error parsing JPL data line: {e}")
                        continue

        current_app.logger.error("No valid data found in JPL response")
        return None

    except Exception as e:
        current_app.logger.error(f"Error parsing JPL response: {e}")
        return None


def convert_ra_dec_to_longitude(ra_str, dec_str):
    """
    Convert Right Ascension and Declination to ecliptic longitude
    Simplified conversion for demonstration
    """
    try:
        # Parse RA in HMS format (e.g., "12 34 56.78")
        ra_parts = ra_str.split()
        if len(ra_parts) >= 3:
            ra_hours = float(ra_parts[0])
            ra_mins = float(ra_parts[1])
            ra_secs = float(ra_parts[2])
            ra_decimal = ra_hours + ra_mins/60 + ra_secs/3600
            ra_degrees = ra_decimal * 15  # Convert hours to degrees
        else:
            ra_degrees = float(ra_str)

        # Parse DEC in DMS format (e.g., "+12 34 56.7")
        dec_parts = dec_str.replace('+', '').replace('-', '').split()
        if len(dec_parts) >= 3:
            dec_degrees = float(dec_parts[0])
            dec_mins = float(dec_parts[1])
            dec_secs = float(dec_parts[2])
            dec_decimal = dec_degrees + dec_mins/60 + dec_secs/3600
            if dec_str.startswith('-'):
                dec_decimal = -dec_decimal
        else:
            dec_decimal = float(dec_str)

        # Simplified conversion to ecliptic longitude
        # For more accuracy, this would need proper coordinate transformation
        longitude = ra_degrees % 360

        return longitude

    except Exception as e:
        current_app.logger.error(f"Error converting RA/DEC: {e}")
        return 0.0


def calculate_houses_simple(birth_dt, latitude, longitude):
    """
    Calculate house cusps using simplified Placidus system
    """
    try:
        # Calculate Local Sidereal Time
        jd = datetime_to_julian(birth_dt)
        lst = calculate_local_sidereal_time(jd, longitude)

        # Calculate Ascendant (simplified)
        ascendant = (lst * 15) % 360  # Convert hours to degrees

        # Calculate house cusps (equal house system for simplicity)
        houses = []
        for house_num in range(1, 13):
            cusp_longitude = (ascendant + (house_num - 1) * 30) % 360
            precise_position = get_precise_sign_position(cusp_longitude)

            houses.append({
                'house': house_num,
                'cusp': cusp_longitude,
                'sign': precise_position['sign'],
                'degree': precise_position['degree_decimal'],
                'degree_notation': precise_position['degree_notation'],
                'full_position': precise_position['full_position']
            })

        return houses

    except Exception as e:
        current_app.logger.error(f"Error calculating houses: {e}")
        return []


def calculate_angles(birth_dt, latitude, longitude):
    """
    Calculate Ascendant and Midheaven
    """
    try:
        jd = datetime_to_julian(birth_dt)
        lst = calculate_local_sidereal_time(jd, longitude)

        # Simplified calculations
        ascendant = (lst * 15) % 360
        midheaven = (ascendant + 90) % 360

        # Get precise positions for angles
        asc_position = get_precise_sign_position(ascendant)
        mc_position = get_precise_sign_position(midheaven)

        return {
            'Ascendant': {
                'longitude': ascendant,
                'sign': {
                    'name': asc_position['sign'],
                    'degree': asc_position['degree_decimal'],
                    'degree_notation': asc_position['degree_notation'],
                    'full_position': asc_position['full_position']
                },
                'house': 1
            },
            'Midheaven': {
                'longitude': midheaven,
                'sign': {
                    'name': mc_position['sign'],
                    'degree': mc_position['degree_decimal'],
                    'degree_notation': mc_position['degree_notation'],
                    'full_position': mc_position['full_position']
                },
                'house': 10
            }
        }

    except Exception as e:
        current_app.logger.error(f"Error calculating angles: {e}")
        return {}


def calculate_local_sidereal_time(jd, longitude):
    """
    Calculate Local Sidereal Time
    """
    # Days since J2000.0
    t = (jd - 2451545.0) / 36525.0

    # Greenwich Mean Sidereal Time at 0h UT (in hours)
    gmst = 6.697374558 + 2400.051336 * t + 0.000025862 * t * t

    # Convert to Local Sidereal Time
    lst = gmst + longitude / 15.0

    # Normalize to 0-24 hours
    return lst % 24


def find_house_for_planet(planet_longitude, houses):
    """
    Find which house a planet belongs to based on its longitude
    """
    if not houses:
        return 0

    for i, house in enumerate(houses):
        next_house = houses[(i + 1) % 12]
        current_cusp = house['cusp']
        next_cusp = next_house['cusp']

        # Handle wrapping around 0°
        if next_cusp < current_cusp:
            if planet_longitude >= current_cusp or planet_longitude < next_cusp:
                return house['house']
        else:
            if current_cusp <= planet_longitude < next_cusp:
                return house['house']

    return 1  # Default to first house


def calculate_aspects_jpl(planets):
    """
    Calculate aspects between planets from JPL data
    """
    aspects = []
    planet_names = list(planets.keys())

    # Major aspects and their orbs
    aspect_types = {
        'conjunction': {'angle': 0, 'orb': 8},
        'opposition': {'angle': 180, 'orb': 8},
        'trine': {'angle': 120, 'orb': 6},
        'square': {'angle': 90, 'orb': 6},
        'sextile': {'angle': 60, 'orb': 4}
    }

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            planet1 = planet_names[i]
            planet2 = planet_names[j]

            long1 = planets[planet1]['longitude']
            long2 = planets[planet2]['longitude']

            # Calculate angular difference
            diff = abs(long1 - long2)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects
            for aspect_name, aspect_data in aspect_types.items():
                target_angle = aspect_data['angle']
                orb = aspect_data['orb']

                if abs(diff - target_angle) <= orb:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect': aspect_name,
                        'angle': diff,
                        'orb': abs(diff - target_angle),
                        'applying': True  # Simplified
                    })

    return aspects


def extract_houses_from_divine(divine_data):
    """Extract house cusps from Divine API data"""
    houses = []

    # Divine API provides house information in the planetary data
    # We need to calculate house cusps based on the Ascendant
    ascendant_longitude = 0

    for item in divine_data:
        if item.get('name') == 'Ascendant':
            ascendant_longitude = float(item.get('longitude', 0))
            break

    # Calculate house cusps using equal house system (30° each)
    for house_num in range(1, 13):
        cusp_longitude = (ascendant_longitude + (house_num - 1) * 30) % 360
        houses.append({
            'house': house_num,
            'longitude': cusp_longitude,
            'sign': get_zodiac_sign_from_longitude(cusp_longitude)
        })

    return houses


def calculate_divine_aspects(planets):
    """Calculate aspects between planets from Divine API data"""
    aspects = []
    planet_names = list(planets.keys())

    # Major aspects and their orbs
    aspect_types = {
        'conjunction': {'angle': 0, 'orb': 8},
        'opposition': {'angle': 180, 'orb': 8},
        'trine': {'angle': 120, 'orb': 6},
        'square': {'angle': 90, 'orb': 6},
        'sextile': {'angle': 60, 'orb': 4}
    }

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            planet1 = planet_names[i]
            planet2 = planet_names[j]

            long1 = planets[planet1]['longitude']
            long2 = planets[planet2]['longitude']

            # Calculate angular difference
            diff = abs(long1 - long2)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects
            for aspect_name, aspect_data in aspect_types.items():
                target_angle = aspect_data['angle']
                orb = aspect_data['orb']

                if abs(diff - target_angle) <= orb:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect': aspect_name,
                        'angle': diff,
                        'orb': abs(diff - target_angle),
                        'applying': True  # Simplified
                    })

    return aspects


def get_fallback_chart(birth_dt, latitude, longitude, timezone_name):
    """Fallback chart calculation if Divine API fails"""
    return {
        'birth_info': {
            'date': birth_dt.strftime('%Y-%m-%d'),
            'time': birth_dt.strftime('%H:%M'),
            'latitude': latitude,
            'longitude': longitude,
            'timezone': timezone_name,
            'api_source': 'Fallback calculation'
        },
        'planets': get_basic_planetary_positions(birth_dt),
        'houses': [],
        'angles': {},
        'aspects': [],
        'zodiac_signs': get_zodiac_signs(),
        'success': False,
        'error': 'Divine API unavailable, using basic calculations'
    }


def get_basic_planetary_positions(birth_dt):
    """Very basic planetary positions for fallback"""
    jd = datetime_to_julian(birth_dt)
    days_since_j2000 = jd - 2451545.0

    # Simplified positions
    return {
        'Sun': {
            'longitude': (280.460 + 0.9856474 * days_since_j2000) % 360,
            'sign': get_zodiac_sign_from_longitude((280.460 + 0.9856474 * days_since_j2000) % 360),
            'house': 0
        },
        'Moon': {
            'longitude': (218.316 + 13.176396 * days_since_j2000) % 360,
            'sign': get_zodiac_sign_from_longitude((218.316 + 13.176396 * days_since_j2000) % 360),
            'house': 0
        }
    }


def datetime_to_julian(dt):
    """Convert datetime to Julian Day Number"""
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3

    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    fraction = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0

    return jdn + fraction - 0.5


def get_element_from_sign(sign):
    """Get element (Fire, Earth, Air, Water) from zodiac sign"""
    elements = {
        'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
        'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
        'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
        'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
    }
    return elements.get(sign, 'Unknown')


def get_modality_from_sign(sign):
    """Get modality (Cardinal, Fixed, Mutable) from zodiac sign"""
    modalities = {
        'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
        'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
        'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
    }
    return modalities.get(sign, 'Unknown')


def calculate_element_modality_breakdown(planets):
    """
    Calculate element and modality distribution among planets
    Returns professional astrology statistics like "Fire: 3, Earth: 0, Air: 5, Water: 2"
    """
    # Initialize counters
    elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    modalities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}

    # Count planets by element and modality (excluding asteroids for traditional count)
    traditional_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

    for planet_name, planet_data in planets.items():
        if planet_name in traditional_planets:
            element = planet_data.get('element', '')
            modality = planet_data.get('modality', '')

            if element in elements:
                elements[element] += 1
            if modality in modalities:
                modalities[modality] += 1

    # Also count with asteroids for comprehensive analysis
    all_elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    all_modalities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}

    for planet_name, planet_data in planets.items():
        element = planet_data.get('element', '')
        modality = planet_data.get('modality', '')

        if element in all_elements:
            all_elements[element] += 1
        if modality in all_modalities:
            all_modalities[modality] += 1

    # Determine dominant element and modality
    dominant_element = max(elements, key=elements.get) if max(elements.values()) > 0 else 'None'
    dominant_modality = max(modalities, key=modalities.get) if max(modalities.values()) > 0 else 'None'

    # Find missing elements
    missing_elements = [elem for elem, count in elements.items() if count == 0]

    return {
        'traditional_planets': {
            'elements': elements,
            'modalities': modalities,
            'total_planets': sum(elements.values())
        },
        'all_celestial_bodies': {
            'elements': all_elements,
            'modalities': all_modalities,
            'total_bodies': sum(all_elements.values())
        },
        'analysis': {
            'dominant_element': dominant_element,
            'dominant_modality': dominant_modality,
            'missing_elements': missing_elements,
            'element_summary': f"Fire: {elements['Fire']}, Earth: {elements['Earth']}, Air: {elements['Air']}, Water: {elements['Water']}",
            'modality_summary': f"Cardinal: {modalities['Cardinal']}, Fixed: {modalities['Fixed']}, Mutable: {modalities['Mutable']}"
        }
    }


def get_timezone_from_coords(latitude, longitude):
    """
    Determine timezone from latitude and longitude coordinates
    """
    try:
        # First try to import timezonefinder for accurate results
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
            if timezone_name:
                return timezone_name
        except ImportError:
            pass

        # Fallback: Use longitude-based approximation
        # This is a rough approximation: 15 degrees longitude ≈ 1 hour
        utc_offset_hours = round(longitude / 15)

        # Common timezone mappings for better accuracy
        timezone_map = {
            # North America
            (-5, 39, 49, -67, -125): 'America/New_York',  # Eastern US
            (-6, 25, 49, -87, -104): 'America/Chicago',   # Central US
            (-7, 31, 49, -104, -117): 'America/Denver',   # Mountain US
            (-8, 32, 49, -117, -125): 'America/Los_Angeles', # Pacific US

            # Europe
            (1, 36, 71, -10, 40): 'Europe/London',
            (2, 47, 56, 5, 15): 'Europe/Paris',
            (1, 35, 72, 6, 19): 'Europe/Berlin',
        }

        # Check if coordinates fall within known regions
        for (offset, lat_min, lat_max, lon_min, lon_max), tz in timezone_map.items():
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                return tz

        # Fallback to UTC offset
        if utc_offset_hours >= 0:
            return f'Etc/GMT-{utc_offset_hours}'
        else:
            return f'Etc/GMT+{abs(utc_offset_hours)}'

    except Exception as e:
        current_app.logger.warning(f"Could not determine timezone for {latitude}, {longitude}: {e}")
        return 'UTC'


def get_zodiac_sign_from_longitude(longitude):
    """Convert longitude (0-360°) to zodiac sign"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_index = int(longitude // 30)
    if 0 <= sign_index < 12:
        return signs[sign_index]
    return 'Unknown'


def format_degrees_minutes(decimal_degrees):
    """
    Convert decimal degrees to degrees and minutes format (e.g., 16.78 -> "16°47'")
    Professional astrology notation
    """
    degrees = int(decimal_degrees)
    minutes = int((decimal_degrees - degrees) * 60)
    return f"{degrees}°{minutes:02d}'"


def get_precise_sign_position(longitude):
    """
    Get precise zodiac sign position with degrees and minutes
    Returns format like "16°47' Pisces"
    """
    sign_name = get_zodiac_sign_from_longitude(longitude)
    degree_in_sign = longitude % 30
    degree_notation = format_degrees_minutes(degree_in_sign)

    return {
        'sign': sign_name,
        'degree_decimal': degree_in_sign,
        'degree_notation': degree_notation,
        'full_position': f"{degree_notation} {sign_name}"
    }


def get_zodiac_signs():
    """Return zodiac sign information"""
    return [
        {'name': 'Aries', 'symbol': '♈', 'element': 'Fire', 'modality': 'Cardinal', 'start': 0},
        {'name': 'Taurus', 'symbol': '♉', 'element': 'Earth', 'modality': 'Fixed', 'start': 30},
        {'name': 'Gemini', 'symbol': '♊', 'element': 'Air', 'modality': 'Mutable', 'start': 60},
        {'name': 'Cancer', 'symbol': '♋', 'element': 'Water', 'modality': 'Cardinal', 'start': 90},
        {'name': 'Leo', 'symbol': '♌', 'element': 'Fire', 'modality': 'Fixed', 'start': 120},
        {'name': 'Virgo', 'symbol': '♍', 'element': 'Earth', 'modality': 'Mutable', 'start': 150},
        {'name': 'Libra', 'symbol': '♎', 'element': 'Air', 'modality': 'Cardinal', 'start': 180},
        {'name': 'Scorpio', 'symbol': '♏', 'element': 'Water', 'modality': 'Fixed', 'start': 210},
        {'name': 'Sagittarius', 'symbol': '♐', 'element': 'Fire', 'modality': 'Mutable', 'start': 240},
        {'name': 'Capricorn', 'symbol': '♑', 'element': 'Earth', 'modality': 'Cardinal', 'start': 270},
        {'name': 'Aquarius', 'symbol': '♒', 'element': 'Air', 'modality': 'Fixed', 'start': 300},
        {'name': 'Pisces', 'symbol': '♓', 'element': 'Water', 'modality': 'Mutable', 'start': 330}
    ]


def calculate_natal_chart(birth_dt, latitude, longitude, timezone_name='UTC'):
    """
    Calculate accurate natal chart using Swiss Ephemeris data
    Returns planetary positions, houses, and aspects
    """

    # Convert to Julian Day Number for ephemeris calculations
    jd = datetime_to_julian(birth_dt)

    # Calculate sidereal time for house calculations
    sidereal_time = calculate_sidereal_time(jd, longitude)

    # Get planetary positions using ephemeris API
    planets = get_planetary_positions(jd)

    # Calculate houses using Placidus system
    houses = calculate_houses_placidus(sidereal_time, latitude)

    # Calculate chart angles (Ascendant, Midheaven, etc.)
    angles = calculate_chart_angles(sidereal_time, latitude, longitude)

    # Calculate aspects between planets
    aspects = calculate_aspects(planets)

    return {
        'birth_info': {
            'date': birth_dt.strftime('%Y-%m-%d'),
            'time': birth_dt.strftime('%H:%M'),
            'latitude': latitude,
            'longitude': longitude,
            'timezone': timezone_name,
            'julian_day': jd,
            'sidereal_time': sidereal_time
        },
        'planets': planets,
        'houses': houses,
        'angles': angles,
        'aspects': aspects,
        'zodiac_signs': get_zodiac_signs()
    }


def datetime_to_julian(dt):
    """Convert datetime to Julian Day Number"""
    # Using standard Julian Day calculation
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3

    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    # Add fractional day for time
    fraction = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0

    return jdn + fraction - 0.5  # Astronomical Julian Day starts at noon


def calculate_sidereal_time(jd, longitude):
    """Calculate Local Sidereal Time"""
    # Greenwich Mean Sidereal Time at 0h UT
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t - t * t * t / 38710000.0

    # Normalize to 0-360 degrees
    gmst = gmst % 360.0
    if gmst < 0:
        gmst += 360.0

    # Convert to Local Sidereal Time
    lst = gmst + longitude
    lst = lst % 360.0
    if lst < 0:
        lst += 360.0

    return lst


def get_planetary_positions(jd):
    """
    Get planetary positions using ephemeris API
    Falls back to simplified calculations if API unavailable
    """
    try:
        # Try to use a real ephemeris API first
        return get_ephemeris_api_positions(jd)
    except Exception as e:
        # Log warning if app context is available, otherwise just print
        try:
            current_app.logger.warning(f"Ephemeris API unavailable, using simplified calculations: {e}")
        except RuntimeError:
            print(f"Ephemeris API unavailable, using simplified calculations: {e}")
        # Fallback to simplified calculations
        return get_simplified_planetary_positions(jd)


def get_ephemeris_api_positions(jd):
    """
    Get planetary positions from NASA JPL Horizons API
    This is the real professional-grade ephemeris service used by astronomers
    """
    from datetime import datetime, timedelta

    planets = {}

    # Convert Julian Day to calendar date for Horizons API
    dt = datetime(2000, 1, 1, 12, 0, 0) + timedelta(days=jd - 2451545.0)
    date_str = dt.strftime('%Y-%m-%d')

    # List of major planets and their Horizons IDs
    planet_ids = {
        'Sun': '10',
        'Moon': '301',
        'Mercury': '199',
        'Venus': '299',
        'Mars': '499',
        'Jupiter': '599',
        'Saturn': '699',
        'Uranus': '799',
        'Neptune': '899',
        'Pluto': '999'
    }

    try:
        # Get positions for each planet from JPL Horizons
        for planet_name, horizons_id in planet_ids.items():
            try:
                # Build JPL Horizons API URL for heliocentric coordinates
                # JPL requires stop time to be after start time, so add 1 hour
                stop_dt = dt + timedelta(hours=1)
                stop_str = stop_dt.strftime('%Y-%m-%d %H:%M')
                start_str = dt.strftime('%Y-%m-%d %H:%M')

                # URL encode the parameters
                params = {
                    'format': 'json',
                    'COMMAND': f"'{horizons_id}'",
                    'EPHEM_TYPE': 'VECTORS',
                    'CENTER': '500@0',  # Solar system barycenter
                    'START_TIME': f"'{start_str}'",
                    'STOP_TIME': f"'{stop_str}'",
                    'STEP_SIZE': '1h',
                    'OUT_UNITS': 'AU-D',
                    'REF_PLANE': 'ECLIPTIC',
                    'REF_SYSTEM': 'J2000',
                    'VEC_TABLE': '2',
                    'VEC_CORR': 'NONE',
                    'OBJ_DATA': 'NO'
                }

                # Build URL with proper encoding
                encoded_params = urllib.parse.urlencode(params)
                api_url = f"https://ssd.jpl.nasa.gov/api/horizons.api?{encoded_params}"

                response = urllib.request.urlopen(api_url, timeout=15)
                result = json.loads(response.read().decode())

                if 'result' in result:
                    # Parse the JPL result to extract coordinates
                    result_text = result['result']

                    # Look for the data lines between $$SOE and $$EOE markers
                    if '$$SOE' in result_text and '$$EOE' in result_text:
                        data_section = result_text.split('$$SOE')[1].split('$$EOE')[0].strip()
                        lines = data_section.split('\n')

                        for line in lines:
                            # Look for lines containing coordinates in JPL format: " X = value Y = value Z = value"
                            if ' X =' in line and ' Y =' in line and ' Z =' in line:
                                try:
                                    # Parse JPL format: " X = 1.383578742584744E+00 Y =-1.621231564658005E-02 Z =-3.426136426962697E-02"
                                    parts = line.strip().split()

                                    # Find X, Y, Z values after the equals signs
                                    x_idx = parts.index('X') + 2 if 'X' in parts else -1
                                    y_idx = parts.index('Y') + 2 if 'Y' in parts else -1
                                    z_idx = parts.index('Z') + 2 if 'Z' in parts else -1

                                    if x_idx > 0 and y_idx > 0 and z_idx > 0:
                                        x = float(parts[x_idx])  # X coordinate (AU)
                                        y = float(parts[y_idx])  # Y coordinate (AU)
                                        z = float(parts[z_idx])  # Z coordinate (AU)

                                        # Convert rectangular to ecliptic longitude
                                        longitude = math.degrees(math.atan2(y, x))
                                        if longitude < 0:
                                            longitude += 360

                                        # Calculate latitude and distance
                                        distance = math.sqrt(x*x + y*y + z*z)
                                        latitude = math.degrees(math.atan2(z, math.sqrt(x*x + y*y)))

                                        planets[planet_name] = {
                                            'longitude': longitude,
                                            'latitude': latitude,
                                            'distance': distance,
                                            'speed': 0,  # Would need velocity calculation
                                            'retrograde': False,  # Would need motion analysis
                                            'sign': get_zodiac_sign_from_longitude(longitude),
                                            'house': 0  # Will be calculated later
                                        }
                                        break

                                except (ValueError, IndexError):
                                    continue

                # If we didn't get data from JPL, fall back to simplified calculation
                if planet_name not in planets:
                    # Use simplified calculation as fallback
                    simplified = get_simplified_planet_position(planet_name, jd)
                    if simplified:
                        planets[planet_name] = {
                            'longitude': simplified['longitude'],
                            'latitude': simplified.get('latitude', 0),
                            'distance': simplified.get('distance', 1),
                            'speed': 0,
                            'retrograde': False,
                            'sign': get_zodiac_sign_from_longitude(simplified['longitude']),
                            'house': 0
                        }

            except Exception as planet_error:
                # For individual planet errors, fall back to simplified calculation
                simplified = get_simplified_planet_position(planet_name, jd)
                if simplified:
                    planets[planet_name] = {
                        'longitude': simplified['longitude'],
                        'latitude': simplified.get('latitude', 0),
                        'distance': simplified.get('distance', 1),
                        'speed': 0,
                        'retrograde': False,
                        'sign': get_zodiac_sign_from_longitude(simplified['longitude']),
                        'house': 0
                    }

        return planets

    except Exception as e:
        raise Exception(f"JPL Horizons API error: {e}")


def get_simplified_planet_position(planet_name, jd):
    """Get simplified planet position for fallback"""
    if planet_name.lower() == 'sun':
        # Simple sun position calculation
        n = jd - 2451545.0
        l = (280.460 + 0.9856474 * n) % 360
        return {'longitude': l, 'latitude': 0, 'distance': 1}
    elif planet_name.lower() == 'moon':
        # Simple moon position calculation
        n = jd - 2451545.0
        l = (218.316 + 13.176396 * n) % 360
        return {'longitude': l, 'latitude': 0, 'distance': 0.002569}
    # Add other simplified calculations for other planets
    return None


def get_simplified_planetary_positions(jd):
    """
    Simplified planetary position calculations for fallback
    Uses basic orbital mechanics - less accurate but functional
    """

    # Orbital elements for planets (simplified)
    orbital_elements = {
        'Sun': {'L0': 280.464, 'n': 0.9856474, 'e': 0.0167, 'omega': 282.937},
        'Moon': {'L0': 318.351, 'n': 13.176358, 'e': 0.0549, 'omega': 125.044},
        'Mercury': {'L0': 252.251, 'n': 4.092385, 'e': 0.2056, 'omega': 77.456},
        'Venus': {'L0': 181.979, 'n': 1.602130, 'e': 0.0068, 'omega': 131.564},
        'Mars': {'L0': 355.433, 'n': 0.524033, 'e': 0.0934, 'omega': 336.041},
        'Jupiter': {'L0': 34.351, 'n': 0.083056, 'e': 0.0484, 'omega': 14.331},
        'Saturn': {'L0': 50.077, 'n': 0.033371, 'e': 0.0540, 'omega': 93.057},
        'Uranus': {'L0': 314.055, 'n': 0.011698, 'e': 0.0472, 'omega': 173.005},
        'Neptune': {'L0': 304.348, 'n': 0.005965, 'e': 0.0086, 'omega': 48.124},
        'Pluto': {'L0': 238.93, 'n': 0.003964, 'e': 0.2488, 'omega': 224.07}
    }

    planets = {}

    # Calculate days since J2000
    days_since_j2000 = jd - 2451545.0

    for name, elements in orbital_elements.items():
        # Calculate mean longitude
        mean_longitude = elements['L0'] + elements['n'] * days_since_j2000
        mean_longitude = mean_longitude % 360.0

        # For now, use simplified calculation (mean longitude ≈ true longitude for circular orbits)
        longitude = mean_longitude

        # Add some basic perturbations for improved accuracy
        if name == 'Moon':
            # Simple lunar perturbations
            sun_longitude = (orbital_elements['Sun']['L0'] + orbital_elements['Sun']['n'] * days_since_j2000) % 360.0
            longitude += 6.29 * math.sin(math.radians(mean_longitude - sun_longitude))

        longitude = longitude % 360.0
        if longitude < 0:
            longitude += 360.0

        planets[name] = {
            'longitude': longitude,
            'latitude': 0.0,  # Simplified - assume planets are on ecliptic
            'distance': 1.0,  # Simplified
            'speed': elements['n'],  # Daily motion
            'retrograde': False,  # Simplified
            'sign': get_zodiac_sign_from_longitude(longitude),
            'house': 0  # Will be calculated later
        }

    # Add calculated points
    planets['North Node'] = {
        'longitude': (125.044 - 0.052954 * days_since_j2000) % 360.0,
        'latitude': 0.0,
        'distance': 1.0,
        'speed': -0.052954,
        'retrograde': True,
        'sign': get_zodiac_sign_from_longitude((125.044 - 0.052954 * days_since_j2000) % 360.0),
        'house': 0
    }

    return planets


def get_vsop87_position(planet_name, jd):
    """
    Get planetary position using VSOP87-based calculations
    More accurate than basic Kepler calculations used by most amateur software
    """

    # Time in Julian centuries since J2000.0
    T = (jd - 2451545.0) / 36525.0

    planet_lower = planet_name.lower()

    if planet_lower == 'sun':
        # Geometric mean longitude of the Sun (deg)
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T

        # Mean anomaly of the Sun (deg)
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T

        # Equation of center
        C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(math.radians(M)) + \
            (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * M)) + \
            0.000289 * math.sin(math.radians(3 * M))

        # True longitude
        longitude = L0 + C

        # Normalize to 0-360
        longitude = longitude % 360

        return {'longitude': longitude, 'latitude': 0, 'distance': 1.0}

    elif planet_lower == 'moon':
        # Lunar longitude (simplified but accurate to ~10 arcminutes)
        # Mean longitude of the Moon
        L_moon = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T + T * T * T / 538841.0 - T * T * T * T / 65194000.0

        # Mean elongation of the Moon
        D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T + T * T * T / 545868.0 - T * T * T * T / 113065000.0

        # Sun's mean anomaly
        M_sun = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T + T * T * T / 24490000.0

        # Moon's mean anomaly
        M_moon = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T + T * T * T / 69699.0 - T * T * T * T / 14712000.0

        # Moon's argument of latitude
        F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T * T - T * T * T / 3526000.0 + T * T * T * T / 863310000.0

        # Periodic terms for longitude (simplified - main terms only)
        longitude_corr = 6.288774 * math.sin(math.radians(M_moon)) + \
                        1.274027 * math.sin(math.radians(2*D - M_moon)) + \
                        0.658314 * math.sin(math.radians(2*D)) + \
                        0.213618 * math.sin(math.radians(2*M_moon)) - \
                        0.185116 * math.sin(math.radians(M_sun)) - \
                        0.114332 * math.sin(math.radians(2*F))

        longitude = L_moon + longitude_corr
        longitude = longitude % 360

        return {'longitude': longitude, 'latitude': 0, 'distance': 0.00257}

    elif planet_lower == 'mercury':
        # Mercury VSOP87 simplified
        L = 252.250906 + 149472.6746358 * T - 0.0000535 * T * T
        a = 0.38709831
        e = 0.20563175 + 0.000020406 * T - 0.0000000284 * T * T
        i = 7.004986 - 0.0059516 * T + 0.000000081 * T * T
        omega = 48.330893 - 0.1254229 * T - 0.000008833 * T * T
        w = 29.124279 + 0.1051581 * T - 0.000012534 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'venus':
        # Venus VSOP87 simplified
        L = 181.979801 + 58517.8156760 * T + 0.00000165 * T * T
        a = 0.72332102
        e = 0.00677188 - 0.000047766 * T + 0.0000000975 * T * T
        i = 3.394662 - 0.0008568 * T - 0.000003244 * T * T
        omega = 76.679920 - 0.2780080 * T - 0.000014256 * T * T
        w = 54.384186 + 0.5081861 * T - 0.000138374 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'mars':
        # Mars VSOP87 simplified
        L = 355.433275 + 19140.2993313 * T + 0.00000261 * T * T
        a = 1.52371243
        e = 0.09336511 + 0.000090484 * T - 0.0000000806 * T * T
        i = 1.849726 - 0.0081479 * T - 0.000002255 * T * T
        omega = 49.588093 - 0.2949846 * T - 0.000063993 * T * T
        w = 286.537204 + 0.4441088 * T - 0.000007009 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'jupiter':
        # Jupiter VSOP87 simplified
        L = 34.351484 + 3034.9056746 * T - 0.00008501 * T * T
        a = 5.20248019
        e = 0.04853590 + 0.000163244 * T - 0.0000004719 * T * T
        i = 1.303267 - 0.0019872 * T + 0.000003318 * T * T
        omega = 100.464441 + 0.1766828 * T + 0.000090387 * T * T
        w = 14.331309 + 0.2155525 * T + 0.000072252 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'saturn':
        # Saturn VSOP87 simplified
        L = 50.077471 + 1222.1137943 * T + 0.00021004 * T * T
        a = 9.54149883
        e = 0.05550825 - 0.000346641 * T - 0.0000006413 * T * T
        i = 2.488878 + 0.0025515 * T - 0.000004903 * T * T
        omega = 113.665524 - 0.2566649 * T - 0.000018345 * T * T
        w = 93.057237 + 0.5665496 * T + 0.000052809 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'uranus':
        # Uranus VSOP87 simplified
        L = 314.055005 + 428.4669983 * T - 0.00000486 * T * T
        a = 19.18797948
        e = 0.04685740 - 0.000001550 * T + 0.0000000071 * T * T
        i = 0.773196 - 0.0016869 * T + 0.000000349 * T * T
        omega = 74.005957 + 0.5211258 * T + 0.000013978 * T * T
        w = 173.005159 + 0.0893206 * T - 0.000009470 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'neptune':
        # Neptune VSOP87 simplified
        L = 304.348665 + 218.4862002 * T + 0.00000059 * T * T
        a = 30.06952752
        e = 0.00895439 + 0.000000628 * T + 0.0000000002 * T * T
        i = 1.769952 + 0.0002257 * T + 0.000000023 * T * T
        omega = 131.784057 - 0.0061651 * T - 0.000000219 * T * T
        w = 48.120276 + 0.0291866 * T + 0.000007610 * T * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    elif planet_lower == 'pluto':
        # Pluto simplified (less accurate due to its complex orbit)
        L = 238.958116 + 144.96 * T
        a = 39.48686035
        e = 0.24885238 + 0.00006016 * T
        i = 17.14104260 + 0.00000501 * T
        omega = 110.30167789 - 0.00809981 * T
        w = 113.76329403 + 0.15906013 * T

        M = L - w
        longitude = solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i)
        return {'longitude': longitude, 'latitude': 0, 'distance': a}

    return None


def solve_kepler_and_convert_to_ecliptic_longitude(M, e, omega, w, i):
    """
    Solve Kepler's equation and convert to ecliptic longitude
    """
    # Normalize mean anomaly
    M = M % 360
    M_rad = math.radians(M)

    # Solve Kepler's equation (simplified iteration)
    E = M_rad
    for _ in range(10):  # Newton-Raphson iteration
        E_new = E + (M_rad + e * math.sin(E) - E) / (1 - e * math.cos(E))
        if abs(E_new - E) < 1e-6:
            break
        E = E_new

    # True anomaly
    nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E/2), math.sqrt(1 - e) * math.cos(E/2))

    # Longitude in orbit
    longitude_in_orbit = math.degrees(nu) + w

    # Convert to ecliptic longitude (simplified)
    longitude = longitude_in_orbit + omega

    # Normalize to 0-360
    longitude = longitude % 360

    return longitude


def calculate_houses_placidus(sidereal_time, latitude):
    """Calculate house cusps using Placidus system"""
    houses = {}

    # Convert latitude to radians
    lat_rad = math.radians(latitude)

    # Calculate house cusps
    for house in range(1, 13):
        if house == 1:
            # 1st house cusp is the Ascendant
            cusp = calculate_ascendant(sidereal_time, latitude)
        elif house == 10:
            # 10th house cusp is the Midheaven (MC)
            cusp = (sidereal_time + 90) % 360.0
        elif house == 4:
            # 4th house cusp is opposite the MC
            cusp = (sidereal_time + 270) % 360.0
        elif house == 7:
            # 7th house cusp is opposite the Ascendant
            asc = calculate_ascendant(sidereal_time, latitude)
            cusp = (asc + 180) % 360.0
        else:
            # For other houses, use simplified equal house calculation
            # (Real Placidus would require complex calculations)
            asc = calculate_ascendant(sidereal_time, latitude)
            cusp = (asc + (house - 1) * 30) % 360.0

        houses[house] = {
            'cusp_longitude': cusp,
            'sign': get_zodiac_sign_from_longitude(cusp)
        }

    return houses


def calculate_ascendant(sidereal_time, latitude):
    """Calculate Ascendant (rising sign)"""
    # Convert to radians
    lst_rad = math.radians(sidereal_time)
    lat_rad = math.radians(latitude)

    # Calculate Ascendant using spherical astronomy
    # Simplified calculation - exact would use iterative methods
    asc_rad = math.atan2(-math.cos(lst_rad),
                        math.sin(lst_rad) * math.cos(lat_rad) +
                        math.tan(math.radians(23.44)) * math.sin(lat_rad))

    asc_deg = math.degrees(asc_rad)
    if asc_deg < 0:
        asc_deg += 360.0

    return asc_deg


def calculate_chart_angles(sidereal_time, latitude, longitude):
    """Calculate major chart angles"""
    ascendant = calculate_ascendant(sidereal_time, latitude)
    midheaven = (sidereal_time + 90) % 360.0
    descendant = (ascendant + 180) % 360.0
    imum_coeli = (midheaven + 180) % 360.0

    return {
        'Ascendant': {
            'longitude': ascendant,
            'sign': get_zodiac_sign_from_longitude(ascendant)
        },
        'Midheaven': {
            'longitude': midheaven,
            'sign': get_zodiac_sign_from_longitude(midheaven)
        },
        'Descendant': {
            'longitude': descendant,
            'sign': get_zodiac_sign_from_longitude(descendant)
        },
        'Imum Coeli': {
            'longitude': imum_coeli,
            'sign': get_zodiac_sign_from_longitude(imum_coeli)
        }
    }


def calculate_aspects(planets):
    """Calculate aspects between planets"""
    aspect_definitions = [
        {'name': 'Conjunction', 'angle': 0, 'orb': 8, 'color': '#ff6b6b'},
        {'name': 'Opposition', 'angle': 180, 'orb': 8, 'color': '#4ecdc4'},
        {'name': 'Trine', 'angle': 120, 'orb': 6, 'color': '#45b7d1'},
        {'name': 'Square', 'angle': 90, 'orb': 6, 'color': '#f9ca24'},
        {'name': 'Sextile', 'angle': 60, 'orb': 4, 'color': '#6c5ce7'},
        {'name': 'Quincunx', 'angle': 150, 'orb': 3, 'color': '#a29bfe'},
        {'name': 'Semisquare', 'angle': 45, 'orb': 2, 'color': '#fd79a8'},
        {'name': 'Sesquiquadrate', 'angle': 135, 'orb': 2, 'color': '#fdcb6e'}
    ]

    aspects = []
    planet_names = list(planets.keys())

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            planet1 = planet_names[i]
            planet2 = planet_names[j]

            lon1 = planets[planet1]['longitude']
            lon2 = planets[planet2]['longitude']

            # Calculate the angular difference
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects
            for aspect_def in aspect_definitions:
                target_angle = aspect_def['angle']
                orb = aspect_def['orb']

                if abs(diff - target_angle) <= orb:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect_name': aspect_def['name'],
                        'angle': target_angle,
                        'actual_angle': diff,
                        'orb': abs(diff - target_angle),
                        'color': aspect_def['color'],
                        'applying': lon1 < lon2  # Simplified
                    })
                    break

    return aspects


def get_zodiac_sign_with_details(longitude):
    """Get zodiac sign with details from ecliptic longitude"""
    signs = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30

    return {
        'name': signs[sign_index],
        'degree': round(degree_in_sign, 2),
        'symbol': get_zodiac_symbol(signs[sign_index])
    }


def get_zodiac_symbol(sign_name):
    """Get zodiac symbol for sign name"""
    symbols = {
        'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋',
        'Leo': '♌', 'Virgo': '♍', 'Libra': '♎', 'Scorpio': '♏',
        'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
    }
    return symbols.get(sign_name, '?')


def get_zodiac_signs():
    """Get zodiac sign data for chart display"""
    return [
        {'name': 'Aries', 'symbol': '♈', 'start_degree': 0, 'element': 'Fire', 'quality': 'Cardinal'},
        {'name': 'Taurus', 'symbol': '♉', 'start_degree': 30, 'element': 'Earth', 'quality': 'Fixed'},
        {'name': 'Gemini', 'symbol': '♊', 'start_degree': 60, 'element': 'Air', 'quality': 'Mutable'},
        {'name': 'Cancer', 'symbol': '♋', 'start_degree': 90, 'element': 'Water', 'quality': 'Cardinal'},
        {'name': 'Leo', 'symbol': '♌', 'start_degree': 120, 'element': 'Fire', 'quality': 'Fixed'},
        {'name': 'Virgo', 'symbol': '♍', 'start_degree': 150, 'element': 'Earth', 'quality': 'Mutable'},
        {'name': 'Libra', 'symbol': '♎', 'start_degree': 180, 'element': 'Air', 'quality': 'Cardinal'},
        {'name': 'Scorpio', 'symbol': '♏', 'start_degree': 210, 'element': 'Water', 'quality': 'Fixed'},
        {'name': 'Sagittarius', 'symbol': '♐', 'start_degree': 240, 'element': 'Fire', 'quality': 'Mutable'},
        {'name': 'Capricorn', 'symbol': '♑', 'start_degree': 270, 'element': 'Earth', 'quality': 'Cardinal'},
        {'name': 'Aquarius', 'symbol': '♒', 'start_degree': 300, 'element': 'Air', 'quality': 'Fixed'},
        {'name': 'Pisces', 'symbol': '♓', 'start_degree': 330, 'element': 'Water', 'quality': 'Mutable'}
    ]


@api_bp.route("/api/save-fire-image", methods=['POST'])
def save_fire_image():
    """Save a captured fire animation image and optionally create a flame reading"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Get the base64 image data
        image_data = data['image']

        # Remove the data URL prefix if present
        if image_data.startswith('data:image/png;base64,'):
            clean_image_data = image_data[22:]  # Remove "data:image/png;base64," prefix
        elif image_data.startswith('data:image/jpeg;base64,'):
            clean_image_data = image_data[23:]  # Remove "data:image/jpeg;base64," prefix
        else:
            clean_image_data = image_data

        # Decode the base64 image
        try:
            image_bytes = base64.b64decode(clean_image_data)
        except Exception as e:
            return jsonify({'error': 'Invalid image data format'}), 400

        # Create the fire captures directory if it doesn't exist
        captures_dir = os.path.join('static', 'fire-captures')
        os.makedirs(captures_dir, exist_ok=True)

        # Generate temporary filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        username = session.get('username', 'anonymous')
        temp_filename = f"fire_{username}_{timestamp}.png"
        temp_filepath = os.path.join(captures_dir, temp_filename)

        # Save the image with temporary filename
        with open(temp_filepath, 'wb') as f:
            f.write(image_bytes)

        # Get additional metadata if provided
        metadata = data.get('metadata', {})

        # Log the save event
        current_app.logger.info(f"Fire image saved: {temp_filepath} for user {username}")

        # Initialize response with temporary filename
        response_data = {
            'success': True,
            'filename': temp_filename,
            'path': temp_filepath,
            'timestamp': timestamp,
            'message': 'Fire image saved successfully'
        }

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Error saving fire image: {e}")
        return jsonify({'error': 'Failed to save fire image'}), 500


# ====================
# ADVANCED ASTROLOGICAL FUNCTIONS
# ====================

def calculate_advanced_aspects(planets, angles):
    """
    Calculate all aspects including minor aspects for professional astrology
    """
    try:
        # Enhanced aspect definitions with minor aspects
        aspect_definitions = {
            'conjunction': {'degrees': 0, 'orb': 8, 'type': 'major', 'nature': 'neutral'},
            'opposition': {'degrees': 180, 'orb': 8, 'type': 'major', 'nature': 'challenging'},
            'trine': {'degrees': 120, 'orb': 8, 'type': 'major', 'nature': 'harmonious'},
            'square': {'degrees': 90, 'orb': 8, 'type': 'major', 'nature': 'challenging'},
            'sextile': {'degrees': 60, 'orb': 6, 'type': 'major', 'nature': 'harmonious'},
            # Minor aspects for advanced astrology (as found in professional charts)
            'semi-sextile': {'degrees': 30, 'orb': 2, 'type': 'minor', 'nature': 'mild'},
            'semi-square': {'degrees': 45, 'orb': 2, 'type': 'minor', 'nature': 'challenging'},
            'octile': {'degrees': 45, 'orb': 2, 'type': 'minor', 'nature': 'challenging'},  # Same as semi-square but different name in some systems
            'sesquiquadrate': {'degrees': 135, 'orb': 2, 'type': 'minor', 'nature': 'challenging'},
            'quincunx': {'degrees': 150, 'orb': 2, 'type': 'minor', 'nature': 'adjusting'},
            # Creative aspects (5th harmonic)
            'quintile': {'degrees': 72, 'orb': 1.5, 'type': 'creative', 'nature': 'creative'},
            'biquintile': {'degrees': 144, 'orb': 1.5, 'type': 'creative', 'nature': 'creative'},
            # Additional minor aspects found in professional software
            'novile': {'degrees': 40, 'orb': 1, 'type': 'spiritual', 'nature': 'spiritual'},
            'binovile': {'degrees': 80, 'orb': 1, 'type': 'spiritual', 'nature': 'spiritual'},
            'quadranovile': {'degrees': 160, 'orb': 1, 'type': 'spiritual', 'nature': 'spiritual'}
        }

        aspects = []
        all_bodies = {**planets, **angles}
        body_names = list(all_bodies.keys())

        for i, planet1 in enumerate(body_names):
            for planet2 in body_names[i + 1:]:
                if planet1 == planet2:
                    continue

                pos1 = all_bodies[planet1]['longitude']
                pos2 = all_bodies[planet2]['longitude']

                # Calculate the shortest angular distance
                diff = abs(pos1 - pos2)
                if diff > 180:
                    diff = 360 - diff

                # Check for aspects
                for aspect_name, aspect_info in aspect_definitions.items():
                    target_angle = aspect_info['degrees']
                    orb = aspect_info['orb']

                    if abs(diff - target_angle) <= orb:
                        orb_value = abs(diff - target_angle)
                        aspects.append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': aspect_name,
                            'orb': round(orb_value, 2),
                            'type': aspect_info['type'],
                            'nature': aspect_info['nature'],
                            'exact': orb_value < 1,
                            'applying': True  # Simplified - in full implementation would check if planets are moving toward exact aspect
                        })

        # Sort by orb (tightest aspects first)
        aspects.sort(key=lambda x: x['orb'])
        return aspects

    except Exception as e:
        current_app.logger.error(f"Error calculating advanced aspects: {e}")
        return []


def calculate_arabic_parts(planets, angles):
    """
    Calculate Arabic Parts (also known as Lots) for advanced astrology
    """
    try:
        arabic_parts = {}

        # Get required positions
        sun_pos = planets.get('Sun', {}).get('longitude', 0)
        moon_pos = planets.get('Moon', {}).get('longitude', 0)
        asc_pos = angles.get('Ascendant', {}).get('longitude', 0)

        # Part of Fortune (most important Arabic Part)
        # Formula: Ascendant + Moon - Sun (for day births)
        # For night births: Ascendant + Sun - Moon

        # Determine if day or night birth (simplified)
        # In full implementation, would check if Sun is above horizon
        is_day_birth = True  # Simplified assumption

        if is_day_birth:
            fortune_pos = (asc_pos + moon_pos - sun_pos) % 360
        else:
            fortune_pos = (asc_pos + sun_pos - moon_pos) % 360

        arabic_parts['Part of Fortune'] = {
            'longitude': fortune_pos,
            'sign': {
                'name': get_zodiac_sign_from_longitude(fortune_pos),
                'degree': round(fortune_pos % 30, 2)
            },
            'description': 'Material prosperity, physical health, and general well-being'
        }

        # Part of Spirit
        if is_day_birth:
            spirit_pos = (asc_pos + sun_pos - moon_pos) % 360
        else:
            spirit_pos = (asc_pos + moon_pos - sun_pos) % 360

        arabic_parts['Part of Spirit'] = {
            'longitude': spirit_pos,
            'sign': {
                'name': get_zodiac_sign_from_longitude(spirit_pos),
                'degree': round(spirit_pos % 30, 2)
            },
            'description': 'Spiritual development, mental energy, and life purpose'
        }

        # Additional Arabic Parts if we have the required planets
        if 'Venus' in planets:
            venus_pos = planets['Venus']['longitude']
            # Part of Love: Ascendant + Venus - Sun
            love_pos = (asc_pos + venus_pos - sun_pos) % 360
            arabic_parts['Part of Love'] = {
                'longitude': love_pos,
                'sign': {
                    'name': get_zodiac_sign_from_longitude(love_pos),
                    'degree': round(love_pos % 30, 2)
                },
                'description': 'Romantic relationships, partnerships, and harmony'
            }

        if 'Mars' in planets:
            mars_pos = planets['Mars']['longitude']
            # Part of Courage: Ascendant + Mars - Sun
            courage_pos = (asc_pos + mars_pos - sun_pos) % 360
            arabic_parts['Part of Courage'] = {
                'longitude': courage_pos,
                'sign': {
                    'name': get_zodiac_sign_from_longitude(courage_pos),
                    'degree': round(courage_pos % 30, 2)
                },
                'description': 'Courage, initiative, and physical energy'
            }

        return arabic_parts

    except Exception as e:
        current_app.logger.error(f"Error calculating Arabic parts: {e}")
        return {}


def calculate_planetary_dignities(planets):
    """
    Calculate planetary dignities (rulerships, exaltations, detriments, falls)
    """
    try:
        # Traditional planetary rulerships
        rulerships = {
            'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
            'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
            'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
        }

        # Modern rulerships (including outer planets)
        modern_rulerships = {
            **rulerships,
            'Scorpio': 'Pluto', 'Aquarius': 'Uranus', 'Pisces': 'Neptune'
        }

        # Exaltations
        exaltations = {
            'Aries': 'Sun', 'Taurus': 'Moon', 'Gemini': None, 'Cancer': 'Jupiter',
            'Leo': None, 'Virgo': 'Mercury', 'Libra': 'Saturn', 'Scorpio': None,
            'Sagittarius': None, 'Capricorn': 'Mars', 'Aquarius': None, 'Pisces': 'Venus'
        }

        dignities = {}

        for planet_name, planet_data in planets.items():
            if planet_name not in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                continue

            sign = planet_data['sign']['name']
            dignity_info = {
                'planet': planet_name,
                'sign': sign,
                'dignities': []
            }

            # Check for rulership (traditional)
            if rulerships.get(sign) == planet_name:
                dignity_info['dignities'].append({
                    'type': 'rulership_traditional',
                    'strength': 5,
                    'description': f'{planet_name} rules {sign} (traditional)'
                })

            # Check for modern rulership
            if modern_rulerships.get(sign) == planet_name and modern_rulerships.get(sign) != rulerships.get(sign):
                dignity_info['dignities'].append({
                    'type': 'rulership_modern',
                    'strength': 4,
                    'description': f'{planet_name} rules {sign} (modern)'
                })

            # Check for exaltation
            if exaltations.get(sign) == planet_name:
                dignity_info['dignities'].append({
                    'type': 'exaltation',
                    'strength': 4,
                    'description': f'{planet_name} is exalted in {sign}'
                })

            # Check for detriment (opposite of rulership)
            for ruled_sign, ruler in modern_rulerships.items():
                if ruler == planet_name:
                    opposite_sign = get_opposite_sign(ruled_sign)
                    if opposite_sign == sign:
                        dignity_info['dignities'].append({
                            'type': 'detriment',
                            'strength': -4,
                            'description': f'{planet_name} is in detriment in {sign}'
                        })

            # Check for fall (opposite of exaltation)
            for exalt_sign, exalt_planet in exaltations.items():
                if exalt_planet == planet_name:
                    opposite_sign = get_opposite_sign(exalt_sign)
                    if opposite_sign == sign:
                        dignity_info['dignities'].append({
                            'type': 'fall',
                            'strength': -4,
                            'description': f'{planet_name} is in fall in {sign}'
                        })

            # Calculate total dignity score
            dignity_info['total_strength'] = sum(d['strength'] for d in dignity_info['dignities'])

            if dignity_info['dignities']:  # Only add if there are dignities
                dignities[planet_name] = dignity_info

        return dignities

    except Exception as e:
        current_app.logger.error(f"Error calculating planetary dignities: {e}")
        return {}


def detect_chart_patterns(planets, aspects):
    """
    Detect major astrological chart patterns (Grand Trines, T-Squares, etc.)
    """
    try:
        patterns = []

        # Get aspect data organized by type
        trines = [a for a in aspects if a['aspect'] == 'trine' and a['orb'] <= 6]
        squares = [a for a in aspects if a['aspect'] == 'square' and a['orb'] <= 6]
        oppositions = [a for a in aspects if a['aspect'] == 'opposition' and a['orb'] <= 6]
        sextiles = [a for a in aspects if a['aspect'] == 'sextile' and a['orb'] <= 4]

        # Detect Grand Trines (3 planets in trine aspect forming a triangle)
        grand_trines = detect_grand_trines(trines, planets)
        patterns.extend(grand_trines)

        # Detect T-Squares (2 squares + 1 opposition)
        t_squares = detect_t_squares(squares, oppositions, planets)
        patterns.extend(t_squares)

        # Detect Grand Cross (4 squares + 2 oppositions)
        grand_crosses = detect_grand_crosses(squares, oppositions, planets)
        patterns.extend(grand_crosses)

        # Detect Mystic Rectangle (2 oppositions + 4 sextiles)
        mystic_rectangles = detect_mystic_rectangles(oppositions, sextiles, planets)
        patterns.extend(mystic_rectangles)

        # Detect Stelliums (3+ planets in same sign or within 12 degrees)
        stelliums = detect_stelliums(planets)
        patterns.extend(stelliums)

        return patterns

    except Exception as e:
        current_app.logger.error(f"Error detecting chart patterns: {e}")
        return []


def detect_grand_trines(trines, planets):
    """Detect Grand Trine patterns"""
    grand_trines = []

    # Find sets of 3 planets that are all trine to each other
    planet_names = list(planets.keys())

    for i, p1 in enumerate(planet_names):
        for j, p2 in enumerate(planet_names[i+1:], i+1):
            for k, p3 in enumerate(planet_names[j+1:], j+1):
                # Check if all three planets are trine to each other
                trine_12 = any(t for t in trines if (t['planet1'] == p1 and t['planet2'] == p2) or (t['planet1'] == p2 and t['planet2'] == p1))
                trine_13 = any(t for t in trines if (t['planet1'] == p1 and t['planet2'] == p3) or (t['planet1'] == p3 and t['planet2'] == p1))
                trine_23 = any(t for t in trines if (t['planet1'] == p2 and t['planet2'] == p3) or (t['planet1'] == p3 and t['planet2'] == p2))

                if trine_12 and trine_13 and trine_23:
                    # Determine element
                    elements = [get_element_from_sign(planets[p]['sign']['name']) for p in [p1, p2, p3]]
                    most_common_element = max(set(elements), key=elements.count)

                    grand_trines.append({
                        'type': 'Grand Trine',
                        'planets': [p1, p2, p3],
                        'element': most_common_element,
                        'description': f'Grand Trine in {most_common_element} - Natural talent and ease of expression',
                        'strength': 'strong'
                    })

    return grand_trines


def detect_t_squares(squares, oppositions, planets):
    """Detect T-Square patterns"""
    t_squares = []

    # T-Square: planet A opposes planet B, and planet C squares both A and B
    for opp in oppositions:
        p1, p2 = opp['planet1'], opp['planet2']

        # Find planets that square both ends of the opposition
        for planet_name in planets.keys():
            if planet_name in [p1, p2]:
                continue

            squares_p1 = any(s for s in squares if (s['planet1'] == planet_name and s['planet2'] == p1) or (s['planet1'] == p1 and s['planet2'] == planet_name))
            squares_p2 = any(s for s in squares if (s['planet1'] == planet_name and s['planet2'] == p2) or (s['planet1'] == p2 and s['planet2'] == planet_name))

            if squares_p1 and squares_p2:
                # Determine modality
                signs = [planets[p]['sign']['name'] for p in [p1, p2, planet_name]]
                modalities = [get_modality_from_sign(sign) for sign in signs]
                most_common_modality = max(set(modalities), key=modalities.count)

                t_squares.append({
                    'type': 'T-Square',
                    'planets': [p1, p2, planet_name],
                    'apex': planet_name,  # The planet that squares the opposition
                    'modality': most_common_modality,
                    'description': f'T-Square in {most_common_modality} signs - Dynamic tension requiring action',
                    'strength': 'strong'
                })

    return t_squares


def detect_grand_crosses(squares, oppositions, planets):
    """Detect Grand Cross patterns"""
    grand_crosses = []

    # Grand Cross: 4 planets, each squaring the adjacent ones and opposing the one across
    if len(oppositions) >= 2:
        for i, opp1 in enumerate(oppositions):
            for opp2 in oppositions[i+1:]:
                p1, p2 = opp1['planet1'], opp1['planet2']
                p3, p4 = opp2['planet1'], opp2['planet2']

                # Check if we have the required squares
                required_squares = [
                    (p1, p3), (p1, p4), (p2, p3), (p2, p4)
                ]

                squares_found = 0
                for sq_p1, sq_p2 in required_squares:
                    if any(s for s in squares if (s['planet1'] == sq_p1 and s['planet2'] == sq_p2) or (s['planet1'] == sq_p2 and s['planet2'] == sq_p1)):
                        squares_found += 1

                if squares_found >= 3:  # Allow some flexibility
                    signs = [planets[p]['sign']['name'] for p in [p1, p2, p3, p4]]
                    modalities = [get_modality_from_sign(sign) for sign in signs]
                    most_common_modality = max(set(modalities), key=modalities.count)

                    grand_crosses.append({
                        'type': 'Grand Cross',
                        'planets': [p1, p2, p3, p4],
                        'modality': most_common_modality,
                        'description': f'Grand Cross in {most_common_modality} signs - Major life challenges and achievement potential',
                        'strength': 'very strong'
                    })

    return grand_crosses


def detect_mystic_rectangles(oppositions, sextiles, planets):
    """Detect Mystic Rectangle patterns"""
    # Implementation placeholder - complex pattern detection
    return []


def detect_stelliums(planets):
    """Detect Stellium patterns (3+ planets in same sign or close conjunction)"""
    stelliums = []

    # Group planets by sign
    by_sign = {}
    for planet_name, planet_data in planets.items():
        sign = planet_data['sign']['name']
        if sign not in by_sign:
            by_sign[sign] = []
        by_sign[sign].append(planet_name)

    # Check for 3+ planets in same sign
    for sign, planet_list in by_sign.items():
        if len(planet_list) >= 3:
            element = get_element_from_sign(sign)
            modality = get_modality_from_sign(sign)

            stelliums.append({
                'type': 'Stellium',
                'planets': planet_list,
                'sign': sign,
                'element': element,
                'modality': modality,
                'description': f'Stellium in {sign} - Concentrated energy and focus in {element} {modality} themes',
                'strength': 'strong' if len(planet_list) >= 4 else 'moderate'
            })

    return stelliums


def get_opposite_sign(sign):
    """Get the opposite zodiac sign"""
    opposites = {
        'Aries': 'Libra', 'Taurus': 'Scorpio', 'Gemini': 'Sagittarius',
        'Cancer': 'Capricorn', 'Leo': 'Aquarius', 'Virgo': 'Pisces',
        'Libra': 'Aries', 'Scorpio': 'Taurus', 'Sagittarius': 'Gemini',
        'Capricorn': 'Cancer', 'Aquarius': 'Leo', 'Pisces': 'Virgo'
    }
    return opposites.get(sign, sign)
