import streamlit as st
import json, os
from firebase_admin import credentials, auth, firestore
import firebase_admin

st.set_page_config(page_title="Smart Meeting Minutes", page_icon="🎤")

# -----------------------------
# 1. LOAD FIREBASE ADMIN JSON
# -----------------------------
if "firebase_initialized" not in st.session_state:
    if "FIREBASE_ADMIN_JSON_CONTENT" in st.secrets:
        firebase_key = st.secrets["FIREBASE_ADMIN_JSON_CONTENT"]
        cred = credentials.Certificate(json.loads(firebase_key))
        firebase_admin.initialize_app(cred)
        st.session_state["db"] = firestore.client()
        st.session_state["firebase_initialized"] = True
    else:
        st.error("Firebase secret missing! Add your JSON in Streamlit Secrets.")
        st.stop()

db = st.session_state["db"]

# -----------------------------
# 2. FIREBASE WEB CONFIG (Your values)
# -----------------------------
firebase_config = {
  "apiKey": "AIzaSyBJMdYT2tL66Q23lhyQroYUPMlIAuUdKX8",
  "authDomain": "landing-page-for-meeting-app.firebaseapp.com",
  "projectId": "landing-page-for-meeting-app",
  "storageBucket": "landing-page-for-meeting-app.firebasestorage.app",
  "messagingSenderId": "802600624072",
  "appId": "1:802600624072:web:8b750e4a032df825d2aafd"
}

APP_URL = "https://smart-meeting-minutes.streamlit.app/"

# -----------------------------
# 3. GOOGLE LOGIN HTML
# -----------------------------
def google_login_button():
    login_html = f"""
    <html>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>

        <script>
            const firebaseConfig = {json.dumps(firebase_config)};
            firebase.initializeApp(firebaseConfig);
            const auth = firebase.auth();

            function googleLogin() {{
                const provider = new firebase.auth.GoogleAuthProvider();
                auth.signInWithPopup(provider).then(async (result) => {{
                    const token = await result.user.getIdToken();
                    const params = new URLSearchParams();
                    params.set("id_token", token);
                    window.location.href = "{APP_URL}?" + params.toString();
                }});
            }}
        </script>

        <button
            onclick="googleLogin()"
            style="padding:15px 25px;font-size:20px;border:none;background:#4285F4;color:white;border-radius:8px;cursor:pointer;">
            🔐 Sign in with Google
        </button>
    </html>
    """
    st.markdown(login_html, unsafe_allow_html=True)

# -----------------------------
# 4. VERIFY LOGIN TOKEN
# -----------------------------
def verify_token():
    if "id_token" in st.query_params:
        token = st.query_params["id_token"]
        try:
            user = auth.verify_id_token(token)
            return user
        except:
            return None
    return None

# -----------------------------
# 5. MAIN LOGIC
# -----------------------------
user = verify_token()

if user is None:
    st.title("🔐 Login Required")
    st.write("Please sign in to use Smart Meeting Minutes.")
    google_login_button()
    st.stop()

# If logged in:
st.success(f"Welcome {user.get('email')} 👋")

# Example Home Page
st.header("🎤 Smart Meeting Minutes – Logged in")
st.write("You are now authenticated with Google & Firebase!")

st.write("Now you can continue building your actual features (upload video, summarize, etc.) here.")

