import os
import asyncio
from typing import List
from langchain_openai import OpenAIEmbeddings
from supabase_client import get_supabase_client

# Mock Data with Access Control Lists
DATA = [
    {
        "content": "The production deployment key is hidden in the ci-cd-secrets vault.",
        "allowed_roles": ["engineer"],
        "metadata": {"source": "engineering_guide.txt"}
    },
    {
        "content": "To reset the wifi password, visit 192.168.1.1/admin.",
        "allowed_roles": ["engineer", "intern"],
        "metadata": {"source": "it_guide.txt"}
    },
    {
        "content": "Employees are entitled to 4 weeks of paid vacation per year.",
        "allowed_roles": ["hr", "engineer", "intern"],
        "metadata": {"source": "employee_handbook.txt"}
    },
    {
        "content": "Executive bonuses are calculated as 5% of net profit.",
        "allowed_roles": ["hr"],
        "metadata": {"source": "executive_comp.txt"}
    },
    {
        "content": "Our public roadmap includes Q4 launch of the new API.",
        "allowed_roles": ["public", "intern", "engineer", "hr"], # effectively public
        "metadata": {"source": "public_web.txt"}
    }
]

async def seed_database():
    print("Initializing Seeding...")
    client = get_supabase_client()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 1. Clear existing documents (Optional, for clean state)
    # Be careful in real apps, this is just for PoC repeatability
    client.table("documents").delete().neq("id", -1).execute()
    
    print("Generating embeddings...")
    texts = [d["content"] for d in DATA]
    vectors = await embeddings.aembed_documents(texts)
    
    rows_to_insert = []
    for i, doc in enumerate(DATA):
        rows_to_insert.append({
            "content": doc["content"],
            "metadata": doc["metadata"],
            "allowed_roles": doc["allowed_roles"],
            "embedding": vectors[i]
        })
        
    print(f"Inserting {len(rows_to_insert)} documents...")
    client.table("documents").insert(rows_to_insert).execute()
    print("Seeding Complete!")

if __name__ == "__main__":
    # Check env vars
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY")
        exit(1)
    
    asyncio.run(seed_database())
