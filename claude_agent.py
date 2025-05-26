"""
financial_advisor_bot.py
Simple implementation of a financial advisor chatbot using AWS Bedrock API with Claude
"""
 
import json
import boto3
from botocore.config import Config
import os
from prompt import FINANCIAL_ADVISOR_PROMPT
import re
import logging

logger = logging.getLogger(__name__)
# from dotenv import load_dotenv
# load_dotenv()
 
# AWS credentials configuration
# Option 1: Environment variables
# os.environ["AWS_ACCESS_KEY_ID"] = "your_access_key"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret_key"
# os.environ["AWS_REGION"] = "us-east-1"
 
# Option 2: Direct configuration
 

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

def prepare_bedrock_request(user_message, country):
    """
    Prepare request for Claude 3.5 via Bedrock Messages API
    using the correct allowed roles (user, assistant).
    Inject system prompt as first user message.
    """
    messages = []

    # Format prompt with country context
    country_note = f"\n\nUser's Selected Country is: {country}."
    modified_prompt = FINANCIAL_ADVISOR_PROMPT + country_note

    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": modified_prompt}]
    })

    for msg in conversation_history:
        if msg["role"] in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}]
            })

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

 
def invoke_claude(bedrock_client, user_message, country):
    """
    Send a request to Claude via AWS Bedrock and return the response
    """
    request_body = prepare_bedrock_request(user_message, country)
    
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
    If the LLM's JSON is malformed, attempt to extract the {...} substring and clean
    trailing commas before loading. Returns structured response with response and confidence.
    """
    # Grab the content blocks
    content_blocks = response_body.get("content", [])
    if not content_blocks:
        return {"response": "No response received.", "confidence": 0}

    # Join all text pieces
    response_text = "\n".join(
        block.get("text", "") 
        for block in content_blocks 
        if block.get("type") == "text"
    ).strip()

    # Try to parse JSON response
    parsed_result = None
    try:
        parsed_result = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract the {...} and clean it up
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = response_text[start:end+1]
            # Remove any trailing commas before } or ]
            candidate = re.sub(r",\s*}", "}", candidate)
            candidate = re.sub(r",\s*]", "]", candidate)
            try:
                parsed_result = json.loads(candidate)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from response: {response_text}")
                parsed_result = None
        else:
            logger.warning(f"No valid JSON structure found in response: {response_text}")
            parsed_result = None

    # Process the parsed result
    if parsed_result is None:
        # Fallback when JSON parsing completely fails
        return {"response": response_text, "confidence": 50}

    # Handle the expected format with 'response' and 'confidence'
    if isinstance(parsed_result, dict):
        # Check if it has the expected 'response' field
        if 'response' in parsed_result:
            response_value = parsed_result['response']
            confidence_value = parsed_result.get('confidence', 50)
            
            # Ensure confidence is a valid number
            if not isinstance(confidence_value, (int, float)):
                try:
                    confidence_value = float(confidence_value)
                except (ValueError, TypeError):
                    confidence_value = 50
                    logger.warning(f"Invalid confidence value, defaulting to 50: {parsed_result.get('confidence')}")
            
            return {
                'response': response_value,
                'confidence': float(confidence_value)
            }
        
        # Handle alternative formats - check if it's a different structure
        elif any(key.startswith('type') for key in parsed_result.keys()):
            # This might be a different format, log and provide fallback
            logger.info(f"Received alternative JSON format: {parsed_result}")
            return {"response": str(parsed_result), "confidence": 50}
        
        # Handle case where parsed_result is a dict but doesn't have 'response'
        else:
            logger.warning(f"Unexpected JSON format without 'response' field: {parsed_result}")
            # Try to extract meaningful content from the dict
            response_content = str(parsed_result)
            return {"response": response_content, "confidence": 50}
    
    # Handle case where parsed_result is not a dict (e.g., list, string, etc.)
    else:
        logger.warning(f"Unexpected JSON structure (not a dict): {parsed_result}")
        return {"response": str(parsed_result), "confidence": 50}
 
def get_financial_advice(user_message, country):
    """
    Process a user message and get a response from the financial advisor
    """
    # Initialize the Bedrock client
    bedrock_client = initialize_bedrock_client()
    
    # Get response from Claude
    raw_response = invoke_claude(bedrock_client, user_message, country)
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
