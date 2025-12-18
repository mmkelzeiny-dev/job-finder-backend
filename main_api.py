# from google.auth.transport.requests import Request
# from google.auth.jwt import Client
from fastapi import FastAPI, Form, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer # For Bearer token structurer  # For Bearer token structur
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal, getcontext
import asyncio
import json
# from google.oauth2 import id_token
# from google.auth.transport import requests
import jwt as pyjwt
from jwt import PyJWTError  # For catching JWT errors
from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine, Base
from models import SavedJob
from indeed_scraper import scrape_jobs
from ai_integration import process_all_jobs, save_to_csv
import logging
from google.auth.transport import requests
from google.auth.transport.requests import Request # This is still correct for the Request object
# from google.oauth2.id_token import _fetch_certs # This is the internal function we need to bypass key issues.
# Also ensure you have the core libraries:
from google.oauth2 import id_token
from google.auth.transport import requests
import firebase_admin
from firebase_admin import credentials, auth


# GOOGLE_CLIENT_ID = "463530012666-iqbgkv4vi2omt3oo8dsa82qer3919rjb.apps.googleusercontent.com"
SECRET_KEY = "change-this-to-a-long-random-string-2025"
ALGORITHM = "HS256"

# Optional: Pre-fetch keys once during startup to ensure the cache is warm
# This explicitly hits the network to download keys.

SERVICE_ACCOUNT_FILE = "job-scraper-9ccef-firebase-adminsdk-fbsvc-a3f3924364.json" 
CRED = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(CRED)
print("Firebase Admin SDK initialized.")
# try:
#     print("Pre-fetching Google Public Keys...")
#     # This call forces the keys to be downloaded and cached by the library
#     _fetch_certs(requests.Request(), certs_url='https://www.googleapis.com/oauth2/v3/certs')
#     print("Google Public Keys successfully cached.")
# except Exception as e:
#     print(f"WARNING: Initial key pre-fetch failed: {e}. Verification may still fail.")


logging.basicConfig(level=logging.INFO)


app = FastAPI(title="Job Scraper + AI Analyzer API")

# Create DB tables
Base.metadata.create_all(bind=engine)

SECRET_KEY = "change-this-to-a-long-random-string-2025"
ALGORITHM = "HS256"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Pydantic models
# ------------------------------
class JobModel(BaseModel):
    title: str
    company: str
    location: str
    description: str
    skills: List[str]
    job_type: str

class JobBatch(BaseModel):
    jobs: List[JobModel]

class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    seniority: Optional[str] = None
    job_type: Optional[str] = None
    job_link: Optional[str] = None
    salary: Optional[str] = None
    

class JobRead(JobCreate):
    id: int

    model_config = {"from_attributes": True}

class SaveJobRequest(BaseModel):
    # user_id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    skills: Optional[List[str]]
    seniority: Optional[str]
    job_type: Optional[str]
    job_link: Optional[str]
    salary: Optional[str]

# 1. for JWT
class GoogleAuthRequest(BaseModel):
    token: str

# ------------------------------
# DB session dependency
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------
# Endpoints
# ------------------------------
@app.get("/")
def root():
    return {"message": "✅ Job Scraper + AI API is running!"}

@app.get("/scrape")
def scrape_endpoint(job: str = "python developer", location: str = "Abudhabi"):
    try:
        jobs = scrape_jobs(job_query=job, location=location) or []
        return {"count": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
def analyze_endpoint(batch: JobBatch):
    try:
        jobs_data = [job.model_dump() for job in batch.jobs]  # Pydantic v2
        results = process_all_jobs(jobs_data)
        save_to_csv(results, "analyzed_jobs.csv")
        return {
            "message": f"Processed {len(results)} jobs successfully",
            "results": results,
            "csv_file": "analyzed_jobs.csv"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
def scrape_and_analyze(job: str = "python developer", location: str = "San Francisco"):
    try:
        jobs = scrape_jobs(job_query=job, location=location)
        results = process_all_jobs(jobs)
        save_to_csv(results, "analyzed_jobs.csv")
        print("🔵 scraped jobs:")
        print(jobs)
        print("🔴 AI PROCESSED RESULTS:")
        print(results)

        return {
            "message": f"Scraped and analyzed {len(results)} jobs",
            "results": results,
            "csv_file": "analyzed_jobs.csv"
        }
    except Exception as e:
        import traceback
        print("❌ Scraper error traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scraper failed: {e}")

# Streaming endpoint for progress updates
async def scrape_and_analyze_with_progress_thread(job: str, location: str):
    yield f"data: {json.dumps({'step': 1, 'total': 3, 'message': 'Starting scraping...'})}\n\n"
    await asyncio.sleep(0.1)
    try:
        jobs = await asyncio.to_thread(scrape_jobs, job_query=job, location=location)
        yield f"data: {json.dumps({'step': 2, 'total': 3, 'message': f'Scraped {len(jobs)} jobs'})}\n\n"
        await asyncio.sleep(0.1)
        results = await asyncio.to_thread(process_all_jobs, jobs)
        yield f"data: {json.dumps({'step': 3, 'total': 3, 'message': 'Analysis complete', 'results': results})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'step': 0, 'total': 3, 'message': f'Error: {str(e)}'})}\n\n"

@app.get("/jobs/stream")
async def jobs_stream(job: str = "python developer", location: str = "Abudhabi"):
    return StreamingResponse(
        scrape_and_analyze_with_progress_thread(job, location),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

# Initialize the OAuth2 scheme to look for the token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google")

async def authenticate_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency function to verify the custom JWT and return the user ID.
    Raises HTTPException 401 on failure.
    """
    # NOTE: Ensure SECRET_KEY and ALGORITHM are defined globally above this function.
    global SECRET_KEY 
    global ALGORITHM

    try:
        # 1. Decode the token using your SECRET_KEY and ALGORITHM
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the user ID (subject 'sub')
        user_id: str = payload.get("sub")
        
        if user_id is None:
            # If the token is valid but somehow lacks a user ID claim
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token (missing user ID claim)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 3. Return the authenticated user ID
        return user_id
        
    except PyJWTError:
        # This catches errors like invalid signature or expired token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (JWT invalid or expired)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # General catch-all for other errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ------------------------------
# Save job endpoint
# ------------------------------
@app.post("/save-job", response_model=JobRead)
def save_job(request: SaveJobRequest, db: Session = Depends(get_db), current_user_id: str = Depends(authenticate_user)):
    user_id = current_user_id
    print("🔥 Incoming SaveJobRequest:", request)

    job_data = request.model_dump()
    print("🔥 Parsed job_data:", job_data)
    print("el salary:", request.salary)

    # Remove user_id from job_data so we don't pass it twice
    job_data.pop("user_id", None)

    # Check duplicates
    existing_job = db.query(SavedJob).filter(
        SavedJob.user_id == user_id,
        SavedJob.title == job_data["title"],
        SavedJob.company == job_data.get("company"),
        SavedJob.location == job_data.get("location")
    ).first()

    if existing_job:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This job is already saved.")

    # Fix skills type
    skills = job_data.get("skills", [])
    if isinstance(skills, list):
        job_data["skills"] = ",".join(skills)
    if job_data.get("skills") is None:
        job_data["skills"] = ""

    # Create the DB object (NOW VALID)
    db_job = SavedJob(user_id=user_id, **job_data)

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return JobRead(
        id=db_job.id,
        title=db_job.title,
        company=db_job.company,
        location=db_job.location,
        summary=db_job.summary,
        description=db_job.description,
        skills=db_job.skills.split(",") if db_job.skills else [],
        seniority=db_job.seniority,
        job_type=db_job.job_type,
        job_link=db_job.job_link,
        salary=db_job.salary
    )

# ------------------------------
# Get saved jobs
# ------------------------------
@app.get("/saved-jobs", response_model=List[JobRead])
def get_saved_jobs(db: Session = Depends(get_db), current_user_id: str = Depends(authenticate_user)):
    # CRITICAL CHANGE: We IGNORE the 'user_id' from the URL and
    # FORCE the query to use the secure ID from the JWT.
    jobs = db.query(SavedJob).filter(SavedJob.user_id == current_user_id).all()
    return [
        JobRead(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            summary=job.summary,
            description=job.description,
            skills=job.skills.split(",") if job.skills else [],
            seniority=job.seniority,
            job_type=job.job_type,
            job_link=job.job_link,
            salary=job.salary,

        ) for job in jobs
    ]

# ------------------------------
# Delete saved job
# ------------------------------
@app.delete("/saved-job/{job_id}", status_code=status.HTTP_200_OK)
def delete_saved_job(job_id: int, db: Session = Depends(get_db), current_user_id: str = Depends(authenticate_user)):
    job = db.query(SavedJob).filter(SavedJob.id == job_id, SavedJob.user_id == current_user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"detail": "Job deleted"}

@app.get("/ping")
def ping():
    return {"message": "pong"}


def create_jwt(google_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=60)
    payload = {
        "sub": google_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc)   # optional but nice
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



@app.post("/auth/google")
async def google_login(request_data: GoogleAuthRequest):
    token = request_data.token
    
    try:
        # THE CORRECT VERIFICATION: Use the Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        
        # The unique ID is 'uid' from the Firebase token
        google_id = decoded_token['uid'] 
        email = decoded_token.get('email')
        name = decoded_token.get('name')

        # SUCCESS: Return the custom JWT
        return {
            "access_token": create_jwt(google_id), 
            "user_id": google_id,
            "email": email,
            "name": name or "User"
        }
    except firebase_admin.exceptions.FirebaseError as e:
        # Firebase-specific failure (e.g., token expired, revoked, or invalid signature)
        print(f"FIREBASE AUTH ERROR: {e}") 
        # Reraise a 401 with the specific Firebase error detail
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token. Error details: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"GENERAL AUTH ERROR: {e}")
        raise HTTPException(status_code=401, detail=f"General Auth failure: {str(e)}")