from backend import job_store


def test_job_store_persists_and_filters_jobs(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_jobs.db"
    monkeypatch.setattr(job_store, "DB_PATH", test_db_path)

    job_store.init_job_store()

    job = job_store.create_indexing_job(
        "https://github.com/Palak123-coder/MiniSearchX"
    )

    job_store.update_job(
        job["job_id"],
        status="failed",
        error="clone failed",
        attempts=1,
        completed_at=job_store.current_timestamp(),
    )

    saved_job = job_store.get_job(job["job_id"])

    assert saved_job is not None
    assert saved_job["status"] == "failed"
    assert saved_job["error"] == "clone failed"
    assert saved_job["attempts"] == 1

    failed_jobs = job_store.list_jobs(status="failed")

    assert len(failed_jobs) == 1
    assert failed_jobs[0]["job_id"] == job["job_id"]