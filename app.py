import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="M&A Deal Profiler", layout="wide", page_icon="🧩")

# Mock Database (simulating what you'd have in a real SQL DB)
MOCK_DB = [
    {"Name": "Vista Equity", "Type": "PE Firm", "Focus": "Enterprise Software", "Min_Rev": 10, "Past_Buys": ["Mindbody", "Apptio"]},
    {"Name": "Constellation Software", "Type": "Holding Co", "Focus": "Vertical Market SaaS", "Min_Rev": 2, "Past_Buys": ["Topicus", "Vela"]},
    {"Name": "Salesforce Ventures", "Type": "Strategic", "Focus": "Cloud CRM & AI", "Min_Rev": 5, "Past_Buys": ["Slack", "Tableau"]},
    {"Name": "DentalCorp", "Type": "Strategic", "Focus": "Healthcare/Dental", "Min_Rev": 1, "Past_Buys": ["Dental Care Alliance"]},
    {"Name": "Thoma Bravo", "Type": "PE Firm", "Focus": "Security & Infrastructure", "Min_Rev": 20, "Past_Buys": ["Proofpoint", "Sophos"]}
]

# --- HELPER FUNCTIONS ---
def mock_ai_analysis(url):
    """Simulates AI analyzing a website."""
    time.sleep(2) # Simulate processing time
    if "dental" in url.lower():
        return "SaaS platform for dental practice management and patient scheduling."
    elif "tech" in url.lower():
        return "B2B Enterprise software for supply chain logistics."
    else:
        return "Cloud-based subscription software for small business inventory management."

def match_acquirers(revenue, deal_type, business_summary):
    """Simulates the matching logic."""
    matches = []
    
    # Simple logic to simulate "AI Matching"
    rev_amount = int(revenue.replace("$", "").replace("M", "").split("-")[0].replace("<", "").replace("+", ""))
    
    for buyer in MOCK_DB:
        score = 0
        # Revenue Logic
        if rev_amount >= buyer["Min_Rev"]:
            score += 30
        
        # Keyword Logic
        if "Dental" in buyer["Focus"] and "dental" in business_summary.lower():
            score += 50
        if "Software" in buyer["Focus"] and "software" in business_summary.lower():
            score += 40
            
        # Randomizer for "AI Confidence" feel
        import random
        score += random.randint(5, 15)
        
        if score > 40:
            matches.append({**buyer, "Score": score})
            
    return sorted(matches, key=lambda x: x['Score'], reverse=True)

# --- THE APP UI ---

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", help="Leave empty to use Demo Mode")
    st.info("💡 **Demo Mode Active:** running without real AI for preview purposes.")

st.title("🧩 M&A Deal Profiler")
st.markdown("Enter a target company URL to find the perfect buyer.")

# STEP 1: INPUT
st.subheader("1. Target Analysis")
col1, col2 = st.columns([3, 1])
with col1:
    url = st.text_input("Company URL", placeholder="www.dentalsolutions.com")

if url:
    with st.spinner("🕷️ Scraping website and analyzing business model..."):
        # In real version, we scrape here. In demo, we mock it.
        summary = mock_ai_analysis(url)
    
    st.success("Analysis Complete")
    st.text_area("AI Business Summary", value=summary, height=80)
    
    st.divider()
    
    # STEP 2: PROFILING
    st.subheader("2. Deal Structuring")
    with st.form("profiler"):
        c1, c2, c3 = st.columns(3)
        with c1:
            revenue = st.selectbox("Revenue", ["<$1M", "$1M-$5M", "$5M-$20M", "$20M+"])
        with c2:
            deal_goal = st.selectbox("Goal", ["Full Exit", "Majority Recap", "Growth Capital"])
        with c3:
            timeline = st.selectbox("Timeline", ["ASAP", "6 Months", "12+ Months"])
            
        search_btn = st.form_submit_button("🔍 Find Acquirers")

    # STEP 3: RESULTS
    if search_btn:
        st.divider()
        st.subheader("3. Top Acquirer Matches")
        
        results = match_acquirers(revenue, deal_goal, summary)
        
        if not results:
            st.warning("No high-confidence matches found in database.")
        
        for res in results:
            with st.container():
                # Card Layout
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.markdown(f"### **{res['Name']}** <span style='color:green; font-size:16px'>({res['Score']}% Match)</span>", unsafe_allow_html=True)
                    st.write(f"**Focus:** {res['Focus']} | **Type:** {res['Type']}")
                    st.caption(f"**Notable Buys:** {', '.join(res['Past_Buys'])}")
                with row2:
                    st.write("") # Spacer
                    if st.button(f"📧 Draft Email", key=res['Name']):
                        st.toast(f"Draft saved for {res['Name']}!")
                st.markdown("---")
