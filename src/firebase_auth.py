import hashlib
import os
import firebase_admin
from firebase_admin import credentials, firestore

# ─── INIT FIREBASE ───────────────────────────────────────────────────────────
def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# ─── HASH PASSWORD ───────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── REGISTER USER ───────────────────────────────────────────────────────────
def register_user(full_name, email, username, password):
    # Validate inputs
    if not full_name.strip():
        return False, "Please enter your full name!"
    if len(username) < 3:
        return False, "Username must be at least 3 characters!"
    if len(password) < 6:
        return False, "Password must be at least 6 characters!"
    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address!"

    try:
        db = init_firebase()
        users_ref = db.collection("users")

        # Check if username already exists
        existing = users_ref.document(username).get()
        if existing.exists:
            return False, "Username already taken! Please choose another."

        # Check if email already registered
        email_check = users_ref.where("email", "==", email.lower().strip()).get()
        if len(list(email_check)) > 0:
            return False, "Email already registered! Please login."

        # Save user to Firestore
        users_ref.document(username).set({
            "full_name": full_name.strip(),
            "email": email.lower().strip(),
            "username": username.strip(),
            "password": hash_password(password),
            "role": "student",
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "Registration successful! Please login."

    except Exception as e:
        return False, f"Error: {str(e)}"

# ─── LOGIN USER ──────────────────────────────────────────────────────────────
def login_user(username, password):
    if not username.strip() or not password.strip():
        return False, "Please fill in all fields!", None

    try:
        db = init_firebase()
        user_doc = db.collection("users").document(username.strip()).get()

        if not user_doc.exists:
            return False, "Username not found! Please register first.", None

        user_data = user_doc.to_dict()

        if user_data["password"] != hash_password(password):
            return False, "Wrong password! Please try again.", None

        return True, user_data["full_name"], user_data

    except Exception as e:
        return False, f"Error: {str(e)}", None
