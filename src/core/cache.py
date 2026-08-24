"""Smart caching to avoid redundant processing."""
import hashlib
import json
import os
from typing import Optional, Any, Dict
from functools import lru_cache

class CacheManager:
    """
    Multi-level cache for LLM responses and RAG results.
    Tier 1: In-Memory (Fastest, volatile)
    Tier 2: Disk (Fast, persistent)
    """
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # In-memory cache (fastest) - Key: Value
        self.memory_cache: Dict[str, Any] = {}
        
        # Disk cache directories
        self.llm_cache_dir = os.path.join(cache_dir, "llm")
        self.rag_cache_dir = os.path.join(cache_dir, "rag")
        os.makedirs(self.llm_cache_dir, exist_ok=True)
        os.makedirs(self.rag_cache_dir, exist_ok=True)
    
    def _generate_key(self, data: dict) -> str:
        """Generate MD5 cache key from data dictionary."""
        # Sort keys to ensure consistent hashing
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.md5(canonical.encode()).hexdigest()
    
    def get_llm_response(self, prompt: str, system_prompt: str, temperature: float, model_type: str = "pro") -> Optional[str]:
        """
        Get cached LLM response.
        Checks Memory -> Disk.
        """
        key = self._generate_key({
            "prompt": prompt,
            "system": system_prompt[:200],
            "temp": temperature,
            "model": model_type
        })
        
        # 1. Check memory
        if key in self.memory_cache:
            # print(f"  ⚡ Cache hit (memory): {key}")
            return self.memory_cache[key]
        
        # 2. Check disk
        cache_file = os.path.join(self.llm_cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            # print(f"  ⚡ Cache hit (disk): {key}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    response = data.get("response")
                    # Populate memory for next time
                    self.memory_cache[key] = response
                    return response
            except Exception as e:
                print(f"  ⚠️ Cache read error: {e}")
                return None
        
        return None
    
    def save_llm_response(self, prompt: str, system_prompt: str, temperature: float, response: str, model_type: str = "pro"):
        """Save LLM response to Memory and Disk."""
        key = self._generate_key({
            "prompt": prompt,
            "system": system_prompt[:200],
            "temp": temperature,
            "model": model_type
        })
        
        # Save to memory
        self.memory_cache[key] = response
        
        # Save to disk
        cache_file = os.path.join(self.llm_cache_dir, f"{key}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "prompt": prompt,
                    "response": response,
                    "temperature": temperature,
                    "system_truncated": system_prompt[:200]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ Cache write error: {e}")
    
    def get_rag_context(self, query: str, index_name: str) -> Optional[str]:
        """Get cached RAG retrieval result."""
        key = self._generate_key({"query": query, "index": index_name})
        
        if key in self.memory_cache:
             # print("  ⚡ RAG cache hit (memory)")
             return self.memory_cache[key]
        
        cache_file = os.path.join(self.rag_cache_dir, f"{key}.txt")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    context = f.read()
                    self.memory_cache[key] = context
                    return context
            except Exception:
                return None
        
        return None
    
    def save_rag_context(self, query: str, index_name: str, context: str):
        """Save RAG result to cache."""
        key = self._generate_key({"query": query, "index": index_name})
        
        self.memory_cache[key] = context
        
        cache_file = os.path.join(self.rag_cache_dir, f"{key}.txt")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(context)
        except Exception as e:
            print(f"  ⚠️ RAG cache write error: {e}")

    def clear(self):
        """Clear in-memory cache."""
        self.memory_cache.clear()

# Global Singleton Instance
cache_manager = CacheManager()

async def cached_llm_call(prompt: str, system_prompt: str, temperature: float = 0.7, model_type: str = "pro") -> str:
    """
    LLM call with automatic caching.
    Returns the RAW string content (JSON or text).
    """
    from src.core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # Check cache
    cached = cache_manager.get_llm_response(prompt, system_prompt, temperature, model_type=model_type)
    if cached:
        return cached
    
    # Call LLM
    llm = get_llm(model_type=model_type, temperature=temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = await llm.ainvoke(messages)
    content = response.content
    if isinstance(content, list): # Gemini 3.0 Fallback
        content = "".join([str(c) for c in content])
    
    # Save to cache
    cache_manager.save_llm_response(prompt, system_prompt, temperature, str(content), model_type=model_type)
    
    return str(content)

def cached_rag_retrieval(query: str, index_name: str, retriever_func) -> str:
    """
    RAG retrieval with caching.
    retriever_func: A Callable that takes the query and returns a string context.
    """
    # Check cache
    cached = cache_manager.get_rag_context(query, index_name)
    if cached:
        return cached
    
    # Retrieve
    try:
        context = retriever_func(query)
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
        return ""
    
    # Save to cache
    cache_manager.save_rag_context(query, index_name, context)
    
    return context
