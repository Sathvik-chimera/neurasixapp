"""
financial_advisor_bot.py
Simple implementation of a financial advisor chatbot using AWS Bedrock API with Claude
"""
 
import json
import boto3
from botocore.config import Config
import os
from prompt import FINANCIAL_ADVISOR_PROMPT
from dotenv import load_dotenv
load_dotenv()
 
# AWS credentials configuration
# Option 1: Environment variables
# os.environ["AWS_ACCESS_KEY_ID"] = "your_access_key"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret_key"
# os.environ["AWS_REGION"] = "us-east-1"
 
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") 
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") 
AWS_REGION = os.getenv("AWS_REGION")
 
# Bedrock model configuration
MODEL_ID = "us.anthropic.claude-3-5-sonnet-20240620-v1:0"
TEMPERATURE = 0.3
MAX_TOKENS = 4096
TOP_P = 0.9
 
# Initialize conversation history
conversation_history = []
 
def initialize_bedrock_client():
    """
    Initialize and return a Bedrock client with the configured credentials
   """
    config = Config(connect_timeout=5, read_timeout=500, retries={'max_attempts': 5})

    return boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        config=config
    )

def prepare_bedrock_request(user_message):
    """
    Prepare request for Claude 3.5 via Bedrock Messages API
    using the correct allowed roles (user, assistant).
    Inject system prompt as first user message.
    """
    messages = []

    # Inject system prompt as first user message
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": FINANCIAL_ADVISOR_PROMPT}]
    })

    # Add chat history
    for msg in conversation_history:
        if msg["role"] not in ["user", "assistant"]:
            continue  # Skip unsupported roles
        messages.append({
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}]
        })

    # Add new user message
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": user_message}]
    })

    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "messages": messages
    }


 
def invoke_claude(bedrock_client, user_message):
    """
    Send a request to Claude via AWS Bedrock and return the response
    """
    request_body = prepare_bedrock_request(user_message)
    
    try:
        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        response_body = json.loads(response.get('body').read())
        return response_body
    except Exception as e:
        print(f"Error invoking Claude model: {e}")
        return {"completion": f"Error: {str(e)}"}
 
def parse_response(response_body):
    """
    Parse Claude Messages API response and extract the JSON response from the LLM.
    Handles nested JSON strings properly.
    """
    content_blocks = response_body.get("content", [])

    if not content_blocks:
        return {
            "response": "No response received.",
            "confidence": 0
        }

    # Join and strip the response text
    response_text = "\n".join(
        block.get("text", "") for block in content_blocks if block.get("type") == "text"
    ).strip()

    # Attempt first level of JSON parsing
    try:
        first_pass = json.loads(response_text)
        
        # If it's a string again, parse it one more time
        if isinstance(first_pass, str):
            try:
                second_pass = json.loads(first_pass)
                if isinstance(second_pass, dict) and "response" in second_pass:
                    return {
                        "response": second_pass["response"],
                        "confidence": second_pass.get("confidence", 50)
                    }
            except json.JSONDecodeError:
                pass  # Fall through to outer return

        # If the first pass is already a dict
        if isinstance(first_pass, dict) and "response" in first_pass:
            return {
                "response": first_pass["response"],
                "confidence": first_pass.get("confidence", 50)
            }

    except json.JSONDecodeError:
        pass

    # Fallback: treat raw text as plain response
    return {
        "response": response_text,
        "confidence": 50
    }
 
def get_financial_advice(user_message):
    """
    Process a user message and get a response from the financial advisor
    """
    # Initialize the Bedrock client
    bedrock_client = initialize_bedrock_client()
    
    # Get response from Claude
    raw_response = invoke_claude(bedrock_client, user_message)
    print("\n--- Raw LLM Response ---")
    print(json.dumps(raw_response, indent=2))
    parsed_response = parse_response(raw_response)
    # Update conversation history with the actual response text (not the JSON structure)
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    conversation_history.append({
        "role": "assistant",
        "content": parsed_response["response"]  # Store only the response text, not the full JSON
    })
    
    return parsed_response
 
def reset_conversation():
    """Clear the conversation history"""
    global conversation_history
    conversation_history = []
 
def main():
    """Example usage of the financial advisor bot"""
    print("Financial Advisor Bot initialized. Type 'exit' to quit.")
    while True:
        user_input = input("\nYour question: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using the Financial Advisor Bot. Goodbye!")
            break
        if user_input.lower() == "reset":
            reset_conversation()
            print("Conversation history has been reset.")
            continue
        # Get response from the bot
        response = get_financial_advice(user_input)
        # Pretty print the JSON response
        print("\n--- Parsed Response ---")

        print(json.dumps(response, indent=2))
 
if __name__ == "__main__":
    main()
