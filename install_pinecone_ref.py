import urllib.request
import zipfile
import os
import shutil

url = "https://github.com/pinecone-io/pinecone-agents-ref/releases/latest/download/agents.zip"
zip_path = "agents.zip"

try:
    print(f"Downloading {url}...")
    # Use valid user agent just in case
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, zip_path)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")

    print("Merging documentation...")
    if os.path.exists("AGENTS-pinecone-snippet.md"):
        with open("AGENTS-pinecone-snippet.md", "r", encoding="utf-8") as src:
            content = src.read()
        
        # Determine if we need a newline (if AGENTS.md exists and lacks one)
        prefix = "\n"
        if not os.path.exists("AGENTS.md"):
            prefix = ""
            
        with open("AGENTS.md", "a", encoding="utf-8") as dst:
            dst.write(prefix + content)
        
        os.remove("AGENTS-pinecone-snippet.md")
        print("Merged and cleaned up snippet.")
    else:
        print("Snippet file not found after extraction. Contents of dir:")
        print(os.listdir("."))

    if os.path.exists(zip_path):
        os.remove(zip_path)
        print("Cleaned up zip file.")

    print("✅ Installation Complete.")

except Exception as e:
    print(f"❌ Error: {e}")
