import json
import re
import time
import csv
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# ⚙️ OpenAI client setup
# Make sure your API key is set in environment variable:
# export OPENAI_API_KEY="YOUR_KEY_HERE" (Linux/Mac)
# setx OPENAI_API_KEY "YOUR_KEY_HERE" (Windows)
client = OpenAI(api_key=os.getenv("openai_api_key"))

# ---------------------------
# 🧩 Process jobs with AI
def process_all_jobs(all_jobs):
    """
    Sends each job to OpenAI and returns a list of enriched job dictionaries.
    """

    
        
    processed = []


    for i, job in enumerate(all_jobs, start=1):
        print(f"🔹 Processing job {i}/{len(all_jobs)}: {job.get('title', 'Untitled')}")

        # ---- Build prompt for this job ----
        prompt = f"""
Extract the following fields from the job below.
Return ONLY valid JSON. NO code blocks. NO backticks. NO explanation. From the job description below, extract the salary ONLY if it is explicitly mentioned.

RULES:
- Do NOT estimate salaries.
- Do NOT infer ranges.
- Do NOT create numbers.
- Do NOT rewrite or summarize.
- Extract text EXACTLY as it appears.

Fields:
- summary: a short summary
- skills: list of skills
- seniority: Junior / Intermediate / Senior
- job_type: Remote / Hybrid / Onsite
- salary: extract explicit salary from description if mentioned and strip of extra text other than salary value and currency.

Job Data:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('description')}
"""
 # Python triple quotes end here
        
        try:
            # ---- Send prompt to OpenAI ----
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract structured job data and must return valid JSON only. You are a strict information extraction tool. You NEVER guess data."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            print("🔴 AI OUTPUT:")
            print(response)


            # ---- Extract response and clean Markdown fences ----
            content = response.choices[0].message.content.strip()
            content = content.strip()

            # Strip code fences if present
            if content.startswith("```"):
                content = content.split("```", 2)[1].strip()

            # Clean again if nested
            if content.startswith("{") is False:
                content = re.search(r"\{.*\}", content, re.DOTALL).group()



            # ---- Parse JSON safely ----
            data = json.loads(content)

            # ---- Merge original job data with AI output ----
            job_with_ai = {
                **job,  # Copy original job fields
                "job_link": job.get("job_link"),
                "summary": data.get("summary", ""),
                "skills": ", ".join(data.get("skills", [])),
                "seniority": data.get("seniority", ""),
                "job_type": data.get("job_type", ""),
                "salary": data.get("salary") or job.get("salary") or "",
                "raw_ai_output": content,  # Keep raw AI output for debugging
            }

        except json.JSONDecodeError:
            print(f"⚠️ Could not parse JSON for job {i}, storing raw output.")
            job_with_ai = {**job, "summary": "", "skills": "", "seniority": "", "job_type": "", "raw_ai_output": content}

        except Exception as e:
            print(f"❌ Error processing job {i}: {e}")
            job_with_ai = {**job, "summary": "", "skills": "", "seniority": "", "job_type": "", "raw_ai_output": ""}

        processed.append(job_with_ai)
        time.sleep(1.2)  # Small delay to avoid rate limits

    return processed


def save_to_csv(jobs, filename="jobs_analyzed.csv"):
    if not jobs:
        print("No jobs to save.")
        return

    headers = list(jobs[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(jobs)

    print(f"✅ Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    all_jobs = [
{
    "title": "Python Developer",
    "company": "TechCorp",
    "location": "Dubai",
    "description": "Looking for a Python developer with experience in Django, FastAPI, and REST APIs. Must be comfortable working in an Agile team."
},
{
    "title": "Data Analyst",
    "company": "DataInc",
    "location": "Remote",
    "description": "We need someone proficient in SQL, Excel, and Python for data analysis and reporting. Experience with Tableau is a plus."
},
{
    "title": "Frontend Engineer",
    "company": "WebWorks",
    "location": "New York",
    "description": "Looking for a frontend engineer skilled in React, HTML, CSS, and JavaScript. Experience with Redux and TypeScript is preferred."
},
{
    "title": "Machine Learning Engineer",
    "company": "AI Solutions",
    "location": "San Francisco",
    "description": "Seeking a machine learning engineer with Python, TensorFlow, and PyTorch experience. Must have knowledge of ML pipelines and model deployment."
}
    
]
    jobs = process_all_jobs(all_jobs)
    save_to_csv(jobs, "ay_7aga.csv")

def extract_salary_with_ai(description: str) -> str | None:
    if not description:
        return None

    prompt = f"""
Extract the salary from the following job description. 
If no salary is mentioned, return null.
Keep the exact text as it appears (e.g., "AED2,000 - AED2,500 per month").
Only return the salary text or null, nothing else.

Job Description:
{description}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        salary = response.choices[0].message.content.strip()
        if salary.lower() in ("null", ""):
            return None
        return salary
    except Exception as e:
        print(f"⚠️ Error extracting salary: {e}")
        return None
