"""
Semantic Document Search - Streamlit Frontend
A simple AI-powered document search application.
"""

import streamlit as st
import requests
import os

# Configuration
API_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

# Page configuration
st.set_page_config(
    page_title="Semantic Document Search",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white !important;
        margin: 0 !important;
    }
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
    }
    /* Better text visibility in expanders */
    .stExpander {
        background: rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
    }
    .stExpander p, .stExpander span, .stExpander div {
        color: #ffffff !important;
    }
    .stMarkdown p {
        color: #e0e0e0 !important;
    }
    /* Make content text more readable */
    pre {
        background: rgba(0,0,0,0.3) !important;
        color: #f0f0f0 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)



def check_api_health():
    """Check if backend is running with retry logic"""
    import time
    
    # Try multiple times (backend might be starting up)
    for attempt in range(3):
        try:
            resp = requests.get(f"{API_URL}/health", timeout=5)
            if resp.status_code == 200:
                return True, resp.json()
        except:
            pass
        
        # Wait before retry (except on last attempt)
        if attempt < 2:
            time.sleep(2)
    
    return False, {}


def upload_document(file):
    """Upload a document"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        resp = requests.post(f"{API_URL}/documents/upload", files=files, timeout=300)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def search_documents(query, top_k=5):
    """Search documents"""
    try:
        resp = requests.post(
            f"{API_URL}/search",
            json={"query": query, "top_k": top_k},
            timeout=30
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_documents():
    """Get list of documents"""
    try:
        resp = requests.get(f"{API_URL}/documents", timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []


def delete_document(doc_id):
    """Delete a document"""
    try:
        resp = requests.delete(f"{API_URL}/documents/{doc_id}", timeout=10)
        return resp.status_code == 200
    except:
        return False


def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Semantic Document Search</h1>
        <p>Upload documents and find content by meaning, not just keywords</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API health
    is_healthy, health_info = check_api_health()
    
    if not is_healthy:
        st.error("""
        ⚠️ **Backend is not running!**
        
        Start it with: `python run.py`
        """)
        return
    
    # Sidebar - Document Management
    with st.sidebar:
        st.markdown("## 📁 Documents")
        
        # Upload
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["pdf", "txt"],
            help="PDF or TXT files"
        )
        
        if uploaded_file:
            with st.spinner("⏳ Processing..."):
                result = upload_document(uploaded_file)
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ Uploaded! ({result.get('chunk_count', 0)} chunks)")
                st.rerun()
        
        st.markdown("---")
        
        # Document list
        documents = get_documents()
        st.markdown(f"### 📄 Your Documents ({len(documents)})")
        
        if not documents:
            st.info("No documents yet. Upload one above!")
        else:
            for doc in documents:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {doc['filename'][:20]}...")
                    st.caption(f"{doc['chunk_count']} chunks")
                with col2:
                    if st.button("🗑️", key=f"del_{doc['id']}"):
                        delete_document(doc['id'])
                        st.rerun()
        
        st.markdown("---")
        
        # Stats
        chunks = health_info.get("services", {}).get("chunks_indexed", 0)
        st.metric("Total Chunks", chunks)
    
    # Main content - Search
    st.markdown("## 🔍 Search")
    
    # Initialize session state for search
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        query = st.text_input(
            "Enter your search query",
            placeholder="e.g., What is machine learning?",
            label_visibility="collapsed",
            key="search_query"
        )
    with col2:
        top_k = st.selectbox("Results", [3, 5, 10], index=1, label_visibility="collapsed")
    with col3:
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Run search when button clicked or Enter pressed (query changed)
    if search_clicked and query:
        with st.spinner("🔍 Searching..."):
            st.session_state.search_results = search_documents(query, top_k)
            st.session_state.last_query = query
    
    # Display results
    results = st.session_state.search_results
    if results:
        if "error" in results:
            st.error(f"❌ {results['error']}")
        elif results.get("total_results", 0) == 0:
            st.warning("No results found. Try a different query or upload more documents.")
        else:
            st.markdown(f"### Found {results['total_results']} results for '{st.session_state.last_query}'")
            
            for i, result in enumerate(results["results"], 1):
                score = result["similarity_score"]
                score_pct = int(score * 100)
                
                # Color based on score
                if score > 0.7:
                    color = "🟢"
                elif score > 0.4:
                    color = "🟡"
                else:
                    color = "🔴"
                
                with st.expander(f"{color} **Result {i}** - {result['filename']} ({score_pct}% match)", expanded=(i <= 3)):
                    st.markdown(f"📊 **Similarity:** {score_pct}%")
                    st.markdown("📄 **Content:**")
                    content = result["content"][:600] + ("..." if len(result["content"]) > 600 else "")
                    st.code(content, language=None)
    
    elif not query:
        # Show instructions
        st.info("""
        👆 **How to use:**
        1. Upload documents in the sidebar (PDF or TXT)
        2. Type a search query above
        3. Click the **Search** button
        
        Unlike keyword search, semantic search finds content by **meaning**.
        For example, searching "AI" will also find content about "machine learning" or "neural networks".
        """)


if __name__ == "__main__":
    main()

