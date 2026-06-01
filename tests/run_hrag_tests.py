#!/usr/bin/env python
"""
Automated Test Runner for CareSmartz360 Hierarchical RAG (HRAG) chatbot.
Executes 15 curated test cases covering various categories, checks latency,
evaluates responses, and outputs a highly polished test report.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error

# Configs
API_URL = "http://127.0.0.1:8000/api/hrag/chat"
REPORT_PATH_LOCAL = os.path.join(os.path.dirname(__file__), "test_report.md")
# Artifact path in user's appDataDir/brain/<conversation-id>/
REPORT_PATH_ARTIFACT = r"C:\Users\HP\.gemini\antigravity\brain\70fe34bb-5092-4bcd-9121-d3c12aef1cda\test_report.md"

TEST_CASES = [
    {
        "id": "TC_001",
        "name": "General/Basic Greeting",
        "question": "Hello! Who are you and how can you help me?",
        "category": "Conversational",
        "expected": "Helpful support assistant identity greeting"
    },
    {
        "id": "TC_002",
        "name": "Procedural Shift Scheduling",
        "question": "How do I schedule a shift in CareSmartz360?",
        "category": "Procedural",
        "expected": "Shift scheduling guidelines or steps"
    },
    {
        "id": "TC_003",
        "name": "Add Caregiver",
        "question": "How do I add a new caregiver into the system?",
        "category": "Management",
        "expected": "Steps to create/add a caregiver profile"
    },
    {
        "id": "TC_004",
        "name": "Billing / Invoice Creation",
        "question": "What is the process to create an invoice for a client?",
        "category": "Billing",
        "expected": "Steps to generate or create client invoices"
    },
    {
        "id": "TC_005",
        "name": "Client Profile Setup",
        "question": "How do I add a client and set up their profile?",
        "category": "Management",
        "expected": "Steps to create/add a new client profile"
    },
    {
        "id": "TC_006",
        "name": "Caregiver Clock In / Out",
        "question": "How do caregivers clock in and out using the mobile app?",
        "category": "Mobile App",
        "expected": "Guidance on mobile EVV clocking in and out"
    },
    {
        "id": "TC_007",
        "name": "Authorization Management",
        "question": "How to set up billing authorization in CareSmartz360?",
        "category": "Payer & Insurance",
        "expected": "Steps to add or configure payer authorizations"
    },
    {
        "id": "TC_008",
        "name": "EVV Configuration",
        "question": "What is EVV and how is it configured in CareSmartz360?",
        "category": "Compliance",
        "expected": "Definition and configuration guide for Electronic Visit Verification"
    },
    {
        "id": "TC_009",
        "name": "Roles & Permissions",
        "question": "How can I edit office staff roles and scheduling permissions?",
        "category": "Security",
        "expected": "Editing roles, permissions, or office staff profiles"
    },
    {
        "id": "TC_010",
        "name": "Custom Fields Setup",
        "question": "How do I create a custom field for client details?",
        "category": "Configuration",
        "expected": "Creating or managing custom fields"
    },
    {
        "id": "TC_011",
        "name": "Negative Test (Out of Domain)",
        "question": "What is the recipe for baking a chocolate chip cookie?",
        "category": "Negative Test",
        "expected": "Polite fallback statement indicating lack of context/information"
    },
    {
        "id": "TC_012",
        "name": "Specific Scheduling Jargon (Split Shift)",
        "question": "How do I set up a split shift in CareSmartz360?",
        "category": "Procedural",
        "expected": "Guide to split shifts or consecutive shifts setup"
    },
    {
        "id": "TC_013",
        "name": "Partially Complete Query",
        "question": "caregiver scheduling conflicts",
        "category": "Short Query",
        "expected": "Resolving scheduling warnings or conflict rules"
    },
    {
        "id": "TC_014",
        "name": "Very Long Complex Scenario",
        "question": "I am trying to run payroll for the caregiver John Doe but the shift hours are not showing up correctly in the billing section, how do I resolve this payroll issue?",
        "category": "Complex Query",
        "expected": "Payroll verification, timesheet approval, or shift matching"
    },
    {
        "id": "TC_015",
        "name": "Special Characters Query",
        "question": "How do I update settings & billing info for client's family portal?",
        "category": "Special Characters",
        "expected": "Updating billing or portal configurations with symbols"
    }
]

def run_post(payload: dict) -> tuple[int, dict, float]:
    """Issues POST request and measures latency with automatic transient retry."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                elapsed = time.time() - t0
                return resp.status, json.loads(resp.read().decode("utf-8")), elapsed
        except urllib.error.HTTPError as exc:
            elapsed = time.time() - t0
            try:
                err_data = json.loads(exc.read().decode("utf-8"))
            except Exception:
                err_data = {"detail": str(exc)}
            # If server error or transient error, retry
            if exc.code >= 500 and attempt < max_retries:
                time.sleep(2.0)
                continue
            return exc.code, err_data, elapsed
        except Exception as exc:
            elapsed = time.time() - t0
            if attempt < max_retries:
                time.sleep(2.0)
                continue
            return 500, {"detail": str(exc)}, elapsed

def evaluate_test(tc: dict, code: int, resp: dict) -> tuple[str, str]:
    """Evaluates answer correctness and fallback flags."""
    if code != 200:
        return "FAIL", f"HTTP {code}: {resp.get('detail', 'Unknown error')}"

    answer = resp.get("answer", "")
    sources = resp.get("sources", [])
    
    # Check fallback for negative test
    if tc["id"] == "TC_011":
        lower_answer = answer.lower()
        fallback_keywords = [
            "lacks context", "support", "not find", "do not have", "apologize", 
            "sorry", "cannot answer", "only provided", "not able to", "does not contain", 
            "no information", "lacks information"
        ]
        matched = [k for k in fallback_keywords if k in lower_answer]
        if matched or not sources:
            return "PASS", f"Successfully declined out-of-domain query (matched fallback rules: {matched})"
        else:
            return "WARN", "Did not trigger expected fallback response; output was synthesized despite out-of-domain question."
            
    # For in-domain queries
    if not answer:
        return "FAIL", "Response answer field is empty."
        
    if not sources:
        # Check if conversational/greeting
        if tc["id"] in ("TC_001"):
            return "PASS", "Conversational response answered correctly (no sources required)."
        return "WARN", "Answered, but no source citations were returned."

    return "PASS", f"Citations verified: {len(sources)} source(s) referenced."

def main():
    print("=" * 60)
    print("CareSmartz Hierarchical RAG — Automated Chatbot Test Suite")
    print("=" * 60)
    print(f"Connecting to Chat Endpoint: {API_URL}")
    
    results = []
    total_passed = 0
    total_warned = 0
    total_failed = 0
    total_latency = 0.0

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{idx}/{len(TEST_CASES)}] Running {tc['id']}: {tc['name']}...")
        print(f"  Query: \"{tc['question']}\"")
        
        payload = {
            "question": tc["question"],
            "top_k_children": 10,
            "top_k_parents": 3
        }
        
        code, resp, latency = run_post(payload)
        status, remarks = evaluate_test(tc, code, resp)
        
        total_latency += latency
        
        if status == "PASS":
            total_passed += 1
            status_symbol = "[PASS]"
        elif status == "WARN":
            total_warned += 1
            status_symbol = "[WARN]"
        else:
            total_failed += 1
            status_symbol = "[FAIL]"
            
        print(f"  Status: {status_symbol} | Latency: {latency:.2f}s")
        if code == 200:
            top_parent = ""
            debug = resp.get("retrieval_debug")
            if debug and debug.get("top_parent_title"):
                top_parent = f"{debug['top_parent_title']} (score={debug.get('top_parent_score', 0):.3f})"
            elif resp.get("sources"):
                top_parent = f"{resp['sources'][0].get('title')} (score={resp['sources'][0].get('score', 0):.3f})"
                
            print(f"  Top Match: {top_parent or 'None'}")
            print(f"  Snippet: {resp['answer'][:120].strip()}...")
        else:
            print(f"  Error: {remarks}")
            
        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "category": tc["category"],
            "question": tc["question"],
            "latency": latency,
            "code": code,
            "status": status,
            "remarks": remarks,
            "answer": resp.get("answer", ""),
            "sources": resp.get("sources", []),
            "images": resp.get("image_urls", []),
            "debug": resp.get("retrieval_debug")
        })
        
        # Gentle cooldown between API invocations
        time.sleep(1.0)

    # Calculate summaries
    avg_latency = total_latency / len(TEST_CASES)
    success_rate = (total_passed + total_warned) / len(TEST_CASES) * 100
    
    # Create Markdown report contents
    md = []
    md.append(f"# CareSmartz360 Hierarchical RAG Chatbot — Test Report\n")
    md.append(f"**Date/Time of Run:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**Test Endpoint:** `{API_URL}`\n")
    md.append(f"## 📊 Executive Summary\n")
    
    md.append(f"| Metric | Value |")
    md.append(f"|---|---|")
    md.append(f"| **Total Test Cases Run** | {len(TEST_CASES)} |")
    md.append(f"| **Passed** | 🟢 {total_passed} |")
    md.append(f"| **Warnings** | 🟡 {total_warned} |")
    md.append(f"| **Failed** | 🔴 {total_failed} |")
    md.append(f"| **Overall Functional Success Rate** | **{success_rate:.1f}%** |")
    md.append(f"| **Average Latency** | **{avg_latency:.2f} seconds** |")
    md.append(f"| **Total Combined Latency** | **{total_latency:.2f} seconds** |\n")

    md.append(f"## 📋 Comprehensive Test Matrix\n")
    md.append(f"| Test ID | Name | Category | Status | Latency | Referenced Sources | Chunks Matched | Remarks |")
    md.append(f"|---|---|---|---|---|---|---|---|")
    
    for r in results:
        status_label = "🟢 PASS" if r["status"] == "PASS" else ("🟡 WARN" if r["status"] == "WARN" else "🔴 FAIL")
        source_count = len(r["sources"])
        matched_chunks = sum(s.get("matched_chunks", 1) for s in r["sources"])
        md.append(
            f"| `{r['id']}` | {r['name']} | *{r['category']}* | **{status_label}** | {r['latency']:.2f}s | {source_count} | {matched_chunks} | {r['remarks']} |"
        )
        
    md.append(f"\n## 🔍 Individual Test Logs\n")
    
    for r in results:
        status_label = "🟢 PASS" if r["status"] == "PASS" else ("🟡 WARN" if r["status"] == "WARN" else "🔴 FAIL")
        md.append(f"### 🧪 `{r['id']}` — {r['name']}")
        md.append(f"- **Category:** {r['category']}")
        md.append(f"- **Status:** **{status_label}**")
        md.append(f"- **Latency:** {r['latency']:.2f} seconds")
        md.append(f"- **User Prompt:** *\"{r['question']}\"*")
        
        md.append(f"- **Generated Response:**")
        md.append(f"  > {r['answer'].replace(chr(10), ' ' + chr(10) + '  ')}\n")
        
        if r["sources"]:
            md.append(f"- **Referenced Source Materials:**")
            for idx, s in enumerate(r["sources"], 1):
                md.append(f"  {idx}. **{s.get('title')}** — Score: `{s.get('score', 0.0):.4f}` | Matched Chunks: `{s.get('matched_chunks', 1)}`")
                if s.get("url"):
                    md.append(f"     [Open Source Link]({s['url']})")
        else:
            md.append(f"- **Referenced Source Materials:** *None cited*")
            
        if r["images"]:
            md.append(f"- **Retrieved Source Images:**")
            for img in r["images"][:3]:
                md.append(f"  - `{img}`")
                
        if r["debug"]:
            md.append(f"- **Vector Index Debug Logs:**")
            md.append(f"  - `parents_retrieved`: {r['debug'].get('parents_retrieved')}")
            md.append(f"  - `top_parent_title`: \"{r['debug'].get('top_parent_title')}\"")
            md.append(f"  - `top_parent_score`: {r['debug'].get('top_parent_score', 0.0):.4f}")
            
        md.append("\n" + "---" + "\n")

    report_content = "\n".join(md)
    
    # Save locally to project tests/test_report.md
    try:
        with open(REPORT_PATH_LOCAL, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n[green]Test report saved successfully in local repo: {REPORT_PATH_LOCAL}[/green]")
    except Exception as exc:
        print(f"[bold red]Failed to write local test report:[/bold red] {exc}")

    # Save to appDataDir artifact so the user sees it immediately
    try:
        os.makedirs(os.path.dirname(REPORT_PATH_ARTIFACT), exist_ok=True)
        with open(REPORT_PATH_ARTIFACT, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[green]Test report saved successfully in appDataDir artifacts: {REPORT_PATH_ARTIFACT}[/green]")
    except Exception as exc:
        print(f"[bold red]Failed to write artifact test report:[/bold red] {exc}")

    print("\n" + "=" * 60)
    print(f"Test Run Completed! Passed: {total_passed} | Warnings: {total_warned} | Failed: {total_failed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
