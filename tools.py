 # tools.py — LangChain tools for AutoReview AI

import os
import re
from github import Github
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()
print("Tools key:",os.getenv("GROQ_API_KEY"))
# ── LLM ──────────────────────────────────
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── GITHUB CLIENT ─────────────────────────
def get_github_client():
    token = os.environ.get("GITHUB_TOKEN", "")
    return Github(token) if token else Github()

# ─────────────────────────────────────────
# TOOL 1 — FETCH PR DIFF
# ─────────────────────────────────────────
@tool
def fetch_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff and metadata from a GitHub Pull Request URL.
    Returns structured info: PR title, description, changed files and their diffs.
    Input: GitHub PR URL like https://github.com/owner/repo/pull/123
    """
    try:
        # Parse owner, repo, PR number from URL
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match   = re.search(pattern, pr_url)
        if not match:
            return "ERROR: Invalid GitHub PR URL. Format: https://github.com/owner/repo/pull/123"

        owner   = match.group(1)
        repo    = match.group(2)
        pr_num  = int(match.group(3))

        g       = get_github_client()
        repo_obj= g.get_repo(f"{owner}/{repo}")
        pr      = repo_obj.get_pull(pr_num)

        # Get changed files
        files   = pr.get_files()
        file_diffs = []

        for f in files:
            if f.patch:  # only files with actual changes
                file_diffs.append({
                    "filename": f.filename,
                    "status":   f.status,      # added/modified/deleted
                    "additions":f.additions,
                    "deletions":f.deletions,
                    "patch":    f.patch[:3000]  # limit patch size
                })

        result = {
            "pr_title":       pr.title,
            "pr_description": pr.body or "No description",
            "pr_number":      pr_num,
            "owner":          owner,
            "repo":           repo,
            "base_branch":    pr.base.ref,
            "head_branch":    pr.head.ref,
            "total_files":    pr.changed_files,
            "additions":      pr.additions,
            "deletions":      pr.deletions,
            "files":          file_diffs
        }

        # Format as readable string for LLM
        output = f"""
PR TITLE: {result['pr_title']}
PR NUMBER: #{result['pr_number']}
DESCRIPTION: {result['pr_description'][:500]}
BRANCH: {result['head_branch']} → {result['base_branch']}
STATS: +{result['additions']} additions, -{result['deletions']} deletions, {result['total_files']} files changed

FILES CHANGED:
"""
        for f in file_diffs[:10]:  # max 10 files
            output += f"""
--- {f['filename']} ({f['status']}) +{f['additions']}/-{f['deletions']} ---
{f['patch'][:2000]}
"""
        return output.strip()

    except Exception as e:
        return f"ERROR fetching PR: {str(e)}"

# ─────────────────────────────────────────
# TOOL 2 — ANALYZE DIFF
# ─────────────────────────────────────────
@tool
def analyze_diff(file_info: str) -> str:
    """
    Analyzes a code diff and returns review comments.
    Input: string containing filename and its diff/patch
    Returns: structured review with bugs, security issues, suggestions
    """
    response = llm.invoke([
        SystemMessage(content="""You are a senior software engineer doing a code review.
Analyze the code diff carefully and provide specific, actionable feedback.

Return your review in EXACTLY this format:
BUGS:
- <line number if known>: <specific bug description> or NONE

SECURITY:
- <line number if known>: <security issue> or NONE

STYLE:
- <specific style issue> or NONE

SUGGESTIONS:
- <improvement suggestion> or NONE

VERDICT: APPROVE or REQUEST_CHANGES
SUMMARY: <one sentence overall assessment>"""),
        HumanMessage(content=f"""
Review this code change:

{file_info}

Be specific — mention exact line numbers when possible.
Focus on real issues, not nitpicks.
""")
    ])

    return response.content

# ─────────────────────────────────────────
# TOOL 3 — POST INLINE COMMENTS
# ─────────────────────────────────────────
@tool
def post_inline_comment(comment_data: str) -> str:
    """
    Posts an inline review comment on a GitHub PR.
    Input format: 'owner|repo|pr_number|commit_sha|filename|line_number|comment_body'
    Returns: success or error message
    """
    try:
        parts = comment_data.split("|")
        if len(parts) < 7:
            return "ERROR: Need format: owner|repo|pr_number|commit_sha|filename|line_number|comment"

        owner      = parts[0].strip()
        repo       = parts[1].strip()
        pr_number  = int(parts[2].strip())
        commit_sha = parts[3].strip()
        filename   = parts[4].strip()
        line       = int(parts[5].strip())
        body       = "|".join(parts[6:]).strip()

        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return "ERROR: GITHUB_TOKEN not set — cannot post comments"

        g        = Github(token)
        repo_obj = g.get_repo(f"{owner}/{repo}")
        pr       = repo_obj.get_pull(pr_number)
        commit   = repo_obj.get_commit(commit_sha)

        pr.create_review_comment(
            body=f"🤖 **AutoReview AI:** {body}",
            commit=commit,
            path=filename,
            line=line
        )

        return f"✅ Comment posted on {filename} line {line}"

    except Exception as e:
        return f"ERROR posting comment: {str(e)}"

# ─────────────────────────────────────────
# TOOL 4 — POST OVERALL REVIEW
# ─────────────────────────────────────────
@tool
def post_overall_review(review_data: str) -> str:
    """
    Posts an overall PR review (approve or request changes) on GitHub.
    Input format: 'owner|repo|pr_number|APPROVE or REQUEST_CHANGES|summary_body'
    Returns: success or error message
    """
    try:
        parts  = review_data.split("|")
        owner  = parts[0].strip()
        repo   = parts[1].strip()
        pr_num = int(parts[2].strip())
        event  = parts[3].strip()  # APPROVE or REQUEST_CHANGES
        body   = "|".join(parts[4:]).strip()

        if event not in ("APPROVE", "REQUEST_CHANGES", "COMMENT"):
            event = "COMMENT"

        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return "Review NOT posted to GitHub (no token) — here is the review:\n" + body

        g        = Github(token)
        repo_obj = g.get_repo(f"{owner}/{repo}")
        pr       = repo_obj.get_pull(pr_num)

        review_body = f"""🤖 **AutoReview AI Report**

{body}

---
*Reviewed by AutoReview AI — LangChain + Groq*
"""
        pr.create_review(body=review_body, event=event)
        return f"✅ Overall review posted: {event}"

    except Exception as e:
        return f"ERROR posting review: {str(e)}"
