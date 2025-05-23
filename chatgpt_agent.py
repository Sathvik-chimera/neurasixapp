# chatgpt_agent.py
import openai
import os
import json
from prompt import FINANCIAL_ADVISOR_PROMPT

openai.api_key = "org-k4uCrElkOY5g7KWBMoHEmIGS"
print("OPENAI_API_KEY =", openai.api_key)

conversation_history = []

def get_financial_advice(user_message, country):
    modified_prompt = FINANCIAL_ADVISOR_PROMPT + f"\n\nUser's Selected Country is: {country}."
    messages = [{"role": "system", "content": modified_prompt}] + conversation_history + [{"role": "user", "content": user_message}]

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3
        )
        reply = response.choices[0].message.content
        confidence = 80

    except Exception as e:
        return {"response": str(e), "confidence": 0}

    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": reply})
    return {"response": reply, "confidence": confidence}

def reset_conversation():
    global conversation_history
    conversation_history = []

response = get_financial_advice("What is the best investment strategy for me?", "United States")
print(response)