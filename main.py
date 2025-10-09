from db import Database
from tkinter import messagebox


class HotelBackend:
    def __init__(self):
        self.db = Database()

        # Load initial data
        self.rooms = {}
        self.services = {}
        self._initial_db_load()

        # Reservation state memory
        self.pending = {
            "name": None,
            "phone": None,
            "nights": None,
            "room": None,
            "services": [],
            "payment": None,
            "total": 0.0
        }

    # ---------- Initial Data Load ----------
    def _initial_db_load(self):
        """Load rooms and services at startup"""
        try:
            conn, err = self.db.try_connect_silent()
            if conn:
                conn.close()
                self.rooms = self.db.load_rooms()
                self.services = self.db.load_services()
            else:
                self.rooms, self.services = {}, {}
        except Exception as e:
            print(f"Error during DB load: {e}")
            self.rooms, self.services = {}, {}

    # ---------- Validation ----------
    def validate_phone_number(self, phone):
        """Ensure phone number has exactly 11 digits"""
        try:
            cleaned = phone.replace('-', '').replace(' ', '').replace('+', '')
            if len(cleaned) == 11 and cleaned.isdigit():
                return True, cleaned
            return False, None
        except Exception:
            return False, None

    def validate_nights(self, nights):
        """Ensure nights input is a positive number"""
        try:
            if not nights.isdigit() or int(nights) <= 0:
                return False
            return True
        except Exception:
            return False

    # ---------- Reservation Logic ----------
    def start_reservation(self, name, phone, nights):
        """Store guest info before choosing room"""
        is_valid, cleaned_phone = self.validate_phone_number(phone)
        if not is_valid:
            messagebox.showwarning("Invalid Phone", "Phone number must have 11 digits.")
            return False

        if not self.validate_nights(nights):
            messagebox.showwarning("Invalid Nights", "Number of nights must be positive.")
            return False

        self.pending["name"] = name
        self.pending["phone"] = cleaned_phone
        self.pending["nights"] = int(nights)
        self.pending["room"] = None
        self.pending["services"] = []
        self.pending["payment"] = None
        self.pending["total"] = 0.0
        return True

    def compute_total(self, room, selected_services):
        """Compute total cost based on room, nights, and services"""
        try:
            nights = self.pending.get("nights", 1)
            room_cost = self.rooms[room]["price"] * nights
            service_cost = sum(self.services[s] for s in selected_services) if selected_services else 0.0
            total = room_cost + service_cost
            self.pending["room"] = room
            self.pending["services"] = selected_services
            self.pending["total"] = total
            return total
        except Exception as e:
            print(f"Error computing total: {e}")
            return 0.0

    def set_payment_method(self, method):
        """Set payment method for current reservation"""
        try:
            self.pending["payment"] = method
        except Exception as e:
            print(f"Error setting payment: {e}")

    def finalize_reservation(self):
        """Save reservation to database"""
        try:
            data = self.pending
            if data["room"] not in self.rooms or self.rooms[data["room"]]["available"] <= 0:
                messagebox.showerror("Unavailable", "This room type is no longer available.")
                return False

            success = self.db.add_reservation(
                self.rooms,
                data["name"],
                data["phone"],
                data["room"],
                data["nights"],
                data["services"],
                data["total"],
                data["payment"]
            )

            if success:
                self.rooms = self.db.load_rooms()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error finalizing reservation: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            return False

    def reset_pending(self):
        """Clear current pending data"""
        self.pending = {
            "name": None,
            "phone": None,
            "nights": None,
            "room": None,
            "services": [],
            "payment": None,
            "total": 0.0
        }

    # ---------- Staff Operations ----------
    def fetch_all_reservations(self):
        """Return all reservations for staff view"""
        try:
            return self.db.get_reservations()
        except Exception as e:
            print(f"Error fetching reservations: {e}")
            return []

    def search_reservations(self, query):
        """Search reservations by guest name or phone"""
        try:
            return self.db.get_reservations_filtered(query)
        except Exception as e:
            print(f"Error searching reservations: {e}")
            return []

    def delete_reservation(self, res_id):
        """Remove a reservation and restore room availability"""
        try:
            return self.db.delete_reservation(res_id)
        except Exception as e:
            print(f"Error deleting reservation: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            return False
