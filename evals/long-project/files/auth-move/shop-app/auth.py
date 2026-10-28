# Demo material: the shop's own sign-in.
import bcrypt

def check_login(db, email, password):
    row = db.execute("SELECT password_hash, role FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    if bcrypt.checkpw(password.encode(), row[0]):
        return row[1]  # "customer" or "staff"
    return None
