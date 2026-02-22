import streamlit as st
import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SCALEDOWN_API_KEY = os.getenv("SCALEDOWN_API_KEY")
SCALEDOWN_URL = os.getenv("SCALEDOWN_API_URL", "https://api.scaledown.xyz/compress/raw/")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# Load knowledge base files
def load_knowledge_base():
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    lease_text = open(os.path.join(base_dir, 'lease_agreement.txt'), 'r', encoding='utf-8').read()
    policy_text = open(os.path.join(base_dir, 'building_policies.txt'), 'r', encoding='utf-8').read()
    return lease_text, policy_text

lease_text, policy_text = load_knowledge_base()
full_knowledge = f"=== LEASE AGREEMENT ===\n{lease_text}\n\n=== BUILDING POLICIES ===\n{policy_text}"

# Step 1: Use ScaleDown to compress the knowledge base
def compress_knowledge(question):
    headers = {
        "x-api-key": SCALEDOWN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "context": full_knowledge,
        "prompt": question,
        "scaledown": { "rate": "auto" }
    }
    try:
        response = requests.post(SCALEDOWN_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            compressed = result["results"]["compressed_prompt"]
            original_tokens = result["results"].get("original_prompt_tokens", 0)
            compressed_tokens = result["results"].get("compressed_prompt_tokens", 0)
            return compressed, original_tokens, compressed_tokens
    except Exception:
        pass
    return question, 0, 0  # fallback: use original question if compression fails

# Step 2: Use Gemini to answer using compressed context
def get_gemini_answer(question, compressed_context):
    prompt = f"""You are a helpful tenant services assistant for Riverside Apartments.
Use ONLY the information below to answer the tenant's question.
If the answer is not in the information, say: "I don't have that information — please contact leasing at leasing@riversideapts.com or call (512) 847-3300"
Be friendly, concise and professional.

When writing monetary amounts, use the form "USD 500" (the letters USD, a space, then the amount) instead of the dollar sign. The UI will convert this back to a dollar sign for display.

KNOWLEDGE BASE (compressed):
{compressed_context}

TENANT QUESTION: {question}

ANSWER:"""
    try:
        response = gemini_model.generate_content(prompt)
        raw = response.text
        return format_answer(raw)
    except Exception as e:
        return f"Unable to get answer from Gemini: {str(e)}"


def format_answer(text: str) -> str:
    """Post-process Gemini output:
    - Convert 'USD 500' back to '$500'
    - Escape dollar signs so Streamlit does not interpret them as LaTeX
    """
    if not isinstance(text, str):
        return text
    # Replace the temporary USD token back to dollar sign
    out = text.replace("USD ", "$")
    # Escape dollar signs for Streamlit/Markdown rendering
    out = out.replace("$", "\\$")
    return out

# Streamlit UI
st.set_page_config(page_title="Tenant Services Chatbot", layout="wide")

# Theme and fonts
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f14;
    color: #e8eaf0;
}
.stApp { background-color: #0d0f14; }
.stSidebar { background-color: #111318; border-right: 1px solid #252830; }
.stChatMessage { background-color: #161920; border: 1px solid #252830; border-radius: 8px; margin-bottom: 8px; }

/* Sidebar brand/title */
.sidebar-brand {
    color: #f6b26b;
    font-size: 1.12rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    margin: 0.15rem 0 0.55rem 0;
}

/* Sidebar link style (used by buttons visually) */
.sidebar-link {
    display: block;
    color: #a0a6b4;
    font-size: 13px;
    font-weight: 400;
    padding: 6px 0;
    cursor: pointer;
    text-decoration: none;
    transition: color 0.25s ease, padding-left 0.25s ease;
    border: none;
    background: none;
}
.sidebar-link:hover {
    color: #f6b26b;
    padding-left: 6px;
}

/* Make all st.button look like plain text links */
.stButton > button {
    background: none !important;
    border: none !important;
    border-radius: 0 !important;
    color: #a0a6b4 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 5px 0 !important;
    text-align: left !important;
    width: 100% !important;
    transition: color 0.25s ease, padding-left 0.25s ease, background-size 0.3s ease !important;
    box-shadow: none !important;
    background-image: linear-gradient(#f6b26b, #f6b26b) !important;
    background-position: 0 100% !important;
    background-repeat: no-repeat !important;
    background-size: 0% 1px !important;
}
.stButton > button:hover {
    color: #f6b26b !important;
    padding-left: 8px !important;
    background-size: 100% 1px !important;
    border: none !important;
}
.stButton > button:focus {
    box-shadow: none !important;
    border: none !important;
    outline: none !important;
    background-size: 100% 1px !important;
}

/* Sidebar-specific hover color tuning */
section[data-testid="stSidebar"] .stButton > button {
    color: #a0a6b4 !important;
    transition: color 0.3s ease, padding-left 0.25s ease, background-size 0.3s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    color: #f6b26b !important;
}

/* Title and text brightness */
h1 {
    color: #e8eaf0 !important;
    font-weight: 600 !important;
    letter-spacing: -0.5px;
    font-size: 2.2rem !important;
}
h2, h3 {
    color: #d0d4de !important;
    font-weight: 500 !important;
}
p, li, .stMarkdown {
    color: #b8bdc9 !important;
}

/* Replace muted label color */
.metric-label, .metric-sub, .section-header { color: #a0a6b4 !important; }

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #252830;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #a0a6b4;
    font-size: 13px;
    font-weight: 400;
    background: transparent;
    border: none;
    padding: 10px 20px;
    transition: color 0.3s ease, background-size 0.3s ease;
    background-image: linear-gradient(#f6b26b, #f6b26b);
    background-position: 0 100%;
    background-repeat: no-repeat;
    background-size: 0% 1px;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f6b26b;
    background-size: 100% 1px;
}
.stTabs [aria-selected="true"] {
    color: #7a9fd4 !important;
    font-weight: 500 !important;
    border-bottom: 2px solid #7a9fd4 !important;
    transition: border-color 0.35s ease, color 0.35s ease !important;
}

/* Inputs, textareas, selects */
.stTextInput > div > div > input {
    background-color: #161920 !important;
    border: 1px solid #252830 !important;
    color: #e8eaf0 !important;
    border-radius: 6px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4a7fe8 !important;
    box-shadow: none !important;
}
.stTextArea > div > div > textarea {
    background-color: #161920 !important;
    border: 1px solid #252830 !important;
    color: #e8eaf0 !important;
    border-radius: 6px !important;
    resize: vertical;
}
.stTextArea > div > div > textarea:focus {
    border-color: #4a7fe8 !important;
    box-shadow: none !important;
}
.stSelectbox > div > div {
    background-color: #161920 !important;
    border: 1px solid #252830 !important;
    color: #e8eaf0 !important;
    border-radius: 6px !important;
}
.stSelectbox svg { fill: #a0a6b4 !important; }
.stSlider > div > div { background-color: transparent !important; }
.stChatInput > div { background-color: #0f1114 !important; border: 1px solid #1f2226 !important; border-radius: 8px !important; color: #e8eaf0 !important; }
.stChatInput > div:focus-within { border-color: #4a7fe8 !important; }

/* Dataframes */
div[data-testid="stDataFrame"] {
    background-color: rgba(59, 130, 246, 0.08) !important;
    border: 1px solid rgba(125, 171, 245, 0.28) !important;
    border-radius: 10px !important;
    padding: 6px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
}
.stDataFrame { background-color: transparent !important; }
div[data-testid="stDataFrame"] table,
div[data-testid="stDataFrame"] thead,
div[data-testid="stDataFrame"] tbody,
div[data-testid="stDataFrame"] tr {
    background-color: rgba(59, 130, 246, 0.08) !important;
}
div[data-testid="stDataFrame"] th {
    background-color: rgba(59, 130, 246, 0.12) !important;
    color: #dbe8ff !important;
    border-color: rgba(125, 171, 245, 0.22) !important;
}
div[data-testid="stDataFrame"] td {
    background-color: rgba(59, 130, 246, 0.08) !important;
    color: #d9deea !important;
    border-color: rgba(125, 171, 245, 0.16) !important;
}
iframe[title="st_dataframe"] { filter: invert(0) !important; }

.stCheckbox > label { color: #b8bdc9 !important; }
.block-container { background-color: #0d0f14 !important; }
section[data-testid="stSidebar"] { background-color: #111318 !important; }

/* Top header / toolbar */
header, .stHeader, .stTopNav {
    background-color: #0b0d10 !important;
    border-bottom: 1px solid #1b1e22 !important;
}

/* Placeholder */
input::placeholder, textarea::placeholder { color: #555a66 !important; }

/* Metric cards and badges */
.metric-card { background-color: #161920; border: 1px solid #252830; border-radius: 8px; padding: 20px; margin-bottom: 12px; }
.metric-value { font-size: 28px; font-weight: 600; color: #e8eaf0; }
.badge-green { background-color: #1a2e24; color: #3a7d5c; border-radius: 4px; padding: 2px 8px; font-size: 12px; }
.badge-amber { background-color: #2a2010; color: #c49a3a; border-radius: 4px; padding: 2px 8px; font-size: 12px; }
.badge-blue { background-color: #1a2040; color: #4a7fe8; border-radius: 4px; padding: 2px 8px; font-size: 12px; }
.building-alert-card {
    background-color: rgba(84, 149, 108, 0.14);
    border: 1px solid rgba(112, 183, 137, 0.35);
}
.section-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    margin-right: 7px;
    color: #99c7a7;
    vertical-align: text-top;
}
.section-icon svg {
    width: 14px;
    height: 14px;
    stroke: currentColor;
    stroke-width: 1.8;
    fill: none;
}

/* Chat input — force dark background with high specificity */
div[data-testid="stChatInput"] {
    background-color: #161920 !important;
    border: 1px solid #252830 !important;
    border-radius: 8px !important;
}
div[data-testid="stChatInput"] > div {
    background-color: #161920 !important;
    border-radius: 8px !important;
}
div[data-testid="stChatInput"] textarea {
    background-color: #161920 !important;
    color: #e8eaf0 !important;
    caret-color: #e8eaf0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #555a66 !important;
}
div[data-testid="stChatInput"] button {
    background-color: #161920 !important;
    color: #8b909e !important;
    border: none !important;
}
div[data-testid="stChatInput"] button:hover {
    color: #c0544a !important;
}

</style>
""", unsafe_allow_html=True)

st.title("Tenant Services Chatbot")

# Startup check (unchanged logic)
if not SCALEDOWN_API_KEY:
    st.error("SCALEDOWN_API_KEY missing in .env")
    st.stop()
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY missing in .env")
    st.stop()

# Initialize chat history and feedback log
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "feedback_log" not in st.session_state:
    st.session_state["feedback_log"] = []

# Sidebar (simplified)
st.sidebar.markdown("<div class='sidebar-brand'>Riverside Apartments</div>", unsafe_allow_html=True)
quick_questions = {
    "Submit Maintenance Request": "How do I submit a maintenance request?",
    "Check Rent Due Date": "When is my rent due and what is the late fee?",
    "Book Rooftop Lounge": "How do I book the rooftop lounge?",
    "Pet Policy": "What is the pet policy?",
    "Quiet Hours": "What are the quiet hours?",
    "Emergency Contacts": "What are the emergency contact numbers?"
}
for label, prefill in quick_questions.items():
    if st.sidebar.button(label):
        if not st.session_state["messages"] or st.session_state["messages"][-1]["content"] != prefill:
            st.session_state["messages"].append({"role": "user", "content": prefill})
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Leasing Office**")
st.sidebar.markdown("(512) 847-3300")
st.sidebar.markdown("leasing@riversideapts.com")

# Top tabs
tabs = st.tabs(["Dashboard", "Chat Assistant", "Rent & Payments", "Feedback"])

####################
# Tab 1: Dashboard
####################
with tabs[0]:
    st.markdown("<div class='section-header'>Overview</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card'>
          <div class='metric-label'>Rent Status</div>
          <div class='metric-value'>$1,850</div>
          <div class='metric-sub'>Due December 1, 2025</div>
          <div style='margin-top:8px;'><span class='badge-green'>On Time</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
          <div class='metric-label'>Lease Status</div>
          <div class='metric-value'>Active</div>
          <div class='metric-sub'>Expires December 31, 2025</div>
          <div style='margin-top:8px;'><span class='badge-blue'>182 days remaining</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
          <div class='metric-label'>Open Maintenance</div>
          <div class='metric-value'>0</div>
          <div class='metric-sub'>No active requests</div>
          <div style='margin-top:8px;'><span class='badge-green'>All Clear</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Upcoming</div>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    from datetime import date
    today = date.today()
    next_due = date(2025, 12, 1)
    days_until = (next_due - today).days
    with r1:
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>Next Rent Due</div>
          <div class='metric-value'>$1,850</div>
          <div class='metric-sub'>Due {next_due.strftime('%B %d, %Y')}</div>
          <div style='margin-top:8px;'><strong style='color:#4a7fe8'>{days_until} days remaining</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div class='metric-card building-alert-card'>
          <div class='metric-label'><span class='section-icon' aria-hidden='true'><svg viewBox='0 0 24 24'><path d='M12 9v4m0 3h.01M10.29 3.86l-8.18 14.15A1 1 0 0 0 3 19.5h18a1 1 0 0 0 .87-1.49L13.71 3.86a1 1 0 0 0-1.42 0z'/></svg></span>Building Alerts</div>
          <div class='metric-sub'>Elevator C maintenance scheduled Feb 25 — use elevators A or B</div>
          <div class='metric-sub'>Pool opens May 1 — registration opens April 15</div>
          <div class='metric-sub'>Pest control treatment second Tuesday of each month</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'><span class='section-icon' aria-hidden='true'><svg viewBox='0 0 24 24'><path d='M4 7h16M4 12h16M4 17h10'/></svg></span>Amenity Hours</div>", unsafe_allow_html=True)
    import pandas as pd
    amenities = [
        ["Fitness Center", "5:00 AM – 11:00 PM", "Floor 2", "Key fob required"],
        ["Swimming Pool", "8:00 AM – 9:00 PM", "Rooftop", "May 1 – Oct 31 only"],
        ["Rooftop Lounge", "9:00 AM – 10:00 PM", "Rooftop", "Book via portal, max 20 guests"],
        ["Business Center", "7:00 AM – 10:00 PM", "Floor 1", "Printing $0.10/page"],
        ["Laundry Room", "7:00 AM – 10:00 PM", "Floor 1", "App payment only"],
        ["Package Room", "24 hours", "Lobby", "Packages held 7 days"]
    ]
    df_amen = pd.DataFrame(amenities, columns=["Amenity", "Hours", "Location", "Notes"])
    st.table(df_amen)

    st.markdown("<div class='section-header'><span class='section-icon' aria-hidden='true'><svg viewBox='0 0 24 24'><path d='M12 2l8 4v6c0 5-3.4 9.4-8 10-4.6-.6-8-5-8-10V6l8-4z'/><path d='M12 8v4m0 4h.01'/></svg></span>Emergency Contacts</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='metric-card'>
      <div class='metric-sub'><strong>Leasing Office:</strong> (512) 847-3300 | leasing@riversideapts.com</div>
      <div class='metric-sub'><strong>Emergency Maintenance:</strong> (512) 847-3311 (24/7)</div>
      <div class='metric-sub'><strong>Non-emergency police:</strong> 311</div>
      <div class='metric-sub'><strong>Fire / Medical:</strong> 911</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

########################
# Tab 2: Chat Assistant
########################
with tabs[1]:
    st.markdown("### Ask anything about your lease, building policies, or maintenance.")
    st.caption("Knowledge base powered by ScaleDown compression")

    # Display chat history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Process any prefilled messages immediately (those added by sidebar buttons)
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
        last = st.session_state["messages"][-1]["content"]
        # If last message has not yet been answered (no assistant reply after it), process
        idx = len(st.session_state["messages"]) - 1
        answered = False
        if idx + 1 < len(st.session_state["messages"]):
            for m in st.session_state["messages"][idx+1:]:
                if m["role"] == "assistant":
                    answered = True
                    break
        if not answered:
            with st.chat_message("assistant"):
                with st.spinner("Compressing with ScaleDown + thinking with Gemini..."):
                    compressed, orig_tokens, comp_tokens = compress_knowledge(last)
                    answer = get_gemini_answer(last, compressed)
                    st.markdown(answer)
                    if orig_tokens and comp_tokens:
                        st.caption(f"ScaleDown compressed {orig_tokens} -> {comp_tokens} tokens before sending to Gemini")
            st.session_state["messages"].append({"role": "assistant", "content": answer})

    # Chat input
    question = st.chat_input("Ask anything about your lease, maintenance, payments or amenities...")

    if question:
        st.session_state["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Compressing with ScaleDown + thinking with Gemini..."):
                compressed, orig_tokens, comp_tokens = compress_knowledge(question)
                answer = get_gemini_answer(question, compressed)
                st.markdown(answer)
                if orig_tokens and comp_tokens:
                    st.caption(f"ScaleDown compressed {orig_tokens} -> {comp_tokens} tokens before sending to Gemini")
        st.session_state["messages"].append({"role": "assistant", "content": answer})

########################
# Tab 3: Rent & Payments
########################
with tabs[2]:
    st.markdown("<div class='section-header'>Payment Summary</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='metric-card'>
      <div class='metric-label'>Monthly Rent</div>
      <div class='metric-value'>$1,850</div>
      <div class='metric-sub'>Security Deposit Paid: $1,850</div>
      <div class='metric-sub'>Pet Deposit: N/A</div>
      <div class='metric-sub'>Last Payment: November 1, 2025 — $1,850 (On Time)</div>
      <div class='metric-sub'>Next Due: December 1, 2025 (grace period until December 5)</div>
      <div class='metric-sub'>Late Fee if missed: $75</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Payment History</div>", unsafe_allow_html=True)
    import pandas as pd
    history = pd.DataFrame([
        ["July 2025", "$1,850", "Jul 1", "Jul 1", "On Time"],
        ["August 2025", "$1,850", "Aug 1", "Aug 3", "On Time"],
        ["September 2025", "$1,850", "Sep 1", "Sep 1", "On Time"],
        ["October 2025", "$1,850", "Oct 1", "Oct 7", "Late — $75 fee applied"],
        ["November 2025", "$1,850", "Nov 1", "Nov 1", "On Time"]
    ], columns=["Month", "Amount", "Due Date", "Paid Date", "Status"])

    def color_status(val):
        if 'Late' in val:
            return 'background-color: #2a2010; color: #c49a3a'
        return 'background-color: #1a2e24; color: #3a7d5c'

    styled = history.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled, use_container_width=True)

    st.markdown("<div class='section-header'>Payment Methods</div>", unsafe_allow_html=True)
    st.markdown("- Online portal: portal.riversideapts.com\n- Check payable to: Riverside Property Management LLC\n- Bank transfer: contact leasing for ACH details")

########################
# Tab 4: Feedback
########################
with tabs[3]:
    st.markdown("<div class='section-header'>Feedback</div>", unsafe_allow_html=True)
    topic = st.selectbox("What is your feedback about?", ["General", "Maintenance", "Amenities", "Leasing Office", "Building Cleanliness", "Noise Complaint", "Other"])
    rating = st.select_slider("Rate your experience", options=[1,2,3,4,5], value=5, format_func=lambda x: {1:'Poor',2:'Fair',3:'Good',4:'Very Good',5:'Excellent'}[x])
    details = st.text_area("Tell us more (optional)", placeholder="Share any details about your experience...")
    follow = st.checkbox("I would like a follow-up from the leasing team")
    if st.button("Submit Feedback"):
        entry = {"topic": topic, "rating": rating, "details": details, "follow_up": follow}
        st.session_state["feedback_log"].append(entry)
        st.success("Thank you for your feedback. Our team reviews all submissions within 2 business days.")
    st.markdown(f"{len(st.session_state['feedback_log'])} pieces of feedback submitted this session")
