import os
import requests
from bs4 import BeautifulSoup
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "manim-knowledge"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Target Documentation Pages (Module Indexes)
BASE_URL = "https://docs.manim.community/en/stable/reference.html"
ROOT_URL = "https://docs.manim.community/en/stable/"

def setup_pinecone():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)

def get_all_module_links(soup):
    """Finds all links to Manim modules from the reference page."""
    links = set()
    # Logic: Look for the big table of contents or sidebar
    # The reference page usually lists 'manim.animation', 'manim.camera', etc.
    
    # 1. Sidebar/TOC extraction
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('reference/manim.') and href.endswith('.html'):
             # Construct full URL
             if href.startswith('reference/'):
                 full_url = ROOT_URL + href
             else:
                 full_url = ROOT_URL + "reference/" + href
             links.add(full_url)
             
    # 2. Main content area links
    main_div = soup.find('div', role='main')
    if main_div:
        for a in main_div.find_all('a', href=True):
            href = a['href']
            # Heuristic for module pages
            if 'manim.' in href and href.endswith('.html'):
                # Avoid duplicates or anchors
                if '#' in href: href = href.split('#')[0]
                
                if href.startswith('manim.'):
                    full_url = ROOT_URL + "reference/" + href
                    links.add(full_url)
    
    return list(links)

def get_leaf_links(base_url, soup):
    """Extracts links to sub-module pages from proper autosummary tables."""
    links = set()
    
    # 1. Look for autosummary tables (listing sub-modules)
    tables = soup.find_all('table', class_='autosummary')
    for table in tables:
        for a in table.find_all('a', href=True):
            href = a['href']
            # Resolve relative links
            if href.startswith('#'): continue
            
            # Simple resolution for Manim docs structure
            # base: .../reference/manim.animation.html
            # href: manim.animation.creation.html
            # result: .../reference/manim.animation.creation.html
            
            root = base_url.rsplit('/', 1)[0]
            full_url = root + '/' + href
            links.add(full_url)
            
    return list(links)

    return list(links)

def scrape_page(url):
    """Scrapes a single page for Class definitions."""
    # print(f"   📄 Processing {url}...")
    try:
        headers = {'User-Agent': 'NewtonArchitect/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f"      ❌ Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sphinx uses <dl class="class"> for Python classes
        definitions = soup.find_all('dl', class_='class')
        
        # Also try <dl class="py class"> if exact match fails, or just iterate classes
        if not definitions:
             definitions = [dl for dl in soup.find_all('dl') if 'class' in dl.get('class', [])]

        results = []
        for definition in definitions:
            dt = definition.find('dt')
            dd = definition.find('dd')
            
            if dt and dd:
                # Name/ID lookups
                full_name = dt.get('id', '')
                if not full_name: continue # Skip if no ID
                
                # Signature extraction (text of dt, cleanup)
                signature = dt.get_text(" ", strip=True).replace('¶', '')
                
                # Docstring (First paragraph of dd)
                doc_p = dd.find('p')
                description = doc_p.get_text(strip=True) if doc_p else "No description."
                
                entry = {
                    "id": full_name,
                    "text": f"Manim Class: {full_name}\nSignature: {signature}\nDocs: {description}",
                    "metadata": {
                        "source": url,
                        "type": "class",
                        "name": full_name.split('.')[-1],
                        "full_signature": signature
                    }
                }
                results.append(entry)
                # print(f"      Found: {entry['metadata']['name']}")
        
        return results

    except Exception as e:
        print(f"      ❌ Error: {e}")
        return []

def scrape_docs():
    all_data = []
    visited_urls = set()
    
    print(f"🕷️ Starting Crawl from: {BASE_URL}")
    
    try:
        headers = {'User-Agent': 'NewtonArchitect/1.0'}
        response = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Discover all module pages
        # First level: Reference index
        module_urls = get_all_module_links(soup)
        print(f"   Found {len(module_urls)} top-level modules.")
        
        # 2. Add specific missing ones manually to be safe
        manual_additions = [
            "https://docs.manim.community/en/stable/reference/manim.mobject.text.tex_mobject.html",
            "https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.html",
            "https://docs.manim.community/en/stable/reference/manim.animation.fading.html",
            "https://docs.manim.community/en/stable/reference/manim.utils.rate_functions.html",
            "https://docs.manim.community/en/stable/reference/manim.camera.camera.html"
        ]
        module_urls.extend(manual_additions)
        
        # Deduplicate
        leaf_urls = set(module_urls)
        
        # 3. Recursive Crawl (Depth 1) - Check each module page for sub-classes
        # Many reference pages just list sub-pages. We need those too.
        final_urls = set()
        
        print("   🕸️ Expanding module links...")
        for url in list(leaf_urls):
            if url in visited_urls: continue
            visited_urls.add(url)
            
            try:
                # Add the page itself (might contain content)
                final_urls.add(url)
                
                # Check for sub-links (autosummary)
                resp = requests.get(url, headers=headers, timeout=5)
                s = BeautifulSoup(resp.content, 'html.parser')
                sub_links = get_leaf_links(url, s)
                if sub_links:
                    for sl in sub_links:
                        final_urls.add(sl)
            except Exception as e:
                # print(f"   ⚠️ Error expanding {url}: {e}")
                pass # Skip problematic modules without noise
                
    except Exception as e:
        print(f"❌ Failed crawl setup: {e}")
        return []

    # 4. Scrape all Discovered Pages
    print(f"📚 Exacting knowledge from {len(final_urls)} pages...")
    sorted_urls = sorted(list(final_urls))
    
    for i, url in enumerate(sorted_urls):
        if i % 10 == 0: print(f"   ... {i}/{len(final_urls)}")
        
        # Scrape with timeout too (handled in scrape_page but needs updating there too?)
        # Let's update scrape_page too
        pass
        
        page_data = scrape_page(url)
        all_data.extend(page_data)
        time.sleep(0.1) # Faster sleep
            
    return all_data

def ingest():
    print("🚀 Starting Manim Documentation Ingestion...")
    
    # 1. Scrape
    data = scrape_docs()
    print(f"✅ Scraped {len(data)} items.")
    
    if not data:
        print("⚠️ No data found. Check scraper selectors.")
        return

    # 2. Embed & Upsert
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
    
    # Prepare texts and metadatas
    texts = [item["text"] for item in data]
    metadatas = [item["metadata"] for item in data]
    
    # Using LangChain Wrapper for easy batching
    print("🧠 Vectorizing and Upserting to Pinecone...")
    PineconeVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        index_name=INDEX_NAME,
        metadatas=metadatas
    )
    
    print("🎉 Ingestion Complete!")

if __name__ == "__main__":
    setup_pinecone()
    ingest()
