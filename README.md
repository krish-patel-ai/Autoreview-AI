# 🤖 AutoReview AI — Autonomous GitHub PR Reviewer

> AI agent that autonomously reviews GitHub Pull Requests, detects bugs, security issues, and posts inline comments directly on GitHub.



![Python](https://img.shields.io/badge/Python-3.10+-blue)




![LangChain](https://img.shields.io/badge/LangChain-latest-green)




![Groq](https://img.shields.io/badge/Groq-LLaMA3.3-orange)




![License](https://img.shields.io/badge/License-MIT-yellow)



---

## 🚀 What it does

Paste a GitHub PR URL → AutoReview AI:

1. **Fetches** the full PR diff and metadata from GitHub
2. **Analyzes** each changed file for bugs, security issues, style problems
3. **Posts inline comments** on specific lines directly on GitHub
4. **Posts overall verdict** — APPROVE or REQUEST CHANGES

All autonomously. Zero human intervention.

---

## 🎯 Demo

```
Input:  https://github.com/owner/repo/pull/123

Output:
BUGS:
- Line 47: Unhandled exception in payment processing loop

SECURITY:
- Line 23: API key hardcoded in source code

VERDICT: REQUEST CHANGES
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | LangChain Tool Calling Agent |
| LLM | Groq — LLaMA 3.3 70B (temperature=0) |
| GitHub Integration | PyGithub |
| Tools | fetch_pr_diff, analyze_diff, post_inline_comment, post_overall_review |
| Environment | Python-dotenv |

---

## ⚙️ Architecture

```
PR URL
  ↓
fetch_pr_diff      → Extracts diff, metadata, changed files
  ↓
analyze_diff       → LLM reviews each file (bugs, security, style)
  ↓
post_inline_comment → Posts specific line comments on GitHub
  ↓
post_overall_review → APPROVE or REQUEST CHANGES verdict
```

---

## 🔧 Setup

```bash
# Clone
git clone https://github.com/Krishp1/AutoReview-AI
cd AutoReview-AI

# Install
pip install -r requirements.txt

# Environment
cp .env.example .env
# Add your keys:
# GROQ_API_KEY=your_key
# GITHUB_TOKEN=your_token

# Run
python main.py
```

---

## 📁 Project Structure

```
AutoReview-AI/
├── main.py          # Agent executor + review functions
├── tools.py         # LangChain tools (fetch, analyze, post)
├── requirements.txt
└── .env
```

---

## 💡 Key Features

- **Autonomous 4-step pipeline** — no human intervention needed
- **Inline GitHub comments** — posts directly on specific lines
- **Structured review format** — Bugs / Security / Style / Suggestions
- **Demo mode** — works without GitHub token for portfolio showcase
- **Rate limit safe** — handles large PRs with file/patch size limits

---

## 📊 Example Output

```
🔍 AutoReview AI starting review...
📎 PR: https://github.com/langchain-ai/langchain/pull/1

✅ PR fetched — 3 files changed
🤖 Analyzing code...

BUGS: None
SECURITY:
- Line 12: Sensitive data exposed in logs
STYLE:
- Missing docstrings on public functions
VERDICT: REQUEST_CHANGES

✅ Review posted to GitHub
```

---

## 🧠 Built With

- [LangChain](https://langchain.com) — Agent framework
- [Groq](https://groq.com) — Ultra-fast LLM inference  
- [PyGithub](https://pygithub.readthedocs.io) — GitHub API wrapper

---

## 👤 Author

**Krish Patel** — AI Engineer  
[GitHub](https://github.com/krish-patel-ai) • [LinkedIn](https://www.linkedin.com/in/krish-patel-4951713b3/)

---

*Built as part of AI Engineer Portfolio — targeting Bangalore AI startups*
