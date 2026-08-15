"""
AWS Bedrock + HuggingFace Connection Verification
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('.env')

SEP = "=" * 65
DIV = "-" * 65

print(SEP)
print("  LLM SENTINEL - AWS & HUGGINGFACE INTEGRATION TEST")
print(SEP)

# ─── Step 1: Provider Detection ─────────────────────────────────────
print()
print("STEP 1: Provider Detection")
print(DIV)
from config.providers import get_configured_providers, PROVIDERS
configured = get_configured_providers()
for pid in ["aws_bedrock", "huggingface"]:
    status = "[OK]  DETECTED" if pid in configured else "[ERR] NOT DETECTED"
    p = PROVIDERS[pid]
    print(f"  {status} - {p.display_name}")
    for key in p.env_keys:
        val = os.environ.get(key, "")
        if len(val) > 12:
            masked = val[:8] + "..." + val[-4:]
        elif val:
            masked = val
        else:
            masked = "(empty)"
        print(f"         {key} = {masked}")
print()

# ─── Step 2: HuggingFace API Test ───────────────────────────────────
print("STEP 2: HuggingFace API Connection")
print(DIV)
try:
    import requests
    token = os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token via whoami
    r = requests.get("https://huggingface.co/api/whoami", headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f"  [OK] Token VALID")
        print(f"       Username : {data.get('name', 'N/A')}")
        print(f"       Type     : {data.get('type', 'N/A')}")
        orgs = [o.get("name") for o in data.get("orgs", [])]
        print(f"       Orgs     : {', '.join(orgs) if orgs else 'none'}")

        # Test model inference - small fast model
        print()
        print("  Testing Inference API (facebook/bart-large-mnli)...")
        payload = {"inputs": "Tell me a fun fact about space in one sentence."}
        r2 = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers=headers, json=payload, timeout=30
        )
        if r2.status_code == 200:
            print(f"  [OK] Inference API WORKING - HTTP 200")
            resp = r2.json()
            if isinstance(resp, list):
                print(f"       Response type : list ({len(resp)} items)")
            elif isinstance(resp, dict):
                print(f"       Response keys : {list(resp.keys())[:5]}")
        elif r2.status_code == 503:
            print(f"  [INFO] Model loading (503) - this is normal, model warms up on first call")
            print(f"         Response: {r2.text[:200]}")
        else:
            print(f"  [WARN] Inference API returned HTTP {r2.status_code}")
            print(f"         Response: {r2.text[:300]}")

        # Test text generation with a smaller model
        print()
        print("  Testing Text Generation (distilgpt2)...")
        r3 = requests.post(
            "https://api-inference.huggingface.co/models/distilgpt2",
            headers=headers,
            json={"inputs": "The future of AI is", "parameters": {"max_new_tokens": 30}},
            timeout=30
        )
        if r3.status_code == 200:
            gen = r3.json()
            if isinstance(gen, list) and gen:
                text = gen[0].get("generated_text", "")[:150]
                print(f"  [OK] Text generation WORKING")
                print(f"       Generated: {text}")
            else:
                print(f"  [OK] Response received: {str(gen)[:150]}")
        elif r3.status_code == 503:
            print(f"  [INFO] distilgpt2 loading (503) - token is valid, model just warming up")
        else:
            print(f"  [WARN] HTTP {r3.status_code}: {r3.text[:200]}")

    else:
        print(f"  [ERR] Token INVALID - HTTP {r.status_code}")
        print(f"         {r.text[:300]}")
except Exception as e:
    print(f"  [ERR] HuggingFace test EXCEPTION: {e}")

print()

# ─── Step 3: AWS Bedrock Test ────────────────────────────────────────
print("STEP 3: AWS Bedrock Connection")
print(DIV)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    region = os.environ.get("AWS_DEFAULT_REGION", "ap-south-2")

    print(f"  Region        : {region}")
    print(f"  Access Key ID : {access_key[:8]}...{access_key[-4:]}")

    # Step 3a: Verify credentials via STS
    print()
    print("  Verifying IAM credentials via STS GetCallerIdentity...")
    sts = boto3.client(
        "sts",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    identity = sts.get_caller_identity()
    print(f"  [OK] AWS credentials VALID")
    print(f"       Account ID : {identity.get('Account', 'N/A')}")
    print(f"       ARN        : {identity.get('Arn', 'N/A')}")
    print(f"       User ID    : {identity.get('UserId', 'N/A')}")

    # Step 3b: Check Bedrock access
    print()
    print("  Checking Bedrock model access...")
    bedrock = boto3.client(
        "bedrock",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    try:
        models_response = bedrock.list_foundation_models(byOutputModality="TEXT")
        models = models_response.get("modelSummaries", [])
        print(f"  [OK] Bedrock API accessible - {len(models)} text models available in {region}")
        # Show first 5
        for m in models[:5]:
            mid = m.get("modelId", "N/A")
            mname = m.get("modelName", "N/A")
            print(f"       - {mid} ({mname})")
        if len(models) > 5:
            print(f"       ... and {len(models) - 5} more")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code in ("AccessDeniedException", "UnauthorizedException"):
            print(f"  [WARN] Bedrock API - Access Denied: {msg}")
            print(f"         Your IAM user needs 'bedrock:ListFoundationModels' permission")
            print(f"         Credentials are VALID but Bedrock permissions may be limited")
        else:
            print(f"  [WARN] Bedrock API error ({code}): {msg}")

    # Step 3c: Try a Bedrock inference call
    print()
    print("  Testing Bedrock InvokeModel (amazon.titan-text-lite-v1)...")
    bedrock_rt = boto3.client(
        "bedrock-runtime",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    import json
    try:
        response = bedrock_rt.invoke_model(
            modelId="amazon.titan-text-lite-v1",
            body=json.dumps({
                "inputText": "Say hello in one sentence.",
                "textGenerationConfig": {"maxTokenCount": 50, "temperature": 0.0}
            }),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        output_text = result.get("results", [{}])[0].get("outputText", "").strip()
        print(f"  [OK] Bedrock InvokeModel WORKING!")
        print(f"       Model    : amazon.titan-text-lite-v1")
        print(f"       Response : {output_text[:200]}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        print(f"  [WARN] InvokeModel ({code}): {msg}")
        if "Could not resolve" in msg or "endpoint" in msg.lower():
            print(f"         Note: Bedrock may not be available in region {region}")
            print(f"         Consider switching to us-east-1 or us-west-2")

except NoCredentialsError:
    print(f"  [ERR] AWS credentials not found in environment")
except Exception as e:
    print(f"  [ERR] AWS test EXCEPTION: {type(e).__name__}: {e}")

# ─── Final Summary ───────────────────────────────────────────────────
print()
print(SEP)
print("  FINAL INTEGRATION STATUS")
print(SEP)
from config.providers import get_configured_providers
configured = get_configured_providers()
all_providers = ["openai", "groq", "deepseek", "aws_bedrock", "huggingface"]
for pid in all_providers:
    if pid in configured:
        p = configured[pid]
        print(f"  [OK]  {p.display_name:<20} CONNECTED to project")
    else:
        p = PROVIDERS.get(pid)
        name = p.display_name if p else pid
        print(f"  [--]  {name:<20} not configured")
print(SEP)
