import logging
from app.models import get_db_connection

logger = logging.getLogger(__name__)

class Favorite:
    @staticmethod
    def create(station_id):
        """
        Add a station to the favorites list.
        
        :param station_id: Unique string identifier from the transit API
        :return: Inserted row ID if successful, None otherwise
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO favorites (station_id) VALUES (?)",
                (station_id,)
            )
            conn.commit()
            fav_id = cursor.lastrowid
            conn.close()
            return fav_id
        except Exception as e:
            logger.error(f"Error creating favorite for station {station_id}: {e}")
            return None

    @staticmethod
    def get_all():
        """
        Get all favorites, joined with station details.
        
        :return: List of dictionaries containing favorite and station details
        """
        try:
            conn = get_db_connection()
            query = """
                SELECT f.id, f.station_id, f.added_at, s.station_name, s.lat, s.lon, s.transport_type
                FROM favorites f
                LEFT JOIN stations s ON f.station_id = s.station_id
                ORDER BY f.added_at DESC
            """
            favorites = conn.execute(query).fetchall()
            conn.close()
            return [dict(row) for row in favorites]
        except Exception as e:
            logger.error(f"Error getting all favorites: {e}")
            return []

    @staticmethod
    def get_by_id(fav_db_id):
        """
        Get a single favorite record by its database ID.
        
        :param fav_db_id: Database auto-increment ID
        :return: Dictionary containing favorite data, or None
        """
        try:
            conn = get_db_connection()
            row = conn.execute("SELECT * FROM favorites WHERE id = ?", (fav_db_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting favorite by id {fav_db_id}: {e}")
            return None

    @staticmethod
    def get_by_station_id(station_id):
        """
        Get a favorite record by station_id.
        
        :param station_id: Unique string identifier from transit API
        :return: Dictionary containing favorite data, or None
        """
        try:
            conn = get_db_connection()
            row = conn.execute("SELECT * FROM favorites WHERE station_id = ?", (station_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting favorite by station_id {station_id}: {e}")
            return None

    @staticmethod
    def delete(fav_db_id):
        """
        Remove a favorite by its database ID.
        
        :param fav_db_id: Database auto-increment ID
        :return: True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            conn.execute("DELETE FROM favorites WHERE id = ?", (fav_db_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting favorite {fav_db_id}: {e}")
            return False

    @staticmethod
    def delete_by_station_id(station_id):
        """
        Remove a favorite by its station_id string.
        
        :param station_id: Unique string identifier from transit API
        :return: True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            conn.execute("DELETE FROM favorites WHERE station_id = ?", (station_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting favorite by station_id {station_id}: {e}")
            return False
