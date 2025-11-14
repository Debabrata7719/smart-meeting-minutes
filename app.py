import streamlit as st
import json, os
from firebase_admin import credentials, auth, firestore
import firebase_admin
import requests
import zipfile

st.set_page_config(page_title="Smart Meeting Minutes", page_icon="🎤")

# The model extracts to "vosk-model-small-en-us-0.15" not "vosk"
MODEL_DIR = "models/vosk-model-small-en-us-0.15"

# Check if model needs to be downloaded (only show message, don't block)
if not os.path.exists(MODEL_DIR):
    # Check if download is in progress
    if "model_downloading" not in st.session_state:
        st.session_state["model_downloading"] = True
        try:
            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            zip_path = "vosk.zip"
            
            # Create models directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            # Download the model
            with st.spinner("Downloading Vosk model (this may take a moment)..."):
                response = requests.get(url, timeout=60)
                response.raise_for_status()  # Raise an error for bad status codes
                
                # Write the zip file
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                
                # Verify the file exists and has content
                if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                    raise FileNotFoundError(f"Downloaded file {zip_path} is missing or empty")
                
                # Extract the zip file
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall("models/")
                
                # Clean up
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            
            # Verify extraction worked - check for the actual extracted folder name
            if os.path.exists(MODEL_DIR):
                st.session_state["model_downloading"] = False
                st.success("✅ Vosk model downloaded successfully!")
            else:
                # Check if any model folder was created
                model_folders = [d for d in os.listdir("models") if os.path.isdir(os.path.join("models", d)) and "vosk" in d.lower()]
                if model_folders:
                    st.session_state["model_downloading"] = False
                    st.success(f"✅ Vosk model downloaded successfully! (found in {model_folders[0]})")
                else:
                    raise FileNotFoundError("Model directory was not created after extraction")
                
        except Exception as e:
            st.session_state["model_downloading"] = False
            st.warning(f"⚠️ Could not download Vosk model: {e}")
            st.info("ℹ️ The app will continue, but transcription features may not work until the model is downloaded.")
            # Don't stop the app, just continue without the model

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
    # Check for token in query parameters
    if "id_token" in st.query_params:
        token = st.query_params["id_token"]
        try:
            user = auth.verify_id_token(token)
            st.session_state["user"] = user
            # Clear the token from URL by setting it to empty
            # This prevents the token from appearing in the URL
            st.query_params["id_token"] = ""
            # Remove it completely if possible
            try:
                # Try to remove the parameter (works in newer Streamlit versions)
                params_dict = dict(st.query_params)
                params_dict.pop("id_token", None)
                st.query_params.clear()
                for k, v in params_dict.items():
                    if v:  # Only add non-empty params
                        st.query_params[k] = v
            except:
                # Fallback: just set to empty string
                pass
            st.rerun()
        except Exception as e:
            st.error(f"Token verification failed: {str(e)}")
            st.session_state["user"] = None

# -----------------------------
# 5. GOOGLE LOGIN COMPONENT
# -----------------------------
def google_login_button():
    # Inject Firebase scripts and auth logic directly into the page (not in iframe)
    firebase_config_json = json.dumps(firebase_config)
    
    # Always load scripts and handle redirect - this ensures it works on every page load
    st.markdown(f"""
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    <script>
        (function() {{
            // Wait for Firebase to load
            function initFirebase() {{
                if (typeof firebase === 'undefined') {{
                    setTimeout(initFirebase, 100);
                    return;
                }}
                
                const firebaseConfig = {firebase_config_json};
                
                // Initialize Firebase only if not already initialized
                if (!firebase.apps.length) {{
                    firebase.initializeApp(firebaseConfig);
                }}
                
                const auth = firebase.auth();
                
                // Handle redirect result on EVERY page load (critical for redirect flow)
                auth.getRedirectResult()
                    .then(async (result) => {{
                        console.log('Redirect result:', result);
                        if (result.user) {{
                            console.log('User authenticated:', result.user.email);
                            const token = await result.user.getIdToken();
                            console.log('Got token, redirecting...');
                            
                            // Add token to URL and reload
                            const currentUrl = new URL(window.location.href);
                            currentUrl.searchParams.set('id_token', token);
                            window.location.href = currentUrl.toString();
                        }} else {{
                            console.log('No user in redirect result');
                        }}
                    }})
                    .catch((error) => {{
                        console.error("Redirect result error:", error);
                        // Don't show alert for expected errors
                        if (error.code && !['auth/popup-closed-by-user', 'auth/cancelled-popup-request'].includes(error.code)) {{
                            console.error("Unexpected auth error:", error);
                        }}
                    }});
            }}
            
            // Start initialization
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', initFirebase);
            }} else {{
                initFirebase();
            }}
        }})();
    </script>
    """, unsafe_allow_html=True)
    
    # Create the login button
    st.markdown("""
    <style>
        .google-login-btn {
            padding: 15px 25px;
            font-size: 20px;
            border: none;
            background: #4285F4;
            color: white;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 300px;
            margin: 10px 0;
        }
        .google-login-btn:hover {
            background: #357ae8;
        }
    </style>
    <button id="googleLoginBtn" class="google-login-btn">
        🔐 Sign in with Google
    </button>
    <script>
        (function() {{
            function setupButton() {{
                const btn = document.getElementById('googleLoginBtn');
                if (!btn) {{
                    setTimeout(setupButton, 100);
                    return;
                }}
                
                // Remove any existing listeners
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
                
                newBtn.addEventListener('click', function() {{
                    if (typeof firebase === 'undefined') {{
                        alert('Firebase is loading, please wait a moment and try again.');
                        return;
                    }}
                    
                    console.log('Login button clicked, initiating redirect...');
                    const provider = new firebase.auth.GoogleAuthProvider();
                    firebase.auth().signInWithRedirect(provider)
                        .then(() => {{
                            console.log('Redirect initiated');
                        }})
                        .catch((error) => {{
                            console.error("Redirect error:", error);
                            alert("Login failed: " + error.message);
                        }});
                }});
            }}
            
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', setupButton);
            }} else {{
                setupButton();
            }}
        }})();
    </script>
    """, unsafe_allow_html=True)

# -----------------------------
# 6. LOGOUT FUNCTION
# -----------------------------
def logout():
    st.session_state["user"] = None
    # Clear all query parameters
    params = dict(st.query_params)
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
    
    # Show helpful information
    with st.expander("ℹ️ Login Instructions"):
        st.write("""
        1. Click the "Sign in with Google" button below
        2. You will be redirected to Google for authentication
        3. Complete the Google sign-in process
        4. You will be redirected back to the app automatically
        
        **Note:** Make sure your Streamlit app URL is added to Firebase Authorized domains
        (Firebase Console → Authentication → Settings → Authorized domains)
        """)
    
    google_login_button()
    
    # Debug info (can be removed in production)
    if st.checkbox("Show debug info"):
        st.write("**Query params:**", dict(st.query_params))
        st.write("**Session state keys:**", list(st.session_state.keys()))
        st.write("**Current URL:**", st.get_option("server.headless"))
        
        st.markdown("""
        <script>
            console.log('Current URL:', window.location.href);
            console.log('Query params:', new URLSearchParams(window.location.search).toString());
        </script>
        """, unsafe_allow_html=True)
        
        st.info("""
        **Troubleshooting:**
        - Check browser console (F12) for Firebase logs
        - Make sure your Streamlit URL is in Firebase Authorized domains
        - Verify Google Sign-In is enabled in Firebase Console
        - Check that redirect URIs are configured correctly
        """)
    
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