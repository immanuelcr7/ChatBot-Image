import os
import re
from typing import Dict, Any, List, Optional
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

class VisionLanguageFusionLayer:
    """Layer 7: Contextual Intelligence Fusion"""
    
    def construct_prompt(
        self,
        persistent_vision: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        user_query: str
    ) -> Dict[str, Any]:
        """
        Unified Prompt Construction.
        Injects persistent visual semantics and dialogue memory into a single reasoning context.
        """
        
        # Structure the vision data clearly for the LLM
        vision_context_str = json.dumps(persistent_vision, indent=2)

        system_instruction = f"""You are 'Visionary', a state-of-the-art Conversational Visual Intelligence Assistant.

CRITICAL INSTRUCTIONS:
1. INTERNAL PERSISTENT IMAGE DATA:
{vision_context_str}

2. CONVERSATIONAL BEHAVIOR:
- You are looking at a single image. Your goal is to discuss it naturally.
- NEVER output raw JSON, technical counts, or mentions of specific models.
- Use HUMAN-LIKE replies. Be warm, professional, and observant.
- PERSISTENCE: The image data above is your 'eyes'. All questions refer to this image context.
- IMPLICIT REFERENCE: Resolve follow-up queries (e.g., "Only blue", "How many?") using history and vision data.

3. DIALOGUE MEMORY:
- Reference previous turns to maintain a seamless flow.
"""

        # Prepare structured data for Gemini API
        contents = []
        
        # Add history
        for turn in conversation_history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": turn["content"]}]
            })
        
        # Add current user query
        contents.append({
            "role": "user",
            "parts": [{"text": user_query}]
        })
        
        return {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents
        }


class ConversationalReasoningLayer:
    """Layer 8: Reasoning Engine with Optimized Gemini Integration"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    async def generate_response(self, prompt_data: Dict[str, Any]) -> str:
        if not self.api_key:
            raise ConnectionError("GEMINI_API_KEY is missing")
        
        # Diagnostic check for initial state
        contents = prompt_data.get("contents", [])
        system_instr = prompt_data.get("system_instruction", {}).get("parts", [{}])[0].get("text", "")
        
        if "{}" in system_instr and len(contents) <= 1:
            return "initial_state"

        # Supported stable models for generateContent
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        
        last_error = ""

        for model_name in models_to_try:
            try:
                url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
                
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(url, json=prompt_data)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "candidates" in data and data["candidates"]:
                            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    last_error = f"{response.status_code}"
                    
            except Exception as e:
                last_error = str(e)
                continue
                
        raise ConnectionError(f"All models failed: {last_error}")


class LocalResponseLayer:
    """Fallback Layer: Generates natural responses from local vision data without external API."""

    def generate_local_reply(self, query: str, vision_data: Dict[str, Any]) -> str:
        query_lower = query.lower()
        
        # Extract data from local engine results
        scene = vision_data.get("scene_description", "an image")
        objects = vision_data.get("detected_objects", {})
        text = vision_data.get("text_detected", [])
        
        # Simple rule-based natural language generation
        if any(word in query_lower for word in ["text", "say", "read", "ocr", "write"]):
            if text and "No readable text" not in text[0]:
                return f"I can see some text in the image that says: \"{', '.join(text)}\"."
            return "I couldn't find any readable text in this particular image."

        if any(word in query_lower for word in ["count", "how many", "amount"]):
            if "car" in query_lower:
                count = objects.get("car", 0)
                return f"I've counted {count} car{'s' if count != 1 else ''} in the scene."
            if "person" in query_lower or "people" in query_lower:
                count = objects.get("person", 0)
                return f"I detect {count} person{'s' if count != 1 else ''} in the view."
            if "bike" in query_lower:
                count = objects.get("bike", 0)
                return f"There {'is' if count == 1 else 'are'} {count} bike{'s' if count != 1 else ''} visible."

        if any(word in query_lower for word in ["what", "describe", "look", "see", "story"]):
            return f"The scene appears to be {scene}. My local sensors also detected {objects.get('car', 0)} cars and {objects.get('person', 0)} people."

        # Default fallback for local mode
        return f"Based on my local analysis, this is {scene}. I can also help you count specific objects or read any text I find."
