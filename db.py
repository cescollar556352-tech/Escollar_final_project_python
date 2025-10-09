import mysql.connector
from tkinter import messagebox


class Database:
    def __init__(self):
        # ✅ MySQL configuration (edit if needed)
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "hotel_reservation_system"
        }

    # ---------- Connection ----------
    def connect(self):
        """Establish MySQL connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Connection failed: {str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("Database Error", f"Unexpected error: {str(e)}")
            return None

    def try_connect_silent(self):
        """Try to connect without pop-up messages"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn, None
        except mysql.connector.Error as e:
            return None, str(e)
        except Exception as e:
            return None, str(e)

    # ---------- Loaders ----------
    def load_rooms(self):
        """Load all room records"""
        conn = self.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rooms")
            rows = cursor.fetchall()
            result = {}
            for r in rows:
                room_type = r.get('room_type')
                result[room_type] = {
                    'id': r.get('room_id'),
                    'price': float(r.get('price')) if r.get('price') else 0.0,
                    'available': int(r.get('available')) if r.get('available') else 0
                }
            return result
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load rooms: {str(e)}")
            return {}
        finally:
            conn.close()

    def load_services(self):
        """Load all services"""
        conn = self.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM services")
            rows = cursor.fetchall()
            result = {}
            for s in rows:
                result[s.get('name')] = float(s.get('price')) if s.get('price') else 0.0
            return result
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load services: {str(e)}")
            return {}
        finally:
            conn.close()

    # ---------- Reservations ----------
    def add_reservation(self, rooms, name, phone, room, nights, services, total, payment):
        """Insert a new reservation"""
        conn = self.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            # Add guest info
            cursor.execute("INSERT INTO guests (name, phone) VALUES (%s, %s)", (name, phone))
            guest_id = cursor.lastrowid
            # Add reservation
            cursor.execute(
                """INSERT INTO reservations (guest_id, room_id, nights, services, total, payment)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (guest_id, rooms[room]['id'], nights, ",".join(services), total, payment)
            )
            # Update availability
            cursor.execute("UPDATE rooms SET available = available - 1 WHERE room_id = %s", (rooms[room]['id'],))
            conn.commit()
            return True
        except mysql.connector.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Failed to add reservation: {str(e)}")
            return False
        finally:
            conn.close()

    def get_reservations(self):
        """Retrieve all reservations"""
        conn = self.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.reservation_id, g.name, g.phone, rm.room_type, 
                       r.nights, r.services, r.total, r.payment
                FROM reservations r
                LEFT JOIN guests g ON r.guest_id = g.guest_id
                LEFT JOIN rooms rm ON r.room_id = rm.room_id
                ORDER BY r.created_at DESC
            """)
            return cursor.fetchall()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to retrieve reservations: {str(e)}")
            return []
        finally:
            conn.close()

    def get_reservations_filtered(self, query_text):
        """Search reservations by guest name or phone"""
        conn = self.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            like_q = f"%{query_text}%"
            cursor.execute("""
                SELECT r.reservation_id, g.name, g.phone, rm.room_type, 
                       r.nights, r.services, r.total, r.payment
                FROM reservations r
                LEFT JOIN guests g ON r.guest_id = g.guest_id
                LEFT JOIN rooms rm ON r.room_id = rm.room_id
                WHERE g.name LIKE %s OR g.phone LIKE %s
                ORDER BY r.created_at DESC
            """, (like_q, like_q))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Search failed: {str(e)}")
            return []
        finally:
            conn.close()

    def delete_reservation(self, res_id):
        """Delete reservation and restore room availability"""
        conn = self.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT room_id FROM reservations WHERE reservation_id = %s", (res_id,))
            row = cursor.fetchone()
            if row and row[0]:
                cursor.execute("UPDATE rooms SET available = available + 1 WHERE room_id = %s", (row[0],))
            cursor.execute("DELETE FROM reservations WHERE reservation_id = %s", (res_id,))
            conn.commit()
            return True
        except mysql.connector.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Failed to delete reservation: {str(e)}")
            return False
        finally:
            conn.close()
