import sqlite3
from werkzeug.security import check_password_hash
from config import Config

class AuthService:
    """Service for handling user authentication logic."""

    @staticmethod
    def authenticate_user(username, password, selected_role):
        """
        Validate user credentials and role against the authentication database.
        Returns a tuple (success, message, user_id, role).
        """
        db_path = Config.AUTH_DB_PATH
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find all entries for the username
            cursor.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,))
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                return False, "Invalid username or password.", None, None
                
            # 1. Check for Admin override (if any entry for this username is admin)
            for user in users:
                if user['role'] == 'admin':
                    if check_password_hash(user['password_hash'], password):
                        return True, "Admin authentication successful.", user['id'], 'admin'
                    else:
                        # If matches admin username but wrong password, fail early
                        return False, "Invalid username or password.", None, None

            # 2. Check for matching selected_role
            for user in users:
                if user['role'] == selected_role:
                    if check_password_hash(user['password_hash'], password):
                        return True, "Authentication successful.", user['id'], selected_role
                    else:
                        return False, "Invalid username or password.", None, None
            
            # If username exists but role doesn't match and no admin override
            return False, f"User is not authorized as {selected_role}.", None, None
                
        except Exception as e:
            print(f"Auth Service Error: {e}")
            return False, "An error occurred during authentication.", None, None

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Validate current password and update to new password.
        Returns a tuple (success, message).
        """
        from werkzeug.security import generate_password_hash
        db_path = Config.AUTH_DB_PATH
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch user details by ID
            cursor.execute('SELECT username, password_hash FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "User not found."
                
            # Verify current password
            if not check_password_hash(user['password_hash'], current_password):
                conn.close()
                return False, "Incorrect current password."
                
            # Hash new password
            new_hash = generate_password_hash(new_password)
            
            # Update password
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
            conn.commit()
            conn.close()
            
            return True, "Password changed successfully."
            
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return False, "Database error occurred."
        except Exception as e:
            print(f"Auth Service Error: {e}")
            return False, "An error occurred while changing password."
