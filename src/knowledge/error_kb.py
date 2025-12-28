import json
import hashlib
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

from src.core.llm import get_embeddings

load_dotenv()

INDEX_NAME = "error-healing"

class ErrorKnowledgeBase:
    """
    Stores error patterns and their solutions in Pinecone.
    Uses semantic search to find similar past errors.
    """
    
    def __init__(self, storage_path: str = "src/knowledge/data/errors"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Keep local log for raw error history (analytics)
        self.errors_file = self.storage_path / "error_log.jsonl"
        
        # Initialize embedding client
        self.embedding_client = get_embeddings()
        
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("❌ Error: PINECONE_API_KEY NOT FOUND in .env")
            self.pc = None
            self.index = None
            return

        self.pc = Pinecone(api_key=api_key)
        
        # Check/Create Index
        self._ensure_index()
        self.index = self.pc.Index(INDEX_NAME)
    
    def _ensure_index(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            existing_indexes = [i.name for i in self.pc.list_indexes()]
            if INDEX_NAME not in existing_indexes:
                print(f"📦 Creating Pinecone index '{INDEX_NAME}'...")
                self.pc.create_index(
                    name=INDEX_NAME, 
                    dimension=768, # Dimension for models/embedding-001
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                time.sleep(10) # Wait for initialization
        except Exception as e:
            print(f"⚠️ Pinecone Index Error: {e}")

    def log_error(self, error_data: Dict):
        """
        Log an error locally for analytics.
        """
        try:
            # Create unique error ID based on error message
            error_id = self._hash_error(error_data['error_message'])
            
            entry = {
                'error_id': error_id,
                'timestamp': datetime.now().isoformat(),
                **error_data
            }
            
            # Append to log
            with open(self.errors_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"⚠️ Failed to log error locally: {e}")
    
    def log_successful_fix(self, fix_data: Dict):
        """
        Upsert a successful fix to Pinecone.
        """
        if not self.index:
            return

        if 'original_error' not in fix_data or not fix_data['original_error']:
             return

        error_id = self._hash_error(fix_data['original_error'])
        
        # Get embedding
        embedding = self._get_embedding(fix_data['original_error'])
        if embedding is None:
            return

        metadata = {
            "original_error": fix_data['original_error'],
            "original_code": fix_data.get('original_code', '')[:40000], # Limit size for metadata
            "fixed_code": fix_data['fixed_code'][:40000],
            "fix_method": fix_data.get('fix_method', 'unknown'),
            "attempts": fix_data.get('attempts', 1),
            "topic": fix_data.get('topic', 'General'),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.index.upsert(vectors=[{
                "id": error_id,
                "values": embedding.tolist(),
                "metadata": metadata
            }])
            print(f"🧠 Learned new error fix! ID: {error_id}")
        except Exception as e:
            print(f"❌ Failed to upsert to Pinecone: {e}")
    
    def find_similar_fix(self, error_message: str, threshold: float = 0.85) -> Optional[Dict]:
        """
        Query Pinecone for a similar past fix.
        """
        if not self.index:
            return None

        embedding = self._get_embedding(error_message)
        if embedding is None:
            return None
            
        try:
            results = self.index.query(
                vector=embedding.tolist(),
                top_k=1,
                include_metadata=True
            )
            
            if not results.matches:
                return None
                
            match = results.matches[0]
            if match.score < threshold:
                return None
                
            return {
                'similarity': match.score,
                'fixed_code': match.metadata.get('fixed_code'),
                'fix_method': match.metadata.get('fix_method'),
                'original_error': match.metadata.get('original_error'),
                'confidence': match.score
            }
        except Exception as e:
            print(f"⚠️ Pinecone Query Error: {e}")
            return None
    
    def _hash_error(self, error_message: str) -> str:
        """
        Create a deterministic hash for an error message.
        """
        normalized = str(error_message).lower().strip()
        import re
        normalized = re.sub(r'line \d+', 'line X', normalized)
        normalized = re.sub(r'/app/scene_\w+\.py', '/app/scene_X.py', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for text using LangChain Google Embeddings.
        """
        try:
            embedding = self.embedding_client.embed_query(text)
            return np.array(embedding)
        except Exception as e:
            print(f"⚠️ Embedding Error: {e}")
            return None
