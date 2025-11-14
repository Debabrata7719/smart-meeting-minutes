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
    # Use st.components.v1.html which actually executes JavaScript
    # Access parent window to avoid iframe restrictions
    firebase_config_json = json.dumps(firebase_config)
    
    # Combined HTML with Firebase and button
    combined_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    </head>
    <body>
        <button id="googleLoginBtn" style="padding:15px 25px;font-size:20px;border:none;background:#4285F4;color:white;border-radius:8px;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,0.2);width:100%;max-width:300px;">
            🔐 Sign in with Google
        </button>
        
        <script>
            console.log('=== FIREBASE AUTH SCRIPT STARTING (in component) ===');
            
            // Try to access parent window, fallback to current window
            const targetWindow = window.top !== window ? window.top : window;
            const targetDoc = targetWindow.document;
            
            const firebaseConfig = {firebase_config_json};
            
            // Initialize Firebase in target window
            function initFirebase() {{
                try {{
                    if (!targetWindow.firebase || !targetWindow.firebase.apps.length) {{
                        console.log('Initializing Firebase in target window...');
                        if (!targetWindow.firebase) {{
                            // Load scripts in parent if needed
                            const script1 = targetDoc.createElement('script');
                            script1.src = 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js';
                            script1.onload = function() {{
                                const script2 = targetDoc.createElement('script');
                                script2.src = 'https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js';
                                script2.onload = function() {{
                                    targetWindow.firebase.initializeApp(firebaseConfig);
                                    setupAuth();
                                }};
                                targetDoc.head.appendChild(script2);
                            }};
                            targetDoc.head.appendChild(script1);
                        }} else {{
                            targetWindow.firebase.initializeApp(firebaseConfig);
                            setupAuth();
                        }}
                    }} else {{
                        console.log('Firebase already initialized');
                        setupAuth();
                    }}
                }} catch (e) {{
                    console.error('Error initializing Firebase:', e);
                    // Fallback: use current window
                    if (!firebase.apps.length) {{
                        firebase.initializeApp(firebaseConfig);
                    }}
                    setupAuthCurrent();
                }}
            }}
            
            function setupAuth() {{
                const auth = targetWindow.firebase.auth();
                
                // Handle redirect result
                auth.getRedirectResult()
                    .then(async (result) => {{
                        console.log('Redirect result:', result);
                        if (result.user) {{
                            const token = await result.user.getIdToken();
                            const currentUrl = new URL(targetWindow.location.href);
                            currentUrl.searchParams.set('id_token', token);
                            targetWindow.location.href = currentUrl.toString();
                        }}
                    }})
                    .catch((error) => {{
                        if (error.code && !['auth/popup-closed-by-user'].includes(error.code)) {{
                            console.error('Redirect result error:', error);
                        }}
                    }});
                
                // Setup button
                document.getElementById('googleLoginBtn').addEventListener('click', function() {{
                    const provider = new targetWindow.firebase.auth.GoogleAuthProvider();
                    auth.signInWithRedirect(provider)
                        .catch((error) => {{
                            console.error('Redirect error:', error);
                            alert('Login failed: ' + error.message);
                        }});
                }});
            }}
            
            function setupAuthCurrent() {{
                const auth = firebase.auth();
                
                auth.getRedirectResult()
                    .then(async (result) => {{
                        if (result.user) {{
                            const token = await result.user.getIdToken();
                            const currentUrl = new URL(window.location.href);
                            currentUrl.searchParams.set('id_token', token);
                            window.top.location.href = currentUrl.toString();
                        }}
                    }})
                    .catch((error) => {{
                        if (error.code && !['auth/popup-closed-by-user'].includes(error.code)) {{
                            console.error('Redirect result error:', error);
                        }}
                    }});
                
                document.getElementById('googleLoginBtn').addEventListener('click', function() {{
                    const provider = new firebase.auth.GoogleAuthProvider();
                    auth.signInWithRedirect(provider)
                        .catch((error) => {{
                            console.error('Redirect error:', error);
                            alert('Login failed: ' + error.message);
                        }});
                }});
            }}
            
            // Wait for Firebase to load, then initialize
            if (typeof firebase !== 'undefined') {{
                initFirebase();
            }} else {{
                window.addEventListener('load', function() {{
                    setTimeout(initFirebase, 500);
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    # Use components.v1.html which actually executes JavaScript
    st.components.v1.html(combined_html, height=100)

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
    
    # Firebase Configuration Checker
    st.markdown("---")
    st.subheader("🔧 Firebase Configuration Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Firebase Config:**")
        st.code(f"""
        Project ID: {firebase_config['projectId']}
        Auth Domain: {firebase_config['authDomain']}
        """)
    
    with col2:
        st.write("**Required Setup:**")
        st.markdown("""
        1. ✅ Go to [Firebase Console](https://console.firebase.google.com/)
        2. ✅ Select project: **landing-page-for-meeting-app**
        3. ✅ Authentication → Settings → Authorized domains
        4. ✅ Add: **smart-meeting-minutes.streamlit.app**
        5. ✅ Authentication → Sign-in method → Enable Google
        """)
    
    # Quick test link
    st.info("""
    **Quick Test:** If login still doesn't work, try this:
    1. Open browser console (F12) before clicking login
    2. Look for any red error messages
    3. Check if you see "=== FIREBASE AUTH SCRIPT STARTING ===" in console
    4. If you don't see Firebase logs, the scripts aren't loading
    """)
    
    # Simple JavaScript test
    st.markdown("""
    <div id="js-test" style="padding:10px;background:#e8f5e9;border-radius:5px;margin:10px 0;">
        <strong>JavaScript Test:</strong> <span id="js-result">Testing...</span>
    </div>
    <script>
        document.getElementById('js-result').textContent = '✅ JavaScript is working!';
        console.log('✅ JavaScript test passed - scripts are executing');
    </script>
    """, unsafe_allow_html=True)
    
    google_login_button()
    
    # Debug info (can be removed in production)
    if st.checkbox("Show debug info"):
        st.write("**Query params:**", dict(st.query_params))
        st.write("**Session state keys:**", list(st.session_state.keys()))
        
        # Show current URL info
        st.markdown("""
        <div id="url-info"></div>
        <script>
            const urlInfo = document.getElementById('url-info');
            const currentUrl = window.location.href;
            const urlParams = new URLSearchParams(window.location.search);
            urlInfo.innerHTML = '<p><strong>Current URL:</strong> ' + currentUrl + '</p>' +
                               '<p><strong>URL Params:</strong> ' + urlParams.toString() + '</p>';
            console.log('Current URL:', currentUrl);
            console.log('Query params:', urlParams.toString());
            
            // Check if Firebase is loaded
            setTimeout(function() {
                if (typeof firebase !== 'undefined') {
                    console.log('Firebase is loaded');
                    urlInfo.innerHTML += '<p style="color: green;"><strong>Firebase Status:</strong> Loaded ✓</p>';
                } else {
                    console.log('Firebase is NOT loaded');
                    urlInfo.innerHTML += '<p style="color: red;"><strong>Firebase Status:</strong> Not loaded ✗</p>';
                }
            }, 1000);
        </script>
        """, unsafe_allow_html=True)
        
        st.info("""
        **Troubleshooting Steps:**
        
        1. **Open Browser Console (F12)** and look for:
           - "Firebase scripts loading..."
           - "Checking for redirect result..."
           - Any error messages
        
        2. **Firebase Configuration:**
           - Go to Firebase Console → Authentication → Settings
           - Under "Authorized domains", add: `smart-meeting-minutes.streamlit.app`
           - Under "Sign-in method", enable Google
        
        3. **After clicking login:**
           - You should be redirected to Google
           - After signing in, you should be redirected back
           - Check console for "Redirect result received"
        
        4. **If redirect doesn't work:**
           - Check browser console for errors
           - Verify your Streamlit URL matches Firebase authorized domains
           - Try clearing browser cache and cookies
        """)
        
        # Add a test button to check Firebase
        st.markdown("""
        <button id="testFirebase" style="padding:10px;background:#f0f0f0;border:1px solid #ccc;border-radius:4px;cursor:pointer;margin:5px;">
            Test Firebase Connection
        </button>
        <div id="testResult" style="margin:10px 0;"></div>
        <script>
            document.getElementById('testFirebase').addEventListener('click', function() {
                const resultDiv = document.getElementById('testResult');
                resultDiv.innerHTML = '<p>Testing Firebase...</p>';
                
                setTimeout(function() {
                    if (typeof firebase === 'undefined') {
                        resultDiv.innerHTML = '<p style="color: red;">❌ Firebase is not loaded</p>' +
                            '<p>Make sure scripts are loading. Check browser console (F12) for errors.</p>';
                    } else {
                        try {
                            const auth = firebase.auth();
                            const config = firebase.app().options;
                            resultDiv.innerHTML = '<p style="color: green;">✅ Firebase is loaded and ready</p>' +
                                '<p><strong>Auth Domain:</strong> ' + config.authDomain + '</p>' +
                                '<p><strong>Project ID:</strong> ' + config.projectId + '</p>';
                            console.log('Firebase auth object:', auth);
                            console.log('Firebase config:', config);
                        } catch (e) {
                            resultDiv.innerHTML = '<p style="color: orange;">⚠️ Firebase loaded but error: ' + e.message + '</p>';
                        }
                    }
                }, 500);
            });
            
            // Log all console messages to help debug
            const originalLog = console.log;
            const originalError = console.error;
            const logs = [];
            
            console.log = function(...args) {
                logs.push({type: 'log', message: args.join(' '), time: new Date().toISOString()});
                originalLog.apply(console, args);
            };
            
            console.error = function(...args) {
                logs.push({type: 'error', message: args.join(' '), time: new Date().toISOString()});
                originalError.apply(console, args);
            };
            
            // Store logs in window for debugging
            window.firebaseLogs = logs;
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.warning("""
        **🔍 Important: Check Browser Console**
        
        Please open your browser's Developer Tools (press F12) and check the Console tab for:
        - Any error messages (in red)
        - Firebase loading messages
        - Redirect result messages
        
        **Common Issues:**
        - If you see "auth/unauthorized-domain": Your Streamlit URL is not in Firebase authorized domains
        - If you see "auth/operation-not-allowed": Google Sign-In is not enabled in Firebase
        - If you see no redirect result: The redirect URL might not be configured correctly
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