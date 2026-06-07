# main.py — AutoReview AI
# LangChain-based autonomous GitHub PR reviewer

import os
import re
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from tools import fetch_pr_diff, analyze_diff, post_inline_comment, post_overall_review

load_dotenv()


# ── LLM ──────────────────────────────────
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── TOOLS ─────────────────────────────────
tools = [fetch_pr_diff, analyze_diff, post_inline_comment, post_overall_review]

# ── PROMPT ────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are AutoReview AI — an expert autonomous GitHub PR reviewer.

Your job when given a PR URL:
1. Use fetch_pr_diff to get the PR details and code changes
2. Use analyze_diff for each changed file to find bugs, security issues, style problems
3. Use post_inline_comment to post specific comments on problematic lines
4. Use post_overall_review to post a final APPROVE or REQUEST_CHANGES verdict

Be thorough but concise. Focus on real issues that matter.
Always complete all 4 steps — don't stop after fetching.

If GitHub token is not available, still analyze and return the review as text.
"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# ── AGENT ─────────────────────────────────
agent          = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True
)

# ─────────────────────────────────────────
# MAIN REVIEW FUNCTION
# ─────────────────────────────────────────
def review_pr(pr_url: str) -> dict:
    """
    Main function to review a GitHub PR.
    Returns structured review result.
    """
    print(f"\n{'='*60}")
    print(f"🔍 AutoReview AI starting review...")
    print(f"📎 PR: {pr_url}")
    print("="*60)

    try:
        result = agent_executor.invoke({
            "input": f"""
Please review this GitHub Pull Request: {pr_url}

Steps to follow:
1. Fetch the PR diff using fetch_pr_diff
2. Analyze each changed file using analyze_diff
3. Post inline comments for specific issues using post_inline_comment
4. Post overall verdict using post_overall_review

Provide a thorough code review focusing on:
- Bugs and logic errors
- Security vulnerabilities
- Code style and best practices
- Performance issues
"""
        })

        output = result.get("output", "")
        print(f"\n✅ Review complete!")
        print(f"\nOutput:\n{output}")

        return {
            "success": True,
            "pr_url":  pr_url,
            "review":  output,
            "error":   None
        }

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        return {
            "success": False,
            "pr_url":  pr_url,
            "review":  None,
            "error":   error_msg
        }

# ─────────────────────────────────────────
# SIMPLE REVIEW (no GitHub token needed)
# For demo purposes
# ─────────────────────────────────────────
def review_pr_simple(pr_url: str) -> dict:
    """
    Reviews PR without posting comments to GitHub.
    Returns full analysis as text — good for demo.
    """
    print(f"\n🔍 Fetching PR data...")

    # Step 1: Fetch diff
    diff_result = fetch_pr_diff.invoke(pr_url)

    if diff_result.startswith("ERROR"):
        return {"success": False, "error": diff_result, "review": None}

    print("✅ PR fetched!")
    print(f"\n🤖 Analyzing code...")

    # Step 2: Analyze
    analysis = analyze_diff.invoke(diff_result[:4000])

    print("✅ Analysis complete!")

    # Step 3: Generate final verdict
    verdict_response = llm.invoke([
        SystemMessage("You are a senior engineer. Give a final PR review verdict."),
        HumanMessage(f"""
Based on this PR analysis, write a complete review report:

PR DATA:
{diff_result[:2000]}

ANALYSIS:
{analysis}

Write a professional review with:
1. Overall verdict (APPROVE / REQUEST CHANGES)
2. Key issues found
3. Positive aspects
4. Specific suggestions
""")
    ])

    return {
        "success":  True,
        "pr_url":   pr_url,
        "pr_data":  diff_result,
        "analysis": analysis,
        "verdict":  verdict_response.content,
        "error":    None
    }

# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    # Test with a real public PR
    test_pr = "https://github.com/langchain-ai/langchain/pull/1"

    print("Mode: Simple review (no GitHub token needed for demo)")
    result = review_pr_simple(test_pr)

    if result["success"]:
        print(f"\n{'='*60}")
        print("📋 PR DATA SUMMARY:")
        print(result["pr_data"][:500])
        print(f"\n🔍 ANALYSIS:")
        print(result["analysis"])
        print(f"\n✅ FINAL VERDICT:")
        print(result["verdict"])
    else:
        print(f"❌ Failed: {result['error']}")