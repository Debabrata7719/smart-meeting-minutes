import streamlit as st
import json, os
from firebase_admin import credentials, auth, firestore
import firebase_admin
import requests
import zipfile

st.set_page_config(page_title="Smart Meeting Minutes", page_icon="🎤")

MODEL_DIR = "models/vosk"

if not os.path.exists(MODEL_DIR):
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = "vosk.zip"

    with open(zip_path, "wb") as f:
        f.write(requests.get(url).content)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("models/")

    os.remove(zip_path)

# -----------------------------
# 1. LOAD FIREBASE ADMIN JSON
# -----------------------------
if "firebase_initialized" not in st.session_state:
    try:
        firebase_json = st.secrets["FIREBASE_ADMIN_JSON_CONTENT"]
        firebase_dict = json.loads(firebase_json)

        cred = credentials.Certificate(firebase_dict)

        # Prevent double initialization
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        st.session_state["db"] = firestore.client()
        st.session_state["firebase_initialized"] = True

    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        st.stop()


db = st.session_state["db"]

# -----------------------------
# 2. FIREBASE WEB CONFIG
# -----------------------------
firebase_config = {
  "apiKey": "AIzaSyBJMdYT2tL66Q23lhyQroYUPMlIAuUdKX8",
  "authDomain": "landing-page-for-meeting-app.firebaseapp.com",
  "projectId": "landing-page-for-meeting-app",
  "storageBucket": "landing-page-for-meeting-app.firebasestorage.app",
  "messagingSenderId": "802600624072",
  "appId": "1:802600624072:web:8b750e4a032df825d2aafd"
}

# -----------------------------
# 3. INITIALIZE SESSION STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# -----------------------------
# 4. VERIFY LOGIN TOKEN
# -----------------------------
def verify_token():
    # Use the new query_params method
    query = st.query_params
    
    if "id_token" in query:
        token = query["id_token"]
        try:
            user = auth.verify_id_token(token)
            st.session_state["user"] = user
            # Clear the token from URL
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Token verification failed: {str(e)}")
            st.session_state["user"] = None

# -----------------------------
# 5. GOOGLE LOGIN COMPONENT
# -----------------------------
def google_login_button():
    # Load Firebase scripts in the head only once
    if "firebase_loaded" not in st.session_state:
        st.session_state["firebase_loaded"] = True
    
    login_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    </head>
    <body>
        <button id="googleLoginBtn"
            style="padding:15px 25px;font-size:20px;border:none;background:#4285F4;color:white;border-radius:8px;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,0.2);">
            🔐 Sign in with Google
        </button>

        <script>
            const firebaseConfig = {json.dumps(firebase_config)};
            
            // Initialize Firebase only if not already initialized
            if (!firebase.apps.length) {{
                firebase.initializeApp(firebaseConfig);
            }}
            
            const auth = firebase.auth();

            document.getElementById('googleLoginBtn').addEventListener('click', function() {{
                const provider = new firebase.auth.GoogleAuthProvider();
                
                auth.signInWithPopup(provider)
                    .then(async (result) => {{
                        const token = await result.user.getIdToken();
                        
                        // Redirect with token
                        const currentUrl = new URL(window.location.href);
                        currentUrl.searchParams.set('id_token', token);
                        window.location.href = currentUrl.toString();
                    }})
                    .catch((error) => {{
                        console.error("Login error:", error);
                        alert("Login failed: " + error.message);
                    }});
            }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(login_html, height=100)

# -----------------------------
# 6. LOGOUT FUNCTION
# -----------------------------
def logout():
    st.session_state["user"] = None
    st.query_params.clear()
    st.rerun()

# -----------------------------
# 7. MAIN LOGIC
# -----------------------------

# Check for token in URL on page load
verify_token()

# Check if user is logged in
if st.session_state["user"] is None:
    st.title("🔐 Login Required")
    st.write("Please sign in to use Smart Meeting Minutes.")
    google_login_button()
    st.stop()

# If logged in:
user = st.session_state["user"]

st.success(f"Welcome {user.get('email')} 👋")

# Logout button
if st.button("🚪 Logout"):
    logout()

# Example Home Page
st.header("🎤 Smart Meeting Minutes – Logged in")
st.write("You are now authenticated with Google & Firebase!")

st.write("Now you can continue building your actual features (upload video, summarize, etc.) here.")

# Display user info
with st.expander("👤 User Details"):
    st.json(user)