import requests

BASE_URL = "http://127.0.0.1:8000"  # or 10.0.2.2 if using Android emulator

USER_ID = "testuser123"

def test_scrape_jobs():
    resp = requests.get(f"{BASE_URL}/jobs?job=python developer&location=Abudhabi")
    print("Scrape Jobs status:", resp.status_code)
    data = resp.json()
    print("Jobs found:", len(data.get("results", [])))

def test_save_job():
    sample_job = {
        "user_id": USER_ID,
        "title": "Python Developer",
        "company": "Acme Corp",
        "location": "Abudhabi",
        "summary": "Test summary",
        "description": "Test description",
        "skills": ["Python", "FastAPI"],
        "seniority": "Mid",
        "job_type": "Full-time"
    }
    resp = requests.post(f"{BASE_URL}/save-job", json=sample_job)
    print("Save Job status:", resp.status_code)
    print(resp.json())

def test_get_saved_jobs():
    resp = requests.get(f"{BASE_URL}/saved-jobs/{USER_ID}")
    print("Get Saved Jobs status:", resp.status_code)
    jobs = resp.json()
    print(f"Saved jobs count: {len(jobs)}")
    return jobs

def test_delete_job(job_id):
    resp = requests.delete(f"{BASE_URL}/saved-job/{job_id}?user_id={USER_ID}")
    print("Delete Job status:", resp.status_code)
    print(resp.json())

if __name__ == "__main__":
    print("===== Testing Scrape Jobs =====")
    test_scrape_jobs()

    print("\n===== Testing Save Job =====")
    test_save_job()

    print("\n===== Testing Get Saved Jobs =====")
    jobs = test_get_saved_jobs()

    if jobs:
        print("\n===== Testing Delete Job =====")
        test_delete_job(jobs[0]["id"])
