import streamlit as st
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase_client import secure_search

# Apply custom styling
st.set_page_config(page_title="IAM-Aware RAG PoC", layout="wide")

st.markdown("""
<style>
    .stChatMessage {
        background-color: #f0f2f6; 
        border-radius: 10px;
        padding: 1rem;
    }
    .stSidebar {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Application Title
st.title("🔒 IAM-Aware RAG System")
st.caption("Proof of Concept: RAG with Row-Level Security")

# --- SIDEBAR: "Auth" Simulation ---
with st.sidebar:
    st.header("👤 Persona Selector")
    st.info("Simulate logging in as different users to test permission boundaries.")
    
    selected_role = st.selectbox(
        "Current User Role",
        options=["engineer", "hr", "intern", "public"],
        index=0
    )
    
    st.divider()
    
    st.subheader("Your Permissions")
    if selected_role == "engineer":
        st.success("✅ Engineering Docs\n\n✅ Internal IT\n\n✅ Public Info")
    elif selected_role == "hr":
        st.success("✅ HR Policy\n\n✅ Salaries\n\n✅ Public Info")
    elif selected_role == "intern":
        st.warning("⚠️ Internal IT (Restricted)\n\n✅ Public Info")
    else:
        st.error("❌ Public Info Only")
        
    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []

# --- MAIN APP ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Logic
if prompt := st.chat_input("Ask a question..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. RAG Retrieval (The Secure Part)
    with st.spinner(f"Retrieving context as '{selected_role}'..."):
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            query_vector = embeddings.embed_query(prompt)
            
            # --- CRITICAL: Pass unique user identity/role to DB ---
            docs = secure_search(query_vector, selected_role)
            
            context_text = ""
            sources = []
            
            if not docs:
                context_text = "No relevant documents found that you are authorized to see."
            else:
                for doc in docs:
                    context_text += f"---\n{doc['content']}\n"
                    sources.append(doc['metadata'].get('source', 'unknown'))
                    
            # 3. Generation
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            
            template = """You are a helpful assistant. Use the following authorized context to answer the question.
            If the context is empty or irrelevant, say "I don't have access to information about that."
            
            Context:
            {context}
            
            Question: {question}
            """
            
            prompt_template = ChatPromptTemplate.from_template(template)
            chain = prompt_template | llm | StrOutputParser()
            
            response = chain.invoke({"context": context_text, "question": prompt})
            
            # 4. Assistant Message
            with st.chat_message("assistant"):
                st.markdown(response)
                if sources:
                    st.caption(f"📚 Sources used: {', '.join(set(sources))}")
                elif "I don't have access" in response:
                    st.caption("🔒 Access Denied / Content Hidden due to RLS")
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
