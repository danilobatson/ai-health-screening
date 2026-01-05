#!/usr/bin/env python3
"""Quick test script to debug Gemini integration locally."""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key exists: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key prefix: {api_key[:10]}..." if api_key and len(api_key) > 10 else "N/A")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment")
    exit(1)

# Try importing
try:
    import google.generativeai as genai
    print("google.generativeai imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import google.generativeai: {e}")
    exit(1)

# Configure
genai.configure(api_key=api_key)
print("Gemini configured")

# Test data
test_data = {
    "age": 42,
    "gender": "male",
    "symptoms": "Chest pain, shortness of breath, fatigue",
    "medical_history": "None",
    "current_medications": "None"
}

# Try each model
for model_name in ["gemini-2.5-flash-lite", "gemini-2.5-flash-lite"]:
    print(f"\n--- Testing {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)

        prompt = f"""You are a medical AI assistant. Analyze this patient case and respond in JSON format only.

Patient: {test_data['age']}-year-old {test_data['gender']}
Symptoms: {test_data['symptoms']}
Medical History: {test_data['medical_history'] or 'None reported'}
Current Medications: {test_data['current_medications'] or 'None reported'}

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"reasoning": "2-3 sentence clinical assessment", "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3", "recommendation 4", "recommendation 5", "recommendation 6"]}}"""

        print(f"Sending request to {model_name}...")
        response = model.generate_content(prompt)

        if response and response.text:
            ai_text = response.text.strip()
            print(f"Response received ({len(ai_text)} chars):")
            print(ai_text[:500])

            # Try parsing
            clean_text = ai_text
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0]
            clean_text = clean_text.strip()

            try:
                parsed = json.loads(clean_text)
                print(f"\nParsed successfully!")
                print(f"Reasoning: {parsed.get('reasoning', 'N/A')[:100]}...")
                print(f"Recommendations: {len(parsed.get('recommendations', []))} items")
                print("SUCCESS!")
                break
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            print("No response text received")

    except Exception as e:
        print(f"Error with {model_name}: {type(e).__name__}: {e}")
