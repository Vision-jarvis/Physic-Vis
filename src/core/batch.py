"""Batch LLM calls to reduce latency."""
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings
import asyncio
from typing import List, Dict, Any, Union

class BatchLLMProcessor:
    """
    Process multiple LLM requests in parallel using asyncio.gather.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.model_orchestrator
    
    async def batch_invoke_async(self, requests: List[Dict[str, Any]]) -> List[str]:
        """
        Process multiple LLM requests asynchronously.
        
        Args:
            requests: List of dicts, each containing:
                - messages: List[Dict] or str
                - temperature: float (optional)
                - system: str (optional, if using prompt templates)
        
        Returns:
            List of response strings in the same order.
        """
        tasks = []
        
        for req in requests:
            # Create a fresh LLM instance for each request to support different configs (temp)
            # This is lightweight in LangChain
            temperature = req.get("temperature", 0.7)
            
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=temperature,
                max_output_tokens=8192,
                google_api_key=settings.gemini_api_key
            )
            
            messages = req["messages"]
            
            # Async invoke
            task = llm.ainvoke(messages)
            tasks.append(task)
        
        # Wait for all tasks to complete concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract content
        results = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                print(f"  ❌ Batch request {i} failed: {resp}")
                results.append(f"ERROR: {str(resp)}")
            else:
                # Handle LangChain response format (Gemini 2.5/3.0 returns lists)
                raw_content = resp.content
                if isinstance(raw_content, list):
                    content = "".join([str(c) for c in raw_content])
                else:
                    content = str(raw_content)
                results.append(content)
        
        return results
    
    def batch_invoke(self, requests: List[Dict[str, Any]]) -> List[str]:
        """
        Synchronous wrapper for batch processing.
        Useful for running inside non-async graph nodes.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.batch_invoke_async(requests))
