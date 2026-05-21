from flask import Blueprint, jsonify, render_template, request, redirect, url_for
from utils.tdx import TDXClient
from app.models.station import Station
from app.models.favorite import Favorite

main_bp = Blueprint('main', __name__)
tdx = TDXClient()

@main_bp.route('/')
def index():
    """Render the main map view."""
    return render_template('index.html')

@main_bp.route('/api/stations')
def get_all_stations():
    """Retrieve all stations from the database for map rendering."""
    stations = Station.get_all()
    return jsonify({
        "status": "success",
        "data": stations
    })

@main_bp.route('/api/station/<station_id>')
def get_station_info(station_id):
    """
    Retrieve station database details combined with real-time arrivals from TDX API.
    """
    station = Station.get_by_station_id(station_id)
    if not station:
        return jsonify({
            "status": "error",
            "message": "Station not found in database"
        }), 404
        
    bus_data = tdx.get_bus_arrival(station_id)
    mrt_data = tdx.get_mrt_arrival(station_id)
    
    return jsonify({
        "status": "success",
        "data": {
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "transport_type": station["transport_type"],
            "bus": bus_data,
            "mrt": mrt_data
        }
    })

@main_bp.route('/favorites')
def favorites():
    """Render the user's favorites list page."""
    fav_list = Favorite.get_all()
    return render_template('favorites.html', favorites=fav_list)

@main_bp.route('/api/favorites/check/<station_id>')
def check_favorite(station_id):
    """Check if a station is currently in favorites."""
    fav = Favorite.get_by_station_id(station_id)
    return jsonify({
        "status": "success",
        "is_favorited": fav is not None
    })

@main_bp.route('/favorites/add', methods=['POST'])
def add_favorite():
    """Add a station to favorites."""
    station_id = request.form.get('station_id')
    if not station_id:
        # Fallback for JSON request
        data = request.get_json() or {}
        station_id = data.get('station_id')

    if not station_id:
        return jsonify({"status": "error", "message": "Missing station_id"}), 400

    station = Station.get_by_station_id(station_id)
    if not station:
        return jsonify({"status": "error", "message": "Station does not exist"}), 404

    existing = Favorite.get_by_station_id(station_id)
    if existing:
        return jsonify({"status": "success", "message": "Already favorited"}), 200

    fav_id = Favorite.create(station_id)
    if fav_id:
        return jsonify({"status": "success", "message": "Added to favorites"}), 201
    else:
        return jsonify({"status": "error", "message": "Failed to add favorite"}), 500

@main_bp.route('/favorites/delete/<station_id>', methods=['POST'])
def delete_favorite(station_id):
    """Delete a station from favorites."""
    success = Favorite.delete_by_station_id(station_id)
    if success:
        # Handle both AJAX request and standard redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({"status": "success", "message": "Favorite deleted"})
        return redirect(url_for('main.favorites'))
    else:
        return jsonify({"status": "error", "message": "Failed to delete favorite"}), 500
