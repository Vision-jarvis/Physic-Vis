from src.knowledge.vector_store import get_pinecone_index
from src.core.llm import get_embeddings

def retrieve_docs(keywords):
    """
    Queries Pinecone for each keyword to get Definition + Examples.
    """
    if not keywords:
        return ""

    try:
        index = get_pinecone_index()
        embeddings = get_embeddings() # Uses Google models/embedding-001
    except Exception as e:
        print(f"   ⚠️ RAG Init Failed: {e}")
        return ""
    
    context_blocks = []
    
    # print(f"🔎 RAG Lookup: {keywords}")
    
    for term in keywords:
        try:
            vector = embeddings.embed_query(f"definition of {term}")
            
            # 1. Get Definition
            def_results = index.query(
                vector=vector, 
                top_k=1, 
                filter={"type": "definition", "class_name": term},
                include_metadata=True
            )
            
            # 2. Get Example (Crucial!)
            ex_results = index.query(
                vector=vector, 
                top_k=1, 
                filter={"type": "example", "class_name": term},
                include_metadata=True
            )
            
            # Format the context block
            if def_results['matches'] or ex_results['matches']:
                block = f"--- DOCS FOR: {term} ---\n"
                if def_results['matches']:
                    block += f"DEFINITION:\n{def_results['matches'][0]['metadata'].get('text', '')}\n"
                if ex_results['matches']:
                    block += f"EXAMPLE:\n{ex_results['matches'][0]['metadata'].get('text', '')}\n"
                context_blocks.append(block)
                
        except Exception as e:
            print(f"⚠️ RAG Error for '{term}': {e}")
            
    return "\n".join(context_blocks)
