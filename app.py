import streamlit as st
import json, os
from firebase_admin import credentials, auth, firestore
import firebase_admin
import os
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
# 3. GOOGLE LOGIN HTML
# -----------------------------
def google_login_button():
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    """, unsafe_allow_html=True)

    login_html = f"""
        <script>
            const firebaseConfig = {json.dumps(firebase_config)};
            if (!firebase.apps.length) {{
                firebase.initializeApp(firebaseConfig);
            }}
            const auth = firebase.auth();

            function googleLogin() {{
                const provider = new firebase.auth.GoogleAuthProvider();
                auth.signInWithPopup(provider).then(async (result) => {{
                    const token = await result.user.getIdToken();
                    const params = new URLSearchParams();
                    params.set("id_token", token);

                    // Redirect properly on Streamlit
                    window.location.href = window.location.origin + "/?" + params.toString();
                }}).catch((err) => {{
                    alert("Login failed: " + err.message);
                }});
            }}
        </script>

        <button onclick="googleLogin()"
            style="padding:15px 25px;font-size:20px;border:none;background:#4285F4;color:white;border-radius:8px;cursor:pointer;">
            🔐 Sign in with Google
        </button>
    """
    st.markdown(login_html, unsafe_allow_html=True)

# -----------------------------
# 4. VERIFY LOGIN TOKEN
# -----------------------------
def verify_token():
    query = st.experimental_get_query_params()

    if "id_token" in query:
        token = query["id_token"][0]
        try:
            user = auth.verify_id_token(token)
            return user
        except Exception as e:
            st.error("Token verification failed: " + str(e))
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
