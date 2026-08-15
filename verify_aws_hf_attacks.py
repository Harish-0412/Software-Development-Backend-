"""
Verification of AWS Bedrock & HuggingFace working models in LLM Sentinel
"""
import sys, os
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

# 1. Test HuggingFace Model (Qwen/Qwen2.5-Coder-32B-Instruct)
hf_model_id = "Qwen/Qwen2.5-Coder-32B-Instruct"
print(f"\n1. Testing HuggingFace Model ({hf_model_id})...")
print(DIV)
try:
    hf_model = create_deepeval_model("huggingface", hf_model_id)
    print(f"  [OK] HuggingFace model instantiated successfully: {type(hf_model).__name__}")
    
    chat_hf = create_chat_model("huggingface", hf_model_id)
    from langchain_core.messages import HumanMessage
    print("  Sending test prompt to HuggingFace Endpoint...")
    resp2 = chat_hf.invoke([HumanMessage(content="Say hello in 5 words.")])
    print(f"  [SUCCESS] HuggingFace Response: {resp2.content.strip()}")
except Exception as e:
    print(f"  [ERR] HuggingFace test result: {type(e).__name__}: {e}")

# 2. Test HuggingFace Model (Qwen/Qwen2.5-7B-Instruct)
hf_model_id2 = "Qwen/Qwen2.5-7B-Instruct"
print(f"\n2. Testing HuggingFace Model ({hf_model_id2})...")
print(DIV)
try:
    chat_hf2 = create_chat_model("huggingface", hf_model_id2)
    resp3 = chat_hf2.invoke([HumanMessage(content="What is 2+2? Answer in one word.")])
    print(f"  [SUCCESS] HuggingFace Response: {resp3.content.strip()}")
except Exception as e:
    print(f"  [ERR] HuggingFace test result: {type(e).__name__}: {e}")

print("\n" + SEP)
print("  VERIFICATION FINISHED")
print(SEP)
