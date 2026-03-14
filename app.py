import streamlit as st
import requests
import os
import random
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from database import (
    login_user, register_user, get_all_tenants,
    get_all_payments, add_payment, add_complaint,
    resolve_complaint, get_all_complaints,
    add_feedback, get_all_feedback, add_announcement,
    get_announcements, record_manual_payment,
    get_tenant_payments, update_user_balance
)

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
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    margin: 0.2rem 0 0.6rem 0;
    line-height: 1.2;
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

.auth-button > button {
    background-color: #4a7fe8 !important;
    color: white !important;
    border-radius: 6px !important;
    width: 100% !important;
    padding: 10px !important;
    font-weight: 500 !important;
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

# Initialize session state for auth
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None

# Initialize chat history and feedback log
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "feedback_log" not in st.session_state:
    st.session_state["feedback_log"] = []

# ── AUTH GATE ──────────────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    st.markdown(
        "<h2 style='text-align:center;color:#f6b26b;'>Riverside Apartments</h2>",
        unsafe_allow_html=True,
    )
    auth_tabs = st.tabs(["Sign In", "Create Account"])

    # ── Sign In ────────────────────────────────────────────────────────────────
    with auth_tabs[0]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## Welcome Back")
            st.markdown("Sign in to your tenant portal")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            st.markdown('<div class="auth-button">', unsafe_allow_html=True)
            if st.button("Sign In", key="signin_btn"):
                user = login_user(username, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.session_state["role"] = user.get("role", "tenant")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Create Account ─────────────────────────────────────────────────────────
    with auth_tabs[1]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## Create Your Account")
            name = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email Address", key="reg_email")
            phone = st.text_input("Phone Number", placeholder="+91 XXXXX XXXXX", key="reg_phone")
            unit = st.text_input("Unit Number", placeholder="e.g. 2B, 3C", key="reg_unit")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            st.markdown('<div class="auth-button">', unsafe_allow_html=True)
            if st.button("Create Account", key="register_btn"):
                if not all([name, email, phone, unit, reg_username, reg_password, confirm]):
                    st.error("All fields required")
                elif reg_password != confirm:
                    st.error("Passwords do not match")
                elif len(reg_password) < 8:
                    st.error("Password must be 8+ characters")
                elif "@" not in email:
                    st.error("Invalid email address")
                else:
                    ok, msg = register_user(reg_username, reg_password, name, email, unit, phone)
                    if ok:
                        st.success("Account created! You can now sign in.")
                    else:
                        st.error(msg)
            st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ── SIDEBAR (post-login) ───────────────────────────────────────────────────────
user = st.session_state["user"]
role = st.session_state["role"]

st.sidebar.markdown(
    f"<div class='sidebar-brand' style='font-size:1.35rem;font-weight:700;"
    f"color:#f6b26b;letter-spacing:0.01em;margin-bottom:4px;'>"
    f"{user['name']}</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<div style='color:#a0a6b4;font-size:13px;margin-bottom:4px;'>"
    f"{'Admin' if role == 'admin' else 'Unit ' + user['unit']}</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

if role == "tenant":
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
else:
    for label in ["Overview", "Tenants", "Payments", "Complaints", "Announcements"]:
        st.sidebar.markdown(f"<span class='sidebar-link'>{label}</span>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Leasing Office**")
st.sidebar.markdown("+91 98765 43210")
st.sidebar.markdown("leasing@riversideapts.com")
st.sidebar.markdown("---")

if st.sidebar.button("Sign Out"):
    st.session_state.clear()
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if role == "admin":
    admin_tabs = st.tabs(["Overview", "Tenants", "Payments", "Complaints", "Announcements"])

    # ── Overview ───────────────────────────────────────────────────────────────
    with admin_tabs[0]:
        st.markdown("<div class='section-header'>Admin Overview</div>", unsafe_allow_html=True)
        tenants = get_all_tenants()
        payments = get_all_payments()
        complaints = get_all_complaints()
        pending = sum(1 for t in tenants if t.get("balance", 0) > 0)
        open_complaints = sum(1 for c in complaints if c.get("status") == "Open")
        total_collected = sum(p.get("amount", 0) for p in payments)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>Total Tenants</div>
              <div class='metric-value'>{len(tenants)}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>Rent Collected</div>
              <div class='metric-value'>₹{total_collected:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>Pending Payments</div>
              <div class='metric-value'>{pending}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>Open Complaints</div>
              <div class='metric-value'>{open_complaints}</div>
            </div>""", unsafe_allow_html=True)

    # ── Tenants ────────────────────────────────────────────────────────────────
    with admin_tabs[1]:
        st.markdown("<div class='section-header'>All Tenants</div>", unsafe_allow_html=True)
        tenants = get_all_tenants()
        if tenants:
            rows = []
            for t in tenants:
                rows.append({
                    "Name": t.get("name", ""),
                    "Unit": t.get("unit", ""),
                    "Email": t.get("email", ""),
                    "Phone": t.get("phone", ""),
                    "Rent": f"₹{t.get('rent', 0):,.0f}",
                    "Balance": f"₹{t.get('balance', 0):,.0f}",
                    "Status": "Overdue" if t.get("balance", 0) > 0 else "Current",
                })
            df_tenants = pd.DataFrame(rows)
            def highlight_status(val):
                if val == "Overdue":
                    return "background-color: #2a2010; color: #c49a3a"
                return "background-color: #1a2e24; color: #3a7d5c"
            styled_t = df_tenants.style.applymap(highlight_status, subset=["Status"])
            st.dataframe(styled_t, use_container_width=True)
        else:
            st.info("No tenants found.")

    # ── Payments ───────────────────────────────────────────────────────────────
    with admin_tabs[2]:
        st.markdown("<div class='section-header'>All Payments</div>", unsafe_allow_html=True)
        payments = get_all_payments()
        if payments:
            df_pay = pd.DataFrame(payments)
            st.dataframe(df_pay, use_container_width=True)
            total = sum(p.get("amount", 0) for p in payments)
            st.markdown(f"**Total Collected: ₹{total:,.0f}**")
        else:
            st.info("No payments recorded.")

        st.markdown("---")
        st.markdown("<div class='section-header'>Record Manual Payment</div>", unsafe_allow_html=True)
        all_tenants = get_all_tenants()
        if all_tenants:
            tenant_names = [t["name"] for t in all_tenants]
            sel_tenant_name = st.selectbox("Tenant", tenant_names, key="manual_pay_tenant")
            sel_tenant = next((t for t in all_tenants if t["name"] == sel_tenant_name), None)
            manual_amount = st.number_input("Amount ($)", min_value=0.0, step=50.0, key="manual_amount")
            manual_date = st.date_input("Date", key="manual_date")
            if st.button("Record Payment"):
                if sel_tenant:
                    ok = record_manual_payment(
                        sel_tenant["id"], sel_tenant["name"],
                        sel_tenant["unit"], manual_amount,
                        str(manual_date)
                    )
                    if ok:
                        st.success("Payment recorded.")
                    else:
                        st.error("Failed to record payment.")

    # ── Complaints ─────────────────────────────────────────────────────────────
    with admin_tabs[3]:
        st.markdown("<div class='section-header'>Complaints</div>", unsafe_allow_html=True)
        complaints = get_all_complaints()
        if complaints:
            for c in complaints:
                badge = "<span class='badge-green'>Resolved</span>" if c.get("status") == "Resolved" else "<span class='badge-amber'>Open</span>"
                st.markdown(f"""
                <div class='metric-card'>
                  <div><strong>{c.get('tenant_name','')}</strong> — Unit {c.get('unit','')} &nbsp;{badge}</div>
                  <div class='metric-sub'><strong>Category:</strong> {c.get('category','')}</div>
                  <div class='metric-sub'><strong>Subject:</strong> {c.get('subject','')}</div>
                  <div class='metric-sub'>{c.get('message','')}</div>
                  <div class='metric-sub'>Filed: {c.get('date','')}</div>
                </div>""", unsafe_allow_html=True)
                if c.get("status") != "Resolved":
                    if st.button("Mark Resolved", key=f"resolve_{c['id']}"):
                        resolve_complaint(c["id"])
                        st.rerun()
        else:
            st.info("No complaints filed.")

        st.markdown("---")
        st.markdown("<div class='section-header'>Feedback</div>", unsafe_allow_html=True)
        feedbacks = get_all_feedback()
        if feedbacks:
            for f in feedbacks:
                st.markdown(f"""
                <div class='metric-card'>
                  <div><strong>{f.get('tenant_name','')}</strong> — Unit {f.get('unit','')}</div>
                  <div class='metric-sub'><strong>Topic:</strong> {f.get('topic','')} | <strong>Rating:</strong> {f.get('rating','')}/5</div>
                  <div class='metric-sub'>{f.get('details','')}</div>
                  <div class='metric-sub'>Follow-up: {'Yes' if f.get('follow_up') else 'No'}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No feedback submitted.")

    # ── Announcements ──────────────────────────────────────────────────────────
    with admin_tabs[4]:
        st.markdown("<div class='section-header'>Post Announcement</div>", unsafe_allow_html=True)
        ann_title = st.text_input("Title", key="ann_title")
        ann_message = st.text_area("Message", key="ann_message")
        ann_priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="ann_priority")
        if st.button("Post Announcement"):
            if ann_title and ann_message:
                ok = add_announcement(ann_title, ann_message, ann_priority)
                if ok:
                    st.success("Announcement posted.")
                    st.rerun()
                else:
                    st.error("Failed to post announcement.")
            else:
                st.error("Title and message are required.")

        st.markdown("<div class='section-header'>All Announcements</div>", unsafe_allow_html=True)
        announcements = get_announcements()
        for a in announcements:
            priority = a.get("priority", "Low")
            badge_cls = "badge-amber" if priority == "High" else "badge-blue" if priority == "Medium" else "badge-green"
            st.markdown(f"""
            <div class='metric-card'>
              <div><strong>{a.get('title','')}</strong> &nbsp;<span class='{badge_cls}'>{priority}</span></div>
              <div class='metric-sub'>{a.get('message','')}</div>
              <div class='metric-sub'>{a.get('date','')}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TENANT VIEW
# ═══════════════════════════════════════════════════════════════════════════════
else:
    tenant_name = user["name"]
    tenant_unit = user["unit"]
    tenant_rent = user["rent"]
    tenant_balance = user["balance"]

    tabs = st.tabs(["Dashboard", "Chat Assistant", "Rent & Payments", "Feedback"])

    ####################
    # Tab 1: Dashboard
    ####################
    with tabs[0]:
        st.markdown(
            f"<div class='section-header'>Good to see you, {tenant_name}. Unit {tenant_unit} summary.</div>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            balance_badge = (
                "<span class='badge-amber'>Payment Due</span>"
                if tenant_balance > 0
                else "<span class='badge-green'>On Time</span>"
            )
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>Rent Status</div>
              <div class='metric-value'>₹{tenant_rent:,.0f}</div>
              <div class='metric-sub'>Balance Due: ₹{tenant_balance:,.0f}</div>
              <div style='margin-top:8px;'>{balance_badge}</div>
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
              <div class='metric-value'>₹{tenant_rent:,.0f}</div>
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
        amenities = [
            ["Fitness Center", "5:00 AM – 11:00 PM", "Floor 2", "Key fob required"],
            ["Swimming Pool", "8:00 AM – 9:00 PM", "Rooftop", "May 1 – Oct 31 only"],
            ["Rooftop Lounge", "9:00 AM – 10:00 PM", "Rooftop", "Book via portal, max 20 guests"],
            ["Business Center", "7:00 AM – 10:00 PM", "Floor 1", "Printing ₹0.10/page"],
            ["Laundry Room", "7:00 AM – 10:00 PM", "Floor 1", "App payment only"],
            ["Package Room", "24 hours", "Lobby", "Packages held 7 days"]
        ]
        df_amen = pd.DataFrame(amenities, columns=["Amenity", "Hours", "Location", "Notes"])
        st.table(df_amen)

        st.markdown("<div class='section-header'><span class='section-icon' aria-hidden='true'><svg viewBox='0 0 24 24'><path d='M12 2l8 4v6c0 5-3.4 9.4-8 10-4.6-.6-8-5-8-10V6l8-4z'/><path d='M12 8v4m0 4h.01'/></svg></span>Emergency Contacts</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='metric-card'>
          <div class='metric-sub'><strong>Leasing Office:</strong> +91 98765 43210 | leasing@riversideapts.com</div>
          <div class='metric-sub'><strong>Emergency Maintenance:</strong> +91 98765 43211 (24/7)</div>
          <div class='metric-sub'><strong>Non-emergency police:</strong> 100</div>
          <div class='metric-sub'><strong>Fire / Medical:</strong> 112</div>
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
        # Refresh balance from session state (may have updated)
        tenant_balance = st.session_state["user"]["balance"]
        if tenant_balance == 0:
            st.markdown("<span class='badge-green'>No Payment Due</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='badge-amber'>Payment Due: ₹{tenant_balance:,.0f}</span>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>Monthly Rent</div>
          <div class='metric-value'>₹{tenant_rent:,.0f}</div>
          <div class='metric-sub'>Balance Due: ₹{tenant_balance:,.0f}</div>
          <div class='metric-sub'>Late Fee if missed: ₹75</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("payment_form"):
            st.markdown("#### Payment Details")
            cardholder = st.text_input("Cardholder Name")
            card_number = st.text_input("Card Number", max_chars=16, placeholder="1234567890123456")
            exp_col, cvv_col = st.columns(2)
            with exp_col:
                expiry = st.text_input("Expiry MM/YY", placeholder="MM/YY")
            with cvv_col:
                cvv = st.text_input("CVV", type="password", max_chars=3, placeholder="123")
            billing_zip = st.text_input("Billing ZIP", max_chars=5, placeholder="78701")
            pay_submitted = st.form_submit_button(f"Pay ₹{tenant_balance:,.0f}")
            if pay_submitted:
                if not all([cardholder, card_number, expiry, cvv, billing_zip]):
                    st.error("All payment fields are required.")
                else:
                    ok = add_payment(
                        user["id"], tenant_name, tenant_unit, tenant_balance
                    )
                    if ok:
                        st.session_state["user"]["balance"] = 0
                        st.success("Payment processed successfully")
                        st.balloons()
                    else:
                        st.error("Payment failed. Please try again.")

        st.markdown("<div class='section-header'>Payment History</div>", unsafe_allow_html=True)
        payment_history = get_tenant_payments(user["id"])
        if payment_history:
            df_hist = pd.DataFrame(payment_history)
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("No payment history found.")

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
            ok = add_feedback(
                user["id"], tenant_name, tenant_unit,
                topic, rating, details, follow
            )
            if ok:
                st.success("Thank you for your feedback. Our team reviews all submissions within 2 business days.")
            else:
                st.error("Failed to submit feedback.")

        st.markdown("---")
        st.markdown("<div class='section-header'>Submit a Complaint</div>", unsafe_allow_html=True)
        c_subject = st.text_input("Subject", key="complaint_subject")
        c_category = st.selectbox("Category", ["Noise", "Maintenance", "Neighbor", "Building Issue", "Other"], key="complaint_category")
        c_message = st.text_area("Describe your complaint", key="complaint_message")
        if st.button("Submit Complaint"):
            if c_subject and c_message:
                ok = add_complaint(
                    user["id"], tenant_name, tenant_unit,
                    c_subject, c_category, c_message
                )
                if ok:
                    ref = random.randint(1000, 9999)
                    st.success(f"Complaint submitted. Reference #: {ref}")
                else:
                    st.error("Failed to submit complaint.")
            else:
                st.error("Subject and message are required.")
