#!/usr/bin/env python3
import os
import re
import json
import urllib.request

README_PATH = "README.md"

LC_USERNAME = os.environ["LC_USERNAME"]

# Optional (only needed if LeetCode blocks anonymous requests for you):
LC_SESSION = os.environ.get("LC_SESSION", "").strip()
CSRF_TOKEN = os.environ.get("CSRF_TOKEN", "").strip()

def fetch_solved_count(username: str) -> int:
    url = "https://leetcode.com/graphql"
    payload = {
        "query": """
        query userProfile($username: String!) {
          matchedUser(username: $username) {
            submitStatsGlobal {
              acSubmissionNum {
                difficulty
                count
              }
            }
          }
        }
        """,
        "variables": {"username": username},
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "github-action")

    # If needed, send cookies (many users don't need this; try without first).
    cookies = []
    if LC_SESSION:
        cookies.append(f"LEETCODE_SESSION={LC_SESSION}")
    if CSRF_TOKEN:
        cookies.append(f"csrftoken={CSRF_TOKEN}")
        req.add_header("x-csrftoken", CSRF_TOKEN)
        req.add_header("Referer", "https://leetcode.com")

    if cookies:
        req.add_header("Cookie", "; ".join(cookies))

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        obj = json.loads(raw)

    matched = obj.get("data", {}).get("matchedUser")
    if not matched:
        raise RuntimeError(f"Could not find LeetCode user: {username}")

    ac = matched["submitStatsGlobal"]["acSubmissionNum"]
    # Total is typically the entry with difficulty "All"
    total = next((x["count"] for x in ac if x["difficulty"] == "All"), None)
    if total is None:
        # fallback: sum Easy/Medium/Hard
        total = sum(x["count"] for x in ac if x["difficulty"] in ("Easy", "Medium", "Hard"))
    return int(total)

def update_readme(new_count: int) -> bool:
    with open(README_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    pattern = r"(<!--\s*LC_SOLVED_START\s*-->)(.*?)(<!--\s*LC_SOLVED_END\s*-->)"
    m = re.search(pattern, text, flags=re.DOTALL)
    if not m:
        raise RuntimeError("Missing LC_SOLVED_START/LC_SOLVED_END markers in README.md")

    old = m.group(2).strip()
    if old == str(new_count):
        return False

    updated = re.sub(pattern, rf"\1{new_count}\3", text, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    return True

def main():
    solved = fetch_solved_count(LC_USERNAME)
    changed = update_readme(solved)
    print(f"Solved={solved}, changed={changed}")

if __name__ == "__main__":
    main()
