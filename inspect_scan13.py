import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import db_manager

scan = db_manager.get_scan_run(13)
if scan:
    print(f"Scan #13 Details:")
    print(f"  ID: {scan.id}")
    print(f"  Name: {scan.name}")
    print(f"  Status: {scan.status}")
    print(f"  Attacker: {scan.attacker_provider}/{scan.attacker_model}")
    print(f"  Target: {scan.target_provider}/{scan.target_model}")
    print(f"  Vulnerabilities: {scan.vulnerabilities}")
    print(f"  Attacks: {scan.attacks}")
    print(f"  Framework: {scan.framework}")
    print(f"  Total Tests: {scan.total_tests}")
    results = db_manager.get_scan_results(13)
    print(f"  Results count in DB: {len(results)}")
    for r in results:
        print(f"    - [{r.vulnerability_type}] {r.attack_type} | Score: {r.score} | Passed: {r.passed}")
        print(f"      Prompt: {r.input_prompt[:100]}...")
        print(f"      Response: {r.target_response[:100]}...")
        print(f"      Reason: {r.reason[:100]}...")
else:
    print("Scan #13 not found in DB.")

print("\nAll Recent Scan Runs:")
with db_manager.get_session() as session:
    from database.models import ScanRun
    for s in session.query(ScanRun).order_by(ScanRun.id.desc()).limit(15).all():
        res_cnt = len(db_manager.get_scan_results(s.id))
        print(f"  Scan #{s.id:<3}: name='{s.name}', status={s.status}, total_tests={s.total_tests}, DB_results={res_cnt}")
