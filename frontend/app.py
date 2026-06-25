import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="RepoPilot AI",
    page_icon="🔎",
    layout="wide"
)


def call_get(endpoint: str):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=60)
        return response.status_code, response.json()
    except requests.exceptions.RequestException as error:
        return 500, {"detail": str(error)}


def call_post(endpoint: str, payload: dict, timeout: int = 300):
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=timeout
        )
        return response.status_code, response.json()
    except requests.exceptions.RequestException as error:
        return 500, {"detail": str(error)}


st.title("RepoPilot AI")
st.caption(
    "RAG-based codebase intelligence system for indexing GitHub repositories, "
    "searching code, and answering developer questions with source references."
)

st.divider()

# Sidebar
st.sidebar.header("Backend Configuration")
api_url_input = st.sidebar.text_input(
    "FastAPI Backend URL",
    value=API_BASE_URL
)

if api_url_input.strip():
    API_BASE_URL = api_url_input.strip()

status_code, status_data = call_get("/status")

st.sidebar.subheader("Backend Status")
if status_code == 200:
    st.sidebar.success("Backend connected")
    st.sidebar.write(f"Status: `{status_data.get('status')}`")
else:
    st.sidebar.error("Backend not reachable")
    st.sidebar.write(status_data)

# Repository indexing
st.header("1. Index Repository")

repo_url = st.text_input(
    "GitHub Repository URL",
    value="https://github.com/Palak123-coder/MiniSearchX"
)

index_col_1, index_col_2 = st.columns([1, 3])

with index_col_1:
    index_button = st.button("Index Repository", type="primary")

if index_button:
    with st.spinner("Cloning repository, parsing files, chunking code, and creating embeddings..."):
        status_code, index_response = call_post(
            "/index",
            {"repo_url": repo_url},
            timeout=600
        )

    if status_code == 200:
        st.success("Repository indexed successfully")
        st.session_state["index_response"] = index_response
    else:
        st.error("Indexing failed")
        st.json(index_response)

if "index_response" in st.session_state:
    index_response = st.session_state["index_response"]

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Files Indexed", index_response.get("files_indexed", 0))
    metric_2.metric("Chunks Indexed", index_response.get("chunks_indexed", 0))
    metric_3.metric("Indexing Time", f"{index_response.get('indexing_time_ms', 0)} ms")

    with st.expander("Index Response JSON"):
        st.json(index_response)

st.divider()

# Current status
st.header("2. Repository Status")

refresh_status = st.button("Refresh Status")

if refresh_status:
    status_code, status_data = call_get("/status")

if status_code == 200:
    status_1, status_2, status_3, status_4 = st.columns(4)

    status_1.metric("Status", status_data.get("status", "unknown"))
    status_2.metric("Files", status_data.get("files_indexed", 0))
    status_3.metric("Chunks", status_data.get("chunks_indexed", 0))
    status_4.metric("Index Time", f"{status_data.get('indexing_time_ms', 0)} ms")

    with st.expander("Full Status JSON"):
        st.json(status_data)
else:
    st.error("Could not fetch status")
    st.json(status_data)

st.divider()

# Search tabs
st.header("3. Search and Ask")

tab_keyword, tab_semantic, tab_ask = st.tabs(
    ["Keyword Search", "Semantic Search", "RAG Ask"]
)


with tab_keyword:
    st.subheader("Keyword Search")

    keyword_query = st.text_input(
        "Keyword query",
        value="multithreading synchronization",
        key="keyword_query"
    )

    keyword_top_k = st.slider(
        "Top K results",
        min_value=1,
        max_value=10,
        value=5,
        key="keyword_top_k"
    )

    if st.button("Run Keyword Search"):
        with st.spinner("Running keyword search..."):
            status_code, keyword_response = call_post(
                "/search",
                {
                    "query": keyword_query,
                    "top_k": keyword_top_k
                }
            )

        if status_code == 200:
            st.success("Keyword search completed")
            st.metric("Query Latency", f"{keyword_response.get('query_latency_ms', 0)} ms")

            for index, result in enumerate(keyword_response.get("results", []), start=1):
                with st.expander(f"{index}. {result.get('path')} | Score: {result.get('score')}"):
                    st.write(result.get("snippet", ""))
        else:
            st.error("Keyword search failed")
            st.json(keyword_response)


with tab_semantic:
    st.subheader("Semantic Search")

    semantic_query = st.text_input(
        "Semantic query",
        value="Where is synchronization handled in this project?",
        key="semantic_query"
    )

    semantic_top_k = st.slider(
        "Top K results",
        min_value=1,
        max_value=10,
        value=5,
        key="semantic_top_k"
    )

    if st.button("Run Semantic Search"):
        with st.spinner("Running semantic search..."):
            status_code, semantic_response = call_post(
                "/semantic-search",
                {
                    "query": semantic_query,
                    "top_k": semantic_top_k
                }
            )

        if status_code == 200:
            st.success("Semantic search completed")
            st.metric("Query Latency", f"{semantic_response.get('query_latency_ms', 0)} ms")

            for index, result in enumerate(semantic_response.get("results", []), start=1):
                path = result.get("path")
                chunk_index = result.get("chunk_index")
                distance = result.get("distance")

                with st.expander(
                    f"{index}. {path} | Chunk: {chunk_index} | Distance: {distance}"
                ):
                    st.write(result.get("snippet", ""))
        else:
            st.error("Semantic search failed")
            st.json(semantic_response)


with tab_ask:
    st.subheader("RAG-Based Question Answering")

    question = st.text_area(
        "Ask a question about the indexed repository",
        value="Where is synchronization handled in this project?",
        height=100
    )

    ask_top_k = st.slider(
        "Retrieved chunks",
        min_value=1,
        max_value=10,
        value=5,
        key="ask_top_k"
    )

    if st.button("Ask RepoPilot AI", type="primary"):
        with st.spinner("Retrieving relevant chunks and generating grounded answer..."):
            status_code, ask_response = call_post(
                "/ask",
                {
                    "question": question,
                    "top_k": ask_top_k
                },
                timeout=300
            )

        if status_code == 200:
            st.success("Answer generated")
            st.metric("Answer Latency", f"{ask_response.get('answer_latency_ms', 0)} ms")

            st.subheader("Answer")
            st.write(ask_response.get("answer", ""))

            st.subheader("Sources")
            sources = ask_response.get("sources", [])

            if sources:
                st.dataframe(sources, use_container_width=True)
            else:
                st.info("No sources returned.")

            with st.expander("Full Ask Response JSON"):
                st.json(ask_response)
        else:
            st.error("RAG answer generation failed")
            st.json(ask_response)

st.divider()

st.caption(
    "RepoPilot AI demonstrates repository parsing, semantic retrieval, vector search, "
    "RAG answer generation, source attribution, and latency tracking."
)