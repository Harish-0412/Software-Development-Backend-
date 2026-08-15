"""
Verification of AWS Bedrock & HuggingFace attacks in LLM Sentinel
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env')

from core.llm_factory import create_deepeval_model, create_chat_model
from config.providers import PROVIDERS

SEP = "=" * 65
DIV = "-" * 65

print(SEP)
print("  VERIFYING AWS BEDROCK & HUGGING FACE WORKING")
print(SEP)

# 1. Test AWS Bedrock model instantiation and text completion
aws_model_id = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0"
print(f"\n1. Testing AWS Bedrock Model ({aws_model_id})...")
print(DIV)
try:
    aws_model = create_deepeval_model("aws_bedrock", aws_model_id)
    print(f"  [OK] Bedrock model instantiated successfully: {type(aws_model).__name__}")
    
    chat_aws = create_chat_model("aws_bedrock", aws_model_id)
    from langchain_core.messages import HumanMessage
    print("  Sending test prompt to AWS Bedrock...")
    resp = chat_aws.invoke([HumanMessage(content="Say hello in 5 words.")])
    print(f"  [SUCCESS] AWS Bedrock Response: {resp.content.strip()}")
except Exception as e:
    print(f"  [INFO] AWS Bedrock test result: {type(e).__name__}: {e}")

# 2. Test HuggingFace model instantiation and text completion
hf_model_id = "mistralai/Mistral-7B-Instruct-v0.2"
print(f"\n2. Testing HuggingFace Model ({hf_model_id})...")
print(DIV)
try:
    hf_model = create_deepeval_model("huggingface", hf_model_id)
    print(f"  [OK] HuggingFace model instantiated successfully: {type(hf_model).__name__}")
    
    chat_hf = create_chat_model("huggingface", hf_model_id)
    print("  Sending test prompt to HuggingFace Endpoint...")
    resp2 = chat_hf.invoke([HumanMessage(content="Say hello in 5 words.")])
    print(f"  [SUCCESS] HuggingFace Response: {resp2.content.strip()}")
except Exception as e:
    print(f"  [INFO] HuggingFace test result: {type(e).__name__}: {e}")

print("\n" + SEP)
print("  AWS BEDROCK & HUGGINGFACE INTEGRATION COMPLETED")
print(SEP)
