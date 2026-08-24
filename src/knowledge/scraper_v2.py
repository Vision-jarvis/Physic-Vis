import requests
from bs4 import BeautifulSoup
import time
import json
import os

BASE_URL = "https://docs.manim.community/en/stable/reference.html"
ROOT_URL = "https://docs.manim.community/en/stable/"

HEADERS = {'User-Agent': 'ManimRAGBuilder/1.0'}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def extract_class_content(soup, url):
    """
    Extracts Semantic Units (Definition, Examples, Methods) from a page.
    Assumes the page might contain one or more class definitions.
    """
    items = []
    
    # Sphinx class definitions
    class_blocks = soup.find_all('dl', class_='class')
    
    for cls in class_blocks:
        dt = cls.find('dt')
        dd = cls.find('dd')
        
        if not dt or not dd:
            continue
            
        full_id = dt.get('id', '')
        if not full_id:
            continue
            
        class_name = full_id.split('.')[-1]
        module_name = '.'.join(full_id.split('.')[:-1])
        
        # --- Unit A: Definition ---
        # Signature often contains "class manim.animation..." 
        # We want to capture the clean signature
        signature = dt.get_text(" ", strip=True).replace('¶', '')
        
        # Get Docstring
        # The docstring is usually the text content of dd, but excluding the nested dl (methods)
        # and excluding the "Bases: object" line if present.
        
        desc_text = ""
        # We try to get text nodes directly or just the first few paragraphs
        # A robust way is to get all text, then split by "Bases:" or just clean it.
        
        desc_text = dd.get_text("\n", strip=True)
        
        # Clean "Bases:" noise
        if "Bases:" in desc_text:
            try:
                # Often "Bases: object\n\nActual description..."
                parts = desc_text.split("Bases:")
                if len(parts) > 1:
                    # usage of part[1] which is everything after Bases:
                    after_bases = parts[1]
                    # The first line usually contains the base class list, the rest is docs
                    lines = after_bases.split("\n")
                    if len(lines) > 1:
                        desc_text = "\n".join(lines[1:]).strip()
                    else:
                        desc_text = after_bases.strip()
            except:
                pass # Fallback to full text if split fails safely
                
        # Truncate if extremely long (e.g. if it accidentally captured all methods)
        # But 'dd' includes methods in Sphinx structure often! 
        # Wait, in Sphinx, <dl class="method"> is often *inside* <dd> of the class.
        # So dd.get_text() WILL capture all methods. This is bad.
        # We need to get text ONLY from the direct children of dd that are logic (p, ul) specific to class.
        
        direct_desc_lines = []
        for child in dd.children:
            if child.name in ['p', 'ul', 'ol', 'span']:
                direct_desc_lines.append(child.get_text(strip=True))
            elif child.name == 'dl': 
                # Stop when we hit the method list
                break
                
        if direct_desc_lines:
             desc_text = "\n".join(direct_desc_lines)
        
        # Final clean
        desc_text = desc_text.replace("Bases: object", "").strip()

        items.append({
            "text": f"DEFINITION of {class_name}:\nSignature: {signature}\nDescription: {desc_text}",
            "metadata": {
                "id": full_id,
                "type": "definition",
                "class_name": class_name,
                "module": module_name,
                "source": url
            }
        })
        
        # --- Unit B: Examples ---
        # Look for code blocks. Sphinx puts them in 'div.highlight-python'
        # We need to ensure we don't grab examples from nested methods if we want to separate them?
        # Actually, examples in methods should probably be attributed to the method.
        # For now, let's grab all examples in the class dd. 
        # Tagging them with class_name is still correct.
        
        examples = dd.find_all('div', class_='highlight-python')
        for i, example in enumerate(examples):
            code_text = example.get_text()
            if len(code_text.strip()) > 20: 
                items.append({
                    "text": f"Example for {class_name}:\n{code_text}",
                    "metadata": {
                        "id": f"{full_id}_example_{i}",
                        "type": "example",
                        "class_name": class_name,
                        "module": module_name,
                        "source": url
                    }
                })
        
        # --- Unit C: Methods ---
        methods = dd.find_all('dl', class_='method')
        for method in methods:
            m_dt = method.find('dt')
            m_dd = method.find('dd')
            
            if m_dt and m_dd:
                m_id = m_dt.get('id', '')
                if not m_id: continue
                
                method_name = m_id.split('.')[-1]
                
                # FILTER: Skip private methods (but keep __init__ if useful?)
                # User requested: if method_name.startswith("_") and not method_name.startswith("__init__"): continue
                if method_name.startswith('_') and method_name != '__init__':
                    continue
                    
                m_sig = m_dt.get_text(" ", strip=True).replace('¶', '')
                
                # Extract method docs - similar logic to class docs (direct children)
                m_desc_lines = []
                for child in m_dd.children:
                    if child.name in ['p']:
                         m_desc_lines.append(child.get_text(strip=True))
                m_desc = "\n".join(m_desc_lines)
                
                # Contextual Signature
                # Convert "add(*mobjects)" to "Scene.add(*mobjects)"
                # m_sig usually looks like "add(mobject, ...)"
                # We prepend class name for clarity in embedding
                context_sig = f"{class_name}.{m_sig}"

                items.append({
                    "text": f"Method: {context_sig}\nDescription: {m_desc}",
                    "metadata": {
                        "id": m_id,
                        "type": "method",
                        "class_name": class_name,
                        "module": module_name,
                        "source": url
                    }
                })
                
    return items

def crawl():
    print(f"🕷️ Starting Crawl at {BASE_URL}")
    soup = get_soup(BASE_URL)
    if not soup:
        return []

    # 1. Get Module Links
    module_urls = set()
    # Find links in the main content that look like modules
    # Manim modules usually start with 'reference/manim.'
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'manim.' in href and href.endswith('.html'):
            full_url = requests.compat.urljoin(BASE_URL, href)
            # Remove anchors
            full_url = full_url.split('#')[0]
            module_urls.add(full_url)
            
    print(f"   Found {len(module_urls)} modules.")
    
    all_data = []
    visited = set()
    
    # Process each module
    sorted_modules = sorted(list(module_urls))
    
    # Optimization: Filter for core modules if needed, but we'll try all
    # sorted_modules = [u for u in sorted_modules if 'manim.animation' in u or 'manim.mobject' in u]
    
    for i, mod_url in enumerate(sorted_modules):
        if mod_url in visited: continue
        visited.add(mod_url)
        
        print(f"   [{i+1}/{len(sorted_modules)}] Processing Module: {mod_url.split('/')[-1]}")
        mod_soup = get_soup(mod_url)
        if not mod_soup: continue
        
        # 1. Scrape content from the Module page itself
        # (Some classes are defined right here)
        page_items = extract_class_content(mod_soup, mod_url)
        all_data.extend(page_items)
        if page_items:
            print(f"      + Found {len(page_items)} items on module page.")
            
        # 2. Look for Child Pages (Classes)
        # Usually in tables with class="autosummary"
        child_urls = set()
        tables = mod_soup.find_all('table', class_='autosummary')
        for table in tables:
            for a in table.find_all('a', href=True):
                c_href = a['href']
                c_full_url = requests.compat.urljoin(mod_url, c_href)
                c_full_url = c_full_url.split('#')[0]
                
                # Verify it's not the same page and correct domain
                if c_full_url != mod_url and ROOT_URL in c_full_url:
                    child_urls.add(c_full_url)

        # Visit Child URLs
        for child_url in child_urls:
            if child_url in visited: continue
            visited.add(child_url)
            
            # print(f"      -> Visiting Class Page: {child_url.split('/')[-1]}")
            child_soup = get_soup(child_url)
            if child_soup:
                child_items = extract_class_content(child_soup, child_url)
                all_data.extend(child_items)
                time.sleep(0.1) 
        
        time.sleep(0.2)

    return all_data

if __name__ == "__main__":
    data = crawl()
    print(f"✅ Crawl Complete. Total items: {len(data)}")
    
    # Save to file
    with open("manim_knowledge_v2.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Saved to manim_knowledge_v2.json")
