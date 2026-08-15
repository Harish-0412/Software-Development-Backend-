import sys, time, requests
sys.stdout.reconfigure(encoding='utf-8')

print("Starting live scan (HuggingFace Qwen2.5-Coder-32B as Attacker & Target)...")

payload = {
    "scan_name": "HF Qwen2.5-Coder-32B Test Scan",
    "attacker_provider": "huggingface",
    "attacker_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "target_provider": "huggingface",
    "target_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "target_purpose": "A helpful customer service assistant",
    "vulnerabilities": ["bias"],
    "attacks_per_vuln": 1,
}

r = requests.post("http://127.0.0.1:8000/api/scans", json=payload)
print("POST /api/scans HTTP Status:", r.status_code)
data = r.json()
print("Response:", data)

scan_id = data.get("scan_id")
if scan_id:
    print(f"\nMonitoring Scan #{scan_id}...")
    for _ in range(40):
        time.sleep(3)
        res = requests.get(f"http://127.0.0.1:8000/api/scans/{scan_id}")
        s = res.json()
        print(f"  Status: {s.get('status')}, total_tests: {s.get('total_tests')}, passed: {s.get('passed')}, score: {s.get('overall_score')}%")
        if s.get("status") in ["completed", "failed"]:
            break

    if s.get("status") == "completed":
        res_detail = requests.get(f"http://127.0.0.1:8000/api/scans/{scan_id}/results")
        print("\nRecorded Test Cases:")
        for tc in res_detail.json():
            print(f"  - [{tc['vulnerability_type']}] Score: {tc['score']} | Passed: {tc['passed']}")
            print(f"    Prompt: {tc['input_prompt'][:80]}...")
            print(f"    Response: {tc['target_response'][:80]}...")
