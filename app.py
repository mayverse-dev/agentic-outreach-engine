import requests
from bs4 import BeautifulSoup
from groq import Groq
import pandas as pd
import streamlit as st
import time
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Agentic Outreach Engine (Emass)", layout="wide")

# --- FORCED DARK MODE CSS (Visible PS5 Wave + Blue Boxes) ---
st.markdown("""
<style>
    /* STRICT DARK MODE VARIABLES */
    :root {
        --card-bg: rgba(20, 20, 30, 0.7);
        --input-bg: rgba(10, 25, 60, 0.7); 
        --input-text: #ffffff;
        --input-border: rgba(59, 130, 246, 0.5); 
        --btn-bg: #1d4ed8; 
        --btn-text: #ffffff;
        --btn-glow: rgba(29, 78, 216, 0.6);
        --text-color: #ffffff;
        --subtext-color: #cccccc;
        --border-color: rgba(255, 255, 255, 0.2);
        --hover-border: #3b82f6; 
        --email-box-bg: rgba(10, 25, 60, 0.4);
    }

    /* 1. Global Text Overrides */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label, .stRadio div {
        color: var(--text-color) !important;
    }

    /* 2. Animated App Background - Forced & Visible */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #000000, #000000, #0a2050, #1e3a8a, #000000) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 10s ease infinite !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 3. Streamlit Input Boxes */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="base-input"] {
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        caret-color: var(--input-text) !important; 
        border-color: var(--input-border) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        opacity: 0.5 !important;
    }

    /* 4. Streamlit Primary Button Override */
    .stButton > button {
        background-color: var(--btn-bg) !important;
        color: var(--btn-text) !important;
        border: 1px solid var(--btn-bg) !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px var(--btn-glow) !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 25px var(--btn-glow) !important;
        border-color: var(--hover-border) !important;
        color: var(--btn-text) !important;
    }

    /* 5. 3D Glassmorphism Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 1px 2px var(--border-color);
        border: 1px solid var(--border-color);
        transform-style: preserve-3d;
        perspective: 1000px;
        transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        animation: slideUpFade 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(40px);
    }
    @keyframes slideUpFade {
        to { opacity: 1; transform: translateY(0); }
    }
    
    .glass-card:hover {
        transform: translateY(-12px) rotateX(2deg) rotateY(-2deg);
        box-shadow: 15px 25px 50px rgba(0,0,0,0.8), inset 0 1px 2px var(--input-border);
        border-color: var(--hover-border);
    }

    /* 6. Glowing Mailto Buttons */
    .mailto-btn {
        display: inline-block;
        background: var(--btn-bg);
        color: var(--btn-text) !important;
        padding: 14px 28px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px var(--btn-glow);
        margin-top: 20px;
    }
    
    .mailto-btn:hover {
        transform: scale(1.05) translateY(-3px);
        box-shadow: 0 10px 25px var(--btn-glow);
    }
    
    /* 7. Fixed Text Colors inside cards */
    .email-body-text {
        white-space: pre-wrap;
        font-family: 'Inter', sans-serif;
        color: var(--text-color) !important;
        line-height: 1.7;
        background: var(--email-box-bg);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid var(--btn-bg);
        font-size: 15px;
    }

    .card-header-text {
        color: var(--text-color) !important;
        margin-top: 0;
    }
    .card-subtext {
        font-size: 16px;
        color: var(--subtext-color) !important;
    }
</style>
""", unsafe_allow_html=True)


# --- BACKEND FUNCTIONS ---

def scrape_website(url):
    try:
        if pd.isna(url) or url == "N/A" or not url:
            return "Could not read website."
        if not url.startswith("http"):
            url = "https://" + url

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join(soup.stripped_strings)[:1500]
        return text
    except Exception:
        return "Could not read website."


def generate_icebreaker(client, company_name, website_text):
    if website_text == "Could not read website." or company_name == "your company":
        return "I hope you are having a great week so far!"

    prompt = f"""
    You are an expert copywriter. Read the text from the website of {company_name}: "{website_text}"
    Write ONE single, natural-sounding sentence to use as an icebreaker in an email. 
    It should compliment them on a specific service or achievement. Do not use the words "I noticed" or "I saw".
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception:
        return "I hope you are having a great week so far!"


def generate_full_email(client, first_name, company_name, website_text, custom_prompt, sender_name):
    # Dynamically adjust the prompt based on whether company info exists
    company_context = f"Target Company: {company_name}" if company_name != "your company" else "No specific company data provided."
    web_context = f"Target Website Context: '{website_text}'" if website_text != "Could not read website." else "No website data provided."

    prompt = f"""
    You are an expert copywriter writing a personalized email.
    
    Target First Name: {first_name}
    {company_context}
    {web_context}
    Sender Name: {sender_name}
    
    USER INSTRUCTIONS FOR THE EMAIL:
    "{custom_prompt}"
    
    Write a complete email based EXACTLY on the User Instructions above. 
    If Company and Website context is provided, you may use it to personalize the message. If no company/website is provided, just focus entirely on fulfilling the User Instructions.
    
    MANDATORY RULES:
    1. You MUST start the email with exactly: "Hi {first_name}," (or "Hi there," if no name is provided).
    2. You MUST sign off the email with: "Best,\\n{sender_name}"
    3. Do not include subject lines, just the email body.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception:
        return f"Hi {first_name},\n\nI wanted to reach out and connect.\n\nBest,\n{sender_name}"


# --- UI LAYOUT ---
st.title("Agentic Mailing System")

tab_app, tab_about = st.tabs(["Automated Email Generation", "👤 About Me"])

with tab_about:
    st.header("My Bio")
    st.markdown("**Hi, I'm Wasif Mayraj.** I'm a CSE undergrad, majoring in AL/ML. I'm also a freelance AI Automation Specialist in Fiverr who is focused on building autonomous agents that eliminate operational bottlenecks for businesses.")
    st.header("Why I built this")
    st.markdown("""
    Most outbound campaigns suffer from a massive bottleneck: **Lead Decay & Follow-up Fatigue.** Teams spend hours manually researching to write personalized emails, or default to generic templates. I built this engine to automate the intelligence behind the outreach, not just the sending.
    """)
    st.header("Why this engine is unique")
    st.markdown("Unlike standard tools that just do simple 'Find & Replace', this tool is a **Dual-Mode Contextual AI Agent**. It actively crawls your prospect's website and uses Meta's Llama 3 reasoning to either inject hyper-personalized icebreakers, or autonomously write the entire email from scratch based on your prompt. All you need is your groq API key to unlock AI reasoning.")
    st.divider()
    st.markdown(
        "### Let's Connect:\n* 🔗 [My LinkedIn](https://www.linkedin.com/in/wasif-mayraj-82103329b)\n* 💻 [My GitHub](https://github.com/mayverse-dev)")

with tab_app:
    st.markdown("### 1. Sender Details")
    sender_name_input = st.text_input(
        "Your Name (How should the AI sign the email?)", placeholder="e.g. Wasif")
    sender_name = sender_name_input if sender_name_input else "Wasif"

    st.markdown("### 2. Choose AI Autonomy Level")
    generation_mode = st.radio(
        "How much control do you want to give the AI?",
        ["Hybrid Mode (Template + AI Icebreaker)",
         "Full Autonomous Mode (AI writes the entire email based on your prompt)"]
    )

    if "Hybrid" in generation_mode:
        with st.expander("Edit Your Hybrid Template", expanded=True):
            default_template = "Hi {First Name},\n\n{Icebreaker}\n\nI wanted to reach out to you today to discuss how we can help {Company Name} scale operations.\n\nLet me know what you think.\n\nBest,\n{Sender Name}"
            user_input_box = st.text_area(
                "Write your base template here:", placeholder=default_template, height=200)
            user_input = user_input_box if user_input_box else default_template
    else:
        with st.expander("Prompt the AI (Chatbot Style)", expanded=True):
            default_ai_prompt = "Wish them a happy birthday and hope they have a fantastic year ahead! Keep it short, warm, and professional."
            user_input_box = st.text_area(
                "Give the AI instructions on how to write the email:", placeholder=f"e.g. {default_ai_prompt}", height=150)
            user_input = user_input_box if user_input_box else default_ai_prompt

    st.markdown("### 3. Upload Lead List")
    uploaded_file = st.file_uploader(
        "Upload CSV (Requires 'Email' column. Optional: 'First Name', 'Company Name', 'Website')", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        # Strip whitespace from columns to avoid matching errors
        df.columns = df.columns.str.strip()
        st.dataframe(df.head(3), use_container_width=True)

        st.divider()
        st.markdown("### 4. Connect & Generate")

        col1, col2 = st.columns([1, 1])
        with col1:
            groq_key = st.text_input(
                "🔑 Groq API Key", type="password", placeholder="Paste your API key here...")
            st.caption(
                "[Get your free key here](https://console.groq.com/keys)")

        st.write("")

        if st.button("⚡ Generate AI Campaigns", type="primary", use_container_width=True):
            if not groq_key:
                st.error("Please provide your Groq API Key.")
            elif 'Email' not in df.columns:
                st.error(
                    "⚠️ Your CSV must have a column exactly named 'Email'. Please check your file.")
            else:
                try:
                    client = Groq(api_key=groq_key)
                    st.success(
                        "Agents initialized! Generating tailored campaigns below...")

                    results_container = st.container()

                    with results_container:
                        for index, row in df.iterrows():
                            # --- GRACEFUL FALLBACK LOGIC ---
                            # Extract data securely even if the columns do not exist in the CSV
                            raw_first = str(
                                row.get('First Name', 'N/A')).strip()
                            raw_company = str(
                                row.get('Company Name', 'N/A')).strip()
                            raw_website = str(
                                row.get('Website', 'N/A')).strip()
                            email_address = str(row['Email']).strip()

                            # Set intelligent defaults for missing data
                            first_name = "there" if raw_first in [
                                "N/A", "nan", "None", ""] else raw_first

                            has_company = raw_company not in [
                                "N/A", "nan", "None", ""]
                            company_name = raw_company if has_company else "your company"

                            has_website = raw_website not in [
                                "N/A", "nan", "None", ""]

                            # Update UI elements dynamically based on available data
                            if has_company:
                                status_msg = f"Crawling {company_name}..."
                                subject = f"Quick question for {company_name}"
                                card_title = f"🏢 {company_name}"
                            else:
                                status_msg = f"Generating for {first_name}..."
                                subject = "Checking in"
                                card_title = f"✉️ Outreach Email"

                            with st.spinner(status_msg):
                                # Only try to scrape if a website was actually provided
                                site_context = scrape_website(
                                    raw_website) if has_website else "Could not read website."

                                if "Hybrid" in generation_mode:
                                    icebreaker = generate_icebreaker(
                                        client, company_name, site_context)
                                    try:
                                        full_email = user_input.format(
                                            **{"First Name": first_name, "Company Name": company_name, "Icebreaker": icebreaker, "Sender Name": sender_name}
                                        )
                                    except KeyError:
                                        st.error(
                                            "Template Error: Check your `{}` placeholders.")
                                        st.stop()
                                else:
                                    full_email = generate_full_email(
                                        client, first_name, company_name, site_context, user_input, sender_name)

                                subject_encoded = urllib.parse.quote(subject)
                                body_encoded = urllib.parse.quote(full_email)
                                mailto_link = f"mailto:{email_address}?subject={subject_encoded}&body={body_encoded}"

                                st.markdown(f"""
                                <div class="glass-card">
                                    <h3 class="card-header-text">{card_title} <span class="card-subtext">(To: {first_name} - {email_address})</span></h3>
                                    <div class="email-body-text">{full_email}</div>
                                    <a href="{mailto_link}" class="mailto-btn" target="_blank">🚀 One-Click Send</a>
                                </div>
                                """, unsafe_allow_html=True)

                                time.sleep(0.5)

                        st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
