import os
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import streamlit as st
from groq import Groq

# Optional: Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Read API Key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# 1. TOOL FUNCTIONS
# ==========================================

def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"🧮 Calculation Result: **{result}**"
    except Exception as e:
        return f"❌ Invalid expression: {str(e)}"

def get_system_time() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"🕒 Current System Time: **{now}**"

def create_pdf(filename: str, title: str, content: str) -> str:
    try:
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        output_dir = Path(__file__).resolve().parent
        filepath = output_dir / filename

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=16)
        
        clean_title = title.encode('latin-1', 'replace').decode('latin-1')
        clean_content = content.encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(200, 10, text=clean_title, new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(10)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, text=clean_content)

        pdf.output(str(filepath))
        return f"📄 PDF generated successfully! Saved at: `{filepath}`"
    except Exception as e:
        return f"❌ PDF creation failed: {str(e)}"

def web_search(query: str) -> str:
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        abstract = data.get("AbstractText", "")
        source_url = data.get("AbstractURL", "")
        heading = data.get("Heading", query)
        
        if abstract and source_url:
            return f"🔍 **Search Results:**\n\n- **[{heading}]({source_url})**\n  {abstract}"
    except Exception:
        pass

    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            wiki_data = json.loads(response.read().decode('utf-8'))
            
        results = wiki_data.get("query", {}).get("search", [])
        if results:
            output = "🔍 **Search Results:**\n\n"
            for item in results[:3]:
                title = item.get("title")
                raw_snippet = item.get("snippet", "")
                clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet)
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                output += f"- **[{title}]({page_url})**\n  {clean_snippet}...\n\n"
            return output
    except Exception as e:
        return f"❌ Search Error: {str(e)}"

    return "🔍 No relevant information found."

# ==========================================
# 2. STREAMLIT UI DESIGN
# ==========================================

st.set_page_config(page_title="AI Tools Suite", page_icon="🤖", layout="wide")

st.title("🤖 AI Agent Interactive Suite")
st.caption("Powered by Groq LLM & Custom Python Tools")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 General Chat", 
    "🧮 Calculator", 
    "🕒 System Clock", 
    "🔍 Web Search", 
    "📄 PDF Generator"
])

# --- TAB 1: GROQ CHAT ---
with tab1:
    st.subheader("Interactive Groq AI Chat")

    if not GROQ_API_KEY:
        st.error("⚠️ `.env` file mein `GROQ_API_KEY` nahi mili. Please `.env` check karein.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! Main Groq AI hoon. Aap mujhse koi bhi baat pooch sakte hain!"}
            ]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Type your message..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                            model="openai/gpt-oss-120b",
                        )
                        reply = chat_completion.choices[0].message.content
                        st.markdown(reply)
                
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"❌ Groq Error: {str(e)}")

# --- TAB 2: CALCULATOR ---
with tab2:
    st.subheader("Math Calculator")
    expr = st.text_input("Enter Math Expression", "25 * 4 + 10")
    if st.button("Calculate Now", type="primary"):
        st.success(calculate(expr))

# --- TAB 3: SYSTEM CLOCK ---
with tab3:
    st.subheader("System Time")
    if st.button("Fetch Current Time"):
        st.info(get_system_time())

# --- TAB 4: WEB SEARCH ---
with tab4:
    st.subheader("Web Search")
    query = st.text_input("Enter Query", "Pakistan Cricket")
    if st.button("Search Web"):
        with st.spinner("Searching..."):
            st.markdown(web_search(query))

# --- TAB 5: PDF GENERATOR ---
with tab5:
    st.subheader("PDF Generator")
    col1, col2 = st.columns(2)
    with col1:
        fname = st.text_input("Filename", "report.pdf")
        title = st.text_input("Document Title", "Quarterly Report")
    with col2:
        content = st.text_area("Document Content", "Write your text here...")
    
    if st.button("Generate PDF"):
        st.success(create_pdf(fname, title, content))

st.sidebar.title("⚙️ System Status")
st.sidebar.success("Cloudflare Tunnel: Active")
st.sidebar.info("Model: openai/gpt-oss-120b")