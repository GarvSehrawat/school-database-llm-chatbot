# 🎓 School Database LLM Chatbot

A full-stack school database chatbot built with FastAPI, SQLAlchemy, SQLite, Streamlit, LangChain, and Azure OpenAI.

The application allows users to upload school data through CSV files and ask natural-language questions about students, marks, attendance, fees, rankings, and analytics.

## Features

- Student profile management
- Marks, grades, and semester-wise results
- Attendance tracking
- Fee status and pending amount tracking
- Top students, dense ranking, low attendance, pending fees, and branch toppers
- CSV uploads for students, subjects, marks, attendance, and fees
- Azure OpenAI structured intent extraction
- Deterministic fallback parser
- Safe service-based database access
- Streamlit chat interface
- Automated tests

## Architecture

```text
User
  ↓
Streamlit Frontend
  ↓
FastAPI API
  ↓
Azure OpenAI / Rule-Based Fallback
  ↓
Validated Intent
  ↓
Service Layer
  ↓
Repository Layer
  ↓
SQLAlchemy + SQLite
```

The LLM does not generate SQL or access the database directly.

## Tech Stack

- Python
- FastAPI
- Streamlit
- SQLAlchemy
- SQLite
- Pydantic
- pandas
- LangChain
- Azure OpenAI
- pytest

## Project Structure

```text
school-rag-chatbot/
├── backend/
│   ├── api/
│   ├── llm/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   └── main.py
├── frontend/
│   └── app.py
├── scripts/
│   └── seed_database.py
├── tests/
├── data/
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Git Bash:

```bash
source .venv/Scripts/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```env
DATABASE_URL=sqlite:///./school.db

AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_CHAT_DEPLOYMENT=school-chat-model

LLM_ENABLED=true
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

Do not commit the `.env` file.

### 4. Seed the database

```bash
python -m scripts.seed_database
```

The seed script creates:

- 120 students
- 15 subjects
- 1,800 marks records
- 1,800 attendance records
- 120 fee records

## Run the Application

Start FastAPI:

```bash
uvicorn backend.main:app --reload
```

Start Streamlit in another terminal:

```bash
streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Example Queries

```text
Show semester 2 marks of STU121
Show attendance of STU121
Show semester 5 fees of STU122
Show top 5 students in semester 2
What is the semester 2 rank of STU121?
Show students with attendance below 75 percent
Show pending fees for semester 5
Show semester 2 branch toppers
```

## CSV Uploads

The frontend supports CSV uploads for:

- Students
- Subjects
- Marks
- Attendance
- Fees

Each upload reports inserted, updated, skipped, and failed rows.

## Azure OpenAI

Azure OpenAI converts flexible questions into validated structured intents.

Example:

```text
Could you tell me how STU121 performed during their second semester?
```

Parsed result:

```json
{
  "intent": "get_marks",
  "student_id": "STU121",
  "semester": 2
}
```

If Azure is unavailable, the application automatically uses the rule-based parser.

## Testing

Run all tests:

```bash
pytest -v
```

The test suite covers:

- Query parsing
- API responses
- Validation
- Unknown queries
- CSV insertion
- Duplicate handling
- Record replacement
- Temporary test databases

## Security

The application does not use unrestricted text-to-SQL.

The model can only return predefined intents and validated entities. The backend then calls approved service methods.

## Future Improvements

- PostgreSQL
- Docker
- Deployment
- Authentication
- Role-based access control
- Alembic migrations
- PDF marksheets
- Dashboard charts

## Author

**Garv Sehrawat**

B.Tech Computer Science and Engineering student interested in Python, backend development, machine learning, and LLM applications.

> All student data used in this project is fictional.