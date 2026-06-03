import logging
from app.models import get_db_connection

logger = logging.getLogger(__name__)

class Station:
    @staticmethod
    def create(station_id, station_name, lat, lon, transport_type):
        """
        Create a new station record in the database.
        
        :param station_id: Unique string identifier from the transit API
        :param station_name: Name of the station
        :param lat: Latitude coordinate
        :param lon: Longitude coordinate
        :param transport_type: Type of transport ('Bus' or 'MRT')
        :return: Inserted row ID if successful, None otherwise
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
                (station_id, station_name, lat, lon, transport_type)
            )
            conn.commit()
            station_row_id = cursor.lastrowid
            conn.close()
            return station_row_id
        except Exception as e:
            logger.error(f"Error creating station: {e}")
            return None

    @staticmethod
    def get_all():
        """
        Retrieve all station records.
        
        :return: List of dictionaries containing station data
        """
        try:
            conn = get_db_connection()
            stations = conn.execute("SELECT * FROM stations").fetchall()
            conn.close()
            return [dict(row) for row in stations]
        except Exception as e:
            logger.error(f"Error getting all stations: {e}")
            return []

    @staticmethod
    def get_by_id(station_db_id):
        """
        Retrieve a single station by its database primary key ID.
        
        :param station_db_id: Database auto-increment ID
        :return: Dictionary containing station data, or None
        """
        try:
            conn = get_db_connection()
            row = conn.execute("SELECT * FROM stations WHERE id = ?", (station_db_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting station by id {station_db_id}: {e}")
            return None

    @staticmethod
    def get_by_station_id(station_id):
        """
        Retrieve a single station by its transit-system station_id.
        
        :param station_id: Unique string identifier from transit API
        :return: Dictionary containing station data, or None
        """
        try:
            conn = get_db_connection()
            row = conn.execute("SELECT * FROM stations WHERE station_id = ?", (station_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting station by station_id {station_id}: {e}")
            return None

    @staticmethod
    def update(station_db_id, station_name, lat, lon, transport_type):
        """
        Update an existing station's details.
        
        :param station_db_id: Database auto-increment ID
        :param station_name: Updated name of the station
        :param lat: Updated latitude
        :param lon: Updated longitude
        :param transport_type: Updated transport type
        :return: True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            conn.execute(
                "UPDATE stations SET station_name = ?, lat = ?, lon = ?, transport_type = ? WHERE id = ?",
                (station_name, lat, lon, transport_type, station_db_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating station {station_db_id}: {e}")
            return False

    @staticmethod
    def delete(station_db_id):
        """
        Delete a station by its database primary key ID.
        
        :param station_db_id: Database auto-increment ID
        :return: True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            conn.execute("DELETE FROM stations WHERE id = ?", (station_db_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting station {station_db_id}: {e}")
            return False
