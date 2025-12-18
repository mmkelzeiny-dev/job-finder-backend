# 🛠️ JobFinder Backend (FastAPI + AI)

This is the high-performance Python backend for the JobFinder ecosystem. It handles intelligent job scraping, AI-powered data extraction, and secure user session management.

## 🧠 AI-Powered Analysis

Unlike basic scrapers, this backend uses **OpenAI (GPT-4o)** to process raw job descriptions.

- **Skill Extraction:** Automatically identifies required tech stacks from messy text.
- **Salary Normalization:** Extracts and formats salary ranges into a readable format.
- **Seniority Detection:** Smart-labels jobs (Junior, Mid, Senior) even when not explicitly stated in the title.

## 🚀 Core Features

- **Automated Scraper:** Fetches live data from multiple job boards using BeautifulSoup4.
- **JWT Security:** Validates Firebase Auth tokens to ensure private user data remains secure.
- **SQLAlchemy ORM:** Clean database management for saving and tracking user jobs.

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **AI:** OpenAI API
- **Database:** SQLite (SQLAlchemy)
- **Auth:** Firebase Admin SDK
- **Scraping:** BeautifulSoup4 & Requests

## 📦 Setup & Security

To run this project locally, you must provide your own credentials:

1. **Firebase Admin SDK:** \* Download your service account JSON from the Firebase Console.

   - Save it as `firebase-adminsdk.json` in the root directory.
   - _Note: This file is ignored by Git for security._

2. **Environment Variables:**

   - Create a `.env` file.
   - Add your `OPENAI_API_KEY`.

3. **Install & Run:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
