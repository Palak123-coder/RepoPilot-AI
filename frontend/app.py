import time
import requests
import streamlit as st

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RepoPilot AI",
    page_icon="🔎",
    layout="wide"
)

def call_get(api_base_url: str, endpoint: str, timeout: int = 60):
    try:
        response = requests.get(f"{api_base_url}{endpoint}", timeout=timeout)
        return response.status_code, response.json()
    except requests.exceptions.RequestException as error:
        return 500, {"detail": str(error)}

def call_post(api_base_url: str, endpoint: str, payload: dict, timeout: int = 300):
    try:
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=payload,
            timeout=timeout
        )
        return response.status_code, response.json()
    except requests.exceptions.RequestException as error:
        return 500, {"detail": str(error)}

def render_job_metrics(job_data: dict):
    job_status = job_data.get("status", "unknown")

    col_1, col_2, col_3, col_4 = st.columns(4)

    col_1.metric("Job Status", job_status)
    col_2.metric("Files Indexed", job_data.get("files_indexed", 0))
    col_3.metric("Chunks Indexed", job_data.get("chunks_indexed", 0))
    col_4.metric("Indexing Time", f"{job_data.get('indexing_time_ms', 0)} ms")

    if job_status == "completed":
        st.success("Background indexing job completed successfully")
    elif job_status == "running":
        st.info("Background indexing job is running")
    elif job_status == "pending":
        st.warning("Background indexing job is pending")
    elif job_status == "failed":
        st.error("Background indexing job failed")
        st.write(job_data.get("error"))

def poll_job_until_done(api_base_url: str, job_id: str):
    status_area = st.empty()
    json_area = st.empty()

    latest_job_data = None

    for _ in range(90):
        status_code, job_data = call_get(
            api_base_url,
            f"/jobs/{job_id}",
            timeout=60
        )

        if status_code != 200:
            status_area.error("Could not fetch job status")
            json_area.json(job_data)
            return None

        latest_job_data = job_data
        job_status = job_data.get("status", "unknown")

        with status_area.container():
            st.subheader("Live Job Status")
            st.write(f"Job ID: `{job_id}`")
            render_job_metrics(job_data)

        with json_area.container():
            with st.expander("Job Response JSON", expanded=False):
                st.json(job_data)

        if job_status in ["completed", "failed"]:
            return job_data

        time.sleep(2)

    status_area.warning(
        "Polling stopped after timeout. Please refresh job status manually."
    )

    return latest_job_data

st.title("RepoPilot AI")
st.caption(
    "RAG-based codebase intelligence system for indexing GitHub repositories, "
    "searching code, and answering developer questions with source references."
)

st.divider()

# Sidebar

st.sidebar.header("Backend Configuration")

api_base_url = st.sidebar.text_input(
    "FastAPI Backend URL",
    value=DEFAULT_API_BASE_URL
).strip()

if not api_base_url:
    api_base_url = DEFAULT_API_BASE_URL

status_code, status_data = call_get(api_base_url, "/status")

st.sidebar.subheader("Backend Status")

if status_code == 200:
    st.sidebar.success("Backend connected")
    st.sidebar.write(f"Status: `{status_data.get('status')}`")
else:
    st.sidebar.error("Backend not reachable")
    st.sidebar.write(status_data)

# Repository indexing through background jobs

st.header("1. Index Repository with Background Job")

repo_url = st.text_input(
    "GitHub Repository URL",
    value="https://github.com/Palak123-coder/MiniSearchX"
)

index_col_1, index_col_2 = st.columns([1, 4])

with index_col_1:
    start_job_button = st.button("Start Indexing Job", type="primary")

with index_col_2:
    st.caption(
        "This starts /index-job, returns a job_id immediately, "
        "and polls /jobs/{job_id} until completion."
    )

if start_job_button:
    with st.spinner("Starting background indexing job..."):
        status_code, job_response = call_post(
            api_base_url,
            "/index-job",
            {"repo_url": repo_url},
            timeout=60
        )

    if status_code == 200:
        job_id = job_response.get("job_id")

        st.session_state["active_job_id"] = job_id
        st.session_state["job_start_response"] = job_response

        st.success("Indexing job started")
        st.write(f"Job ID: `{job_id}`")

        with st.expander("Index Job Start Response JSON", expanded=False):
            st.json(job_response)

        with st.spinner("Polling job status..."):
            completed_job_data = poll_job_until_done(api_base_url, job_id)

        if completed_job_data:
            st.session_state["latest_job_data"] = completed_job_data

    else:
        st.error("Could not start indexing job")
        st.json(job_response)

if "active_job_id" in st.session_state:
    st.subheader("Latest Job")

    active_job_id = st.session_state["active_job_id"]
    st.write(f"Active Job ID: `{active_job_id}`")

    refresh_job = st.button("Refresh Latest Job Status")

    if refresh_job:
        status_code, job_data = call_get(
            api_base_url,
            f"/jobs/{active_job_id}",
            timeout=60
        )

        if status_code == 200:
            st.session_state["latest_job_data"] = job_data
        else:
            st.error("Could not refresh job status")
            st.json(job_data)

if "latest_job_data" in st.session_state:
    latest_job_data = st.session_state["latest_job_data"]

    render_job_metrics(latest_job_data)

    with st.expander("Latest Job JSON", expanded=False):
        st.json(latest_job_data)

st.divider()

# Current repository status

st.header("2. Repository Status")

refresh_status = st.button("Refresh Repository Status")

if refresh_status:
    status_code, status_data = call_get(
        api_base_url,
        "/status",
        timeout=60
    )

    if status_code == 200:
        status_col_1, status_col_2, status_col_3, status_col_4 = st.columns(4)

        status_col_1.metric("Status", status_data.get("status", "unknown"))
        status_col_2.metric("Files", status_data.get("files_indexed", 0))
        status_col_3.metric("Chunks", status_data.get("chunks_indexed", 0))
        status_col_4.metric(
            "Index Time",
            f"{status_data.get('indexing_time_ms', 0)} ms"
        )

        with st.expander("Full Status JSON", expanded=False):
            st.json(status_data)

    else:
        st.error("Could not fetch repository status")
        st.json(status_data)

st.divider()

# Background job history

st.header("3. Background Job History")

job_history_button = st.button("Load Job History")

if job_history_button:
    status_code, jobs_response = call_get(
        api_base_url,
        "/jobs",
        timeout=60
    )

    if status_code == 200:
        jobs = jobs_response.get("jobs", [])

        st.metric("Total Jobs", jobs_response.get("total_jobs", 0))

        if jobs:
            st.dataframe(jobs, use_container_width=True)
        else:
            st.info("No jobs found in the current backend session.")

        with st.expander("Jobs Response JSON", expanded=False):
            st.json(jobs_response)
    else:
        st.error("Could not load job history")
        st.json(jobs_response)

st.divider()

# Search and RAG tabs

st.header("4. Search and Ask")

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
                api_base_url,
                "/search",
                {
                    "query": keyword_query,
                    "top_k": keyword_top_k
                },
                timeout=120
            )

        if status_code == 200:
            st.success("Keyword search completed")
            st.metric(
                "Query Latency",
                f"{keyword_response.get('query_latency_ms', 0)} ms"
            )

            for index, result in enumerate(
                keyword_response.get("results", []),
                start=1
            ):
                path = result.get("path")
                score = result.get("score")

                with st.expander(f"{index}. {path} | Score: {score}"):
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
                api_base_url,
                "/semantic-search",
                {
                    "query": semantic_query,
                    "top_k": semantic_top_k
                },
                timeout=120
            )

        if status_code == 200:
            st.success("Semantic search completed")
            st.metric(
                "Query Latency",
                f"{semantic_response.get('query_latency_ms', 0)} ms"
            )

            for index, result in enumerate(
                semantic_response.get("results", []),
                start=1
            ):
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
        with st.spinner(
            "Retrieving relevant chunks and generating grounded answer..."
        ):
            status_code, ask_response = call_post(
                api_base_url,
                "/ask",
                {
                    "question": question,
                    "top_k": ask_top_k
                },
                timeout=300
            )

        if status_code == 200:
            st.success("Answer generated")
            st.metric(
                "Answer Latency",
                f"{ask_response.get('answer_latency_ms', 0)} ms"
            )

            st.subheader("Answer")
            st.write(ask_response.get("answer", ""))

            st.subheader("Sources")
            sources = ask_response.get("sources", [])

            if sources:
                st.dataframe(sources, use_container_width=True)
            else:
                st.info("No sources returned.")

            with st.expander("Full Ask Response JSON", expanded=False):
                st.json(ask_response)
        else:
            st.error("RAG answer generation failed")
            st.json(ask_response)

st.divider()

st.caption(
    "RepoPilot AI demonstrates repository parsing, semantic retrieval, vector search, "
    "RAG answer generation, source attribution, background job tracking, and latency monitoring."
)