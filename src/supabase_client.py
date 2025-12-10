import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment variables.")
    return create_client(url, key)

def valid_role(role: str) -> bool:
    return role in ['engineer', 'hr', 'intern', 'public']

def secure_search(query_embedding: list, user_role: str, match_threshold: float = 0.5, match_count: int = 5):
    """
    Performs a vector search that respects the user_role via Postgres RLS.
    """
    if not valid_role(user_role):
        raise ValueError(f"Invalid role: {user_role}")
    
    client = get_supabase_client()
    
    # We call the RPC function 'match_documents' defined in schema.sql
    # This function safely sets the 'app.current_user_role' config 
    # and then executes the query within the same transaction.
    response = client.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
            "user_role": user_role
        }
    ).execute()
    
    return response.data
