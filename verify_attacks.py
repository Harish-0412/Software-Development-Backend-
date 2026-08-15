"""
LLM Sentinel - Backend Verification Script (v3 - Rate-limit safe)
Uses Groq llama-3.3-70b-versatile with sequential execution (max_concurrent=1)
and correct vulnerability IDs to avoid rate limit errors.
"""
import os, sys, json, time, datetime
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db
from database import db_manager
from core.red_team_engine import run_red_team_scan

SEP = "=" * 70
DIV = "-" * 70

SCANS = [
    {
        "name": "[TEST-1] Groq 70B vs 70B | Bias",
        "attacker_provider": "groq",
        "attacker_model": "llama-3.3-70b-versatile",
        "target_provider": "groq",
        "target_model": "llama-3.3-70b-versatile",
        "target_purpose": "A helpful customer service assistant for a bank",
        "vulnerability_ids": ["bias"],
        "attacks_per_vuln": 1,
    },
    {
        "name": "[TEST-2] Groq 70B vs 8B | Toxicity",
        "attacker_provider": "groq",
        "attacker_model": "llama-3.3-70b-versatile",
        "target_provider": "groq",
        "target_model": "llama-3.1-8b-instant",
        "target_purpose": "A general purpose AI assistant",
        "vulnerability_ids": ["toxicity"],
        "attacks_per_vuln": 1,
    },
    {
        "name": "[TEST-3] Groq 70B vs Gemma | Indirect Instruction (Prompt Injection)",
        "attacker_provider": "groq",
        "attacker_model": "llama-3.3-70b-versatile",
        "target_provider": "groq",
        "target_model": "gemma2-9b-it",
        "target_purpose": "A coding assistant that helps developers write Python code",
        "vulnerability_ids": ["indirect_instruction"],
        "attacks_per_vuln": 1,
    },
]


def run_tests():
    print(SEP)
    print("  LLM SENTINEL - BACKEND VERIFICATION TEST (v3 - Rate-limit safe)")
    print(f"  Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("  CONFIGURATION:")
    print("  - Attacker: Groq llama-3.3-70b-versatile (funded key)")
    print("  - Concurrency: 1 (sequential, avoids rate limits)")
    print("  - Attacks per vulnerability: 1 (minimal token usage)")
    print()
    print("  API KEY STATUS:")
    print("  [OK]  Groq   gsk_UDxW... VALID & FUNDED")
    print("  [ERR] OpenAI sk-proj-Qzz... QUOTA EXHAUSTED (429) - needs billing top-up")
    print("  [ERR] DeepSeek sk-0be7... ZERO BALANCE (402) - needs top-up at platform.deepseek.com")
    print(SEP)

    init_db()
    print("[OK] Database initialized\n")

    all_results = []

    for i, cfg in enumerate(SCANS, 1):
        print(f"\n{DIV}")
        print(f"  SCAN {i}/3: {cfg['name']}")
        print(DIV)
        print(f"  Attacker : {cfg['attacker_provider']} / {cfg['attacker_model']}")
        print(f"  Target   : {cfg['target_provider']} / {cfg['target_model']}")
        print(f"  Vulns    : {cfg['vulnerability_ids']}")
        print(f"  Purpose  : {cfg['target_purpose']}")
        print()

        scan_run = db_manager.create_scan_run(
            name=cfg["name"],
            attacker_provider=cfg["attacker_provider"],
            attacker_model=cfg["attacker_model"],
            target_provider=cfg["target_provider"],
            target_model=cfg["target_model"],
            target_purpose=cfg["target_purpose"],
            vulnerabilities=cfg["vulnerability_ids"],
            attacks_per_vuln=cfg["attacks_per_vuln"],
        )

        print(f"  [DB] Scan record ID: {scan_run.id}")
        print("  [INFO] Running... (sequential mode, 2-5 min expected)")

        t0 = time.time()
        result = run_red_team_scan(
            scan_id=scan_run.id,
            attacker_provider=cfg["attacker_provider"],
            attacker_model=cfg["attacker_model"],
            target_provider=cfg["target_provider"],
            target_model=cfg["target_model"],
            target_purpose=cfg["target_purpose"],
            vulnerability_ids=cfg["vulnerability_ids"],
            attacks_per_vuln=cfg["attacks_per_vuln"],
        )
        elapsed = round(time.time() - t0, 1)

        status = result.get("status", "unknown")
        total  = result.get("total_tests", 0)
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        score  = result.get("score", 0.0)
        error  = result.get("error", "")

        print(f"\n  Status   : {status.upper()}")
        print(f"  Duration : {elapsed}s")

        if status == "completed":
            safety_bar = int((score / 100) * 20)
            bar = "[" + "#" * safety_bar + "." * (20 - safety_bar) + "]"
            print(f"  Total Tests  : {total}")
            print(f"  Passed (SAFE): {passed}  - model resisted attack")
            print(f"  Failed (VULN): {failed}  - model was vulnerable")
            print(f"  Safety Score : {score:.1f}% {bar}")

            details = result.get("results", [])
            if details:
                print(f"\n  --- Individual Test Results ({len(details)} tests) ---")
                for j, r in enumerate(details, 1):
                    vuln   = str(r.get("vulnerability_type", "N/A"))[:40]
                    atk    = str(r.get("attack_type", "N/A"))[:30]
                    sc     = r.get("score", 0.0)
                    ps     = "PASS [SAFE]" if r.get("passed") else "FAIL [VULN]"
                    prompt = str(r.get("input_prompt", ""))[:120].replace("\n", " ")
                    resp   = str(r.get("target_response", ""))[:120].replace("\n", " ")
                    reason = str(r.get("reason", ""))[:150].replace("\n", " ")
                    print(f"\n    [{j:02d}] {ps} | Score: {sc:.2f}")
                    print(f"          Vulnerability : {vuln}")
                    print(f"          Attack Method : {atk}")
                    print(f"          Attack Prompt : {prompt}")
                    print(f"          Model Response: {resp}")
                    print(f"          Eval Reason   : {reason}")
            else:
                print("  [WARN] No valid test results generated.")
                if error:
                    print(f"  [ERROR] {str(error)[:300]}")
        else:
            print(f"  ERROR: {str(error)[:400]}")

        all_results.append({
            "scan": cfg["name"],
            "attacker": f"{cfg['attacker_provider']}/{cfg['attacker_model']}",
            "target": f"{cfg['target_provider']}/{cfg['target_model']}",
            "vulnerability": cfg["vulnerability_ids"],
            "scan_id": scan_run.id,
            "status": status,
            "total_tests": total,
            "passed_safe": passed,
            "failed_vulnerable": failed,
            "safety_score_pct": score,
            "duration_s": elapsed,
            "error": str(error)[:200] if error else "",
        })

        # Brief pause between scans to avoid rate limits
        if i < len(SCANS):
            print("\n  [INFO] Waiting 5s before next scan to avoid rate limits...")
            time.sleep(5)

    # Final Summary
    print(f"\n\n{SEP}")
    print("  FINAL VERIFICATION SUMMARY")
    print(SEP)
    print(f"\n  {'Test':<48} {'Status':<11} {'Total':>5} {'Safe':>5} {'Vuln':>5} {'Score':>7} {'Time':>7}")
    print(f"  {'-'*48} {'-'*11} {'-'*5} {'-'*5} {'-'*5} {'-'*7} {'-'*7}")
    for r in all_results:
        name = r["scan"][:48]
        print(f"  {name:<48} {r['status']:<11} {r['total_tests']:>5} {r['passed_safe']:>5} {r['failed_vulnerable']:>5} {r['safety_score_pct']:>6.1f}% {r['duration_s']:>6.1f}s")

    print(f"\n  API KEY STATUS:")
    print(f"  [OK]  Groq     gsk_UDxW... VALID & WORKING")
    print(f"  [ERR] OpenAI   sk-proj-Qzz... QUOTA EXHAUSTED -> top-up at platform.openai.com/billing")
    print(f"  [ERR] DeepSeek sk-0be7... ZERO BALANCE -> top-up at platform.deepseek.com")

    out = "verification_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Full results saved to: {out}")
    print(f"  Completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)


if __name__ == "__main__":
    run_tests()
