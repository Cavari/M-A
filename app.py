import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util

# --- CONFIGURATION ---
st.set_page_config(page_title="M&A Deal Profiler (Gemini Powered)", layout="wide", page_icon="🧩")

# 1. Load Local Embedding Model (Keeps vector search fast & free)
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedding_model = load_embedding_model()

# 2. Mock Database of Acquirers (In reality, this is your SQL DB)
ACQUIRERS_DB = [
    {"Name": "Vista Equity", "Type": "PE Firm", "Focus": "Enterprise Software, SaaS, Recurring Revenue", "Min_Rev": 10},
    {"Name": "Salesforce Ventures", "Type": "Strategic", "Focus": "Cloud CRM, AI, B2B Marketing", "Min_Rev": 5},
    {"Name": "Constellation Software", "Type": "Holding Co", "Focus": "Niche Vertical SaaS, Transit, Utilities", "Min_Rev": 2},
    {"Name": "DentalCorp", "Type": "Strategic", "Focus": "Dental Practices, Medical Billing", "Min_Rev": 1},
    {"Name": "Blackstone Growth", "Type": "PE Firm", "Focus": "Consumer Tech, content, logistics", "Min_Rev": 50},
]

# --- HELPER FUNCTIONS ---

def scrape_website(url):
    """Scrapes text from the given URL."""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title and paragraphs
        text = soup.title.string + " " if soup.title else ""
        for p in soup.find_all('p'):
            text += p.get_text() + " "
            
        return text[:10000] # Gemini has a large context window, but let's limit to 10k chars for speed
    except Exception as e:
        return None

def analyze_with_gemini(api_key, text):
    """Uses Google Gemini to summarize the business."""
    try:
        genai.configure(api_key=api_key)
        # Use 'gemini-1.5-flash' for speed and low cost
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an M&A analyst. Analyze the following website text for a target company.
        
        1. Summarize what the company does in 2 sentences.
        2. Identify their primary industry/sector.
        3. Identify their likely business model (SaaS, Service, Manufacturing, Marketplace).
        
        Website Text:
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to Gemini: {e}"

def find_matches(target_description, deal_type, revenue):
    """Matches the AI summary against the Database using Vector Search."""
    results = []
    
    # Encode the Target Description
    target_embedding = embedding_model.encode(target_description, convert_to_tensor=True)
    
    for buyer in ACQUIRERS_DB:
        # Encode Buyer Focus
        buyer_text = f"{buyer['Focus']} interested in {buyer['Type']}"
        buyer_embedding = embedding_model.encode(buyer_text, convert_to_tensor=True)
        
        # Calculate Similarity
        score = util.pytorch_cos_sim(target_embedding, buyer_embedding).item()
        
        # Basic Filter: Don't show PE firms for tiny revenue
        rev_val = 0
        if "1M" in revenue: rev_val = 1
        elif "5M" in revenue: rev_val = 5
        elif "20M" in revenue: rev_val = 20
        
        if buyer['Min_Rev'] > rev_val and deal_type != "Distressed Asset":
            score = score - 0.2 # Penalize mismatch in size
            
        if score > 0.2: # Only keep decent matches
            results.append({**buyer, "Score": round(score * 100, 1)})
            
    return sorted(results, key=lambda x: x['Score'], reverse=True)

# --- UI LAYOUT ---

with st.sidebar:
    st.header("🔑 API Setup")
    gemini_key = st.text_input("Google Gemini API Key", type="password", help="Get one at aistudio.google.com")
    st.info("No key? The scraper will work, but the AI summary will fail.")

st.title("🧩 M&A Profiler (Gemini Edition)")
st.markdown("Enter a URL to scrape the business, analyze it with Google Gemini, and find buyers.")

# STEP 1: INPUT
col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input("Company URL", placeholder="www.example.com")

if url_input:
    if not gemini_key:
        st.warning("Please enter your Gemini API Key in the sidebar to proceed.")
    else:
        with st.spinner("🕷️ Scraping & 🧠 Thinking (Gemini 1.5)..."):
            # 1. Scrape
            raw_text = scrape_website(url_input)
            
            if raw_text:
                # 2. Analyze with Gemini
                analysis = analyze_with_gemini(gemini_key, raw_text)
                st.success("Analysis Complete")
                st.markdown(f"### 🤖 AI Assessment")
                st.info(analysis)
                
                st.divider()
                
                # STEP 2: REFINE
                st.subheader("Deal Context")
                with st.form("deal_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        rev = st.selectbox("Annual Revenue", ["<$1M", "$1M - $5M", "$5M - $20M", "$20M+"])
                    with c2:
                        goal = st.selectbox("Deal Goal", ["Full Exit", "Majority Recap", "Growth Equity"])
                        
                    match_btn = st.form_submit_button("Find Buyers")
                
                # STEP 3: MATCHING
                if match_btn:
                    st.divider()
                    st.subheader("Recommended Acquirers")
                    matches = find_matches(analysis, goal, rev)
                    
                    for m in matches:
                        with st.container():
                            st.markdown(f"### {m['Name']} <span style='font-size:0.8em; color:green'>({m['Score']}% Fit)</span>", unsafe_allow_html=True)
                            st.write(f"**Focus:** {m['Focus']}")
                            st.write(f"**Type:** {m['Type']}")
                            if st.button(f"Draft Outreach to {m['Name']}", key=m['Name']):
                                st.toast("Draft saved to sequence!")
                            st.markdown("---")
            else:
                st.error("Could not scrape that URL. Try another or check the link.")
