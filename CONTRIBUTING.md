# Contributing to BoardMorph 🎨

Thank you for your interest in contributing to **BoardMorph**! We welcome contributions of all kinds: bug fixes, documentation enhancements, new tool integrations, compiler optimizations, and visual UI improvements.

---

## 🧭 Code of Conduct

We expect all contributors to adhere to a respectful, welcoming, and collaborative code of conduct. Please treat fellow community members with kindness, empathy, and constructive feedback.

---

## 🛠️ Development Setup

### Prerequisites
- **Python**: `3.11` or `3.12`
- **Node.js**: `v18.0.0` or higher (Node 20+ recommended)
- **Git**

### 1. Fork & Clone the Repository
```bash
git clone https://github.com/<your-username>/boardmorph.git
cd boardmorph
```

### 2. Configure Environment Variables
Create a local `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Populate your `.env` with your OpenRouter API key and Miro app credentials. (Never commit `.env` to version control!)

### 3. Backend Setup (FastAPI)
```bash
# Optional: create a virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt  # or install fastapi uvicorn pydantic pydantic-settings httpx sse-starlette openai pytest

# Run dev server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Frontend Setup (React 19 + Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Tests & Validation

Before submitting a Pull Request, please ensure all tests and type checks pass:

### Backend Tests
```bash
# Run pytest unit tests
python -m pytest backend/tests/test_miro.py -v
```

### Frontend Type-Check & Build
```bash
cd frontend
npm run build
```

---

## 🌿 Git Branching & PR Workflow

1. **Create a topic branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
2. **Commit your changes**:
   Keep commit messages concise and descriptive (e.g., `feat: add safe calculator tool parameter mapping` or `fix: normalize CRLF in SSE streaming parser`).
3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Open a Pull Request**:
   Fill out the PR template, describing what changes were made, why they are needed, and how they were tested.

---

## 📜 Questions or Ideas?

Feel free to open an issue or start a discussion on GitHub. We are excited to see what you build with BoardMorph!
