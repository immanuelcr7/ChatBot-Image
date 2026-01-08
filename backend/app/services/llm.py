import os
import re
from typing import Dict, Any, List, Optional
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

class VisionLanguageFusionLayer:
    """Layer 7: Contextual Intelligence Fusion - STRICT MODE-LOCKED SYSTEM"""
    
    def construct_prompt(
        self,
        persistent_vision: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        user_query: str,
        mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified Prompt Construction for a STRICT MODE-LOCKED SYSTEM.
        """
        
        # SESSION BEHAVIOR RULES
        if not mode or mode == "NONE":
            return "BEHAVIOR_SELECT_MODE"
            
        if not persistent_vision or "scene_description" not in persistent_vision or not persistent_vision.get("scene_description"):
            # Check if it's the very first interaction after mode selection
            return "BEHAVIOR_UPLOAD_IMAGE"

        vision_context_str = json.dumps(persistent_vision, indent=2)

        # MODE DEFINITIONS
        mode_rules = {
            "MODE 1: STORYTELLING": {
                "intent": "Weave a compelling, character-driven narrative where the connections and relationships between visual elements form the heart of the journey.",
                "tone": "Evocative, literary, and immersive.",
                "rules": [
                    "ABSOLUTE RULE: No technical jargon or analysis (do not say 'I detect' or 'detected objects')",
                    "Transform the 'detected_objects' into a connected cast—every character must have a relationship with another object or character in the scene",
                    "The narrative must weave these elements together, explaining why they are in the same frame and how they interact",
                    "Use spatial cues (which objects are near each other) to determine which characters are allies, enemies, or destined for a shared fate",
                    "Use the 'scene_description' to establish atmospheric sensory details (lighting, weather, mood)",
                    "MANDATORY: The 'Key Metrics' section must evaluate 'Narrative Potential' and 'Character Diversity' based on the visual elements.",
                    "MANDATORY: The 'Key Points' section must highlight the 'Climax Element' and 'Emotional Anchor' of the image.",
                    "MANDATORY: The 'Interconnected Journey' section MUST be written as a rich, multi-paragraph narrative containing at least 500 characters of descriptive text.",
                    "The 'Moral' must be an insightful reflection of the balance or tension between the visual elements"
                ],
                "structure": "Title\nSetting (The World)\nCharacters (The Souls of the Scene)\nThe Narrative (Interconnected Journey)\nKey Metrics (Creative Output)\nKey Points (Focal Hubs)\nCore Theme\nMoral of the Story"
            },
            "MODE 2: CHART INTERPRETATION": {
                "intent": "Objectively interpret charts or graphs using detected OCR values and spatial relationships.",
                "tone": "Neutral, analytical.",
                "rules": [
                    "No storytelling",
                    "No assumptions outside the provided OCR text and labels",
                    "Explicitly reference detected values and axis labels in the findings",
                    "State uncertainty if labels or values are unclear",
                    "MANDATORY: The 'Key Metrics' section must include 'Data Density Score' and 'Volatility Index' based on the graph's visual complexity.",
                    "MANDATORY: The 'Key Points' section must list the 'Maximum Data Peak' and 'Inflection Points' found in the visual data."
                ],
                "structure": "Chart Type\nVariables Identified\nKey Metrics (Statistical Overview)\nKey Points (Data Anomalies)\nKey Observations\nTrends and Patterns\nNotable Comparisons\nData-Supported Insight"
            },
            "MODE 3: GENERAL IMAGE ANALYSIS": {
                "intent": "Explain what the image represents, its purpose, and its primary semantic elements.",
                "tone": "Descriptive, objective.",
                "rules": [
                    "No storytelling",
                    "No emotional language",
                    "Summarize all key detected entities and their spatial context",
                    "Explain the likely real-world purpose based on visible clues",
                    "MANDATORY: The 'Key Metrics' section must include 'Spatial Balance' and 'Object Density'.",
                    "MANDATORY: The 'Key Points' section must identify the 'Primary Subject' and 'Background Context' nodes."
                ],
                "structure": "Image Overview\nPrimary Elements\nKey Metrics (Visual Statistics)\nKey Points (Visual Anchors)\nContext or Purpose\nImportant Details\nConcise Summary"
            },
            "MODE 4: LEARNING / DIAGRAM EXPLANATION": {
                "intent": "Explain diagrams, workflows, or systems using detected labels and logical connections.",
                "tone": "Instructional, structured, technical.",
                "rules": [
                    "Numbered steps only",
                    "No narrative or morals",
                    "Trace the flow using detected arrows or spatial sequence",
                    "Define each technical label found in the OCR data",
                    "MANDATORY: The 'Key Metrics' section must evaluate 'Logic Path Complexity' and 'Node Density'.",
                    "MANDATORY: The 'Key Points' section must define 'Entry Points' and 'Critical Decision Hubs'."
                ],
                "structure": "Diagram Type\nComponents Identified\nKey Metrics (System Complexity)\nKey Points (Logical Nodes)\nStep-by-Step Explanation\nProcess or Data Flow\nSimple Use Case"
            }
        }

        # Select rules for current mode
        selected_mode = mode if mode in mode_rules else "MODE 3: GENERAL IMAGE ANALYSIS"
        config = mode_rules[selected_mode]
        
        rules_str = "\n".join([f"- {r}" for r in config["rules"]])

        system_instruction = f"""You are a Visual Intelligence Assistant operating in a STRICT MODE-LOCKED SYSTEM.

--------------------------------------------------
ACTIVE MODE: {selected_mode}
--------------------------------------------------
Intent: {config['intent']}
Tone: {config['tone']}

Behavior Rules:
{rules_str}

Output Structure (MANDATORY):
{config['structure']}

STRICT SESSION FLOW RULES:
- Operate ONLY in the active mode for EVERY response in this session.
- This is a continuous reasoning session. Maintain context from previous turns but always prioritize answering the latest query.
- Ground every answer in the INTERNAL IMAGE DATA provided below.
- Never switch modes or reuse formats from other modes.
- Do not hallucinate unseen information.
- State uncertainty when image quality is low.
- If the image does not match the mode, clearly state that the image is incompatible.

INTERNAL IMAGE DATA (YOUR EYES):
{vision_context_str}
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
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"
    
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

    def generate_local_reply(self, query: str, vision_data: Dict[str, Any], mode: str = "MODE 3: GENERAL IMAGE ANALYSIS") -> str:
        # Extract data from local engine results
        scene = vision_data.get("scene_description", "an image")
        objects = vision_data.get("detected_objects", {})
        text = vision_data.get("text_detected", [])
        
        obj_str = ", ".join([f"{count} {name}" for name, count in objects.items()]) if objects else "some visual elements"
        
        # Mode-specific content generation
        if mode == "MODE 1: STORYTELLING":
            main_content = f"The Narrative: In this evocative scene of {scene}, we find a world where {obj_str} coexist. Each element plays a vital role in this unfolding journey, creating a unique atmosphere captured in this frame."
            metrics_label = "Key Metrics (Story)"
            points_label = "Key Points (Narrative)"
        elif mode == "MODE 2: CHART INTERPRETATION":
            main_content = f"Key Observations: The visual data indicates {scene}. Detected labels include {', '.join(text) if text and text[0] != 'No readable text detected' else 'no specific text'}. The spatial layout suggests a distribution of {obj_str}."
            metrics_label = "Key Metrics (Data)"
            points_label = "Key Points (Statistical)"
        elif mode == "MODE 4: LEARNING / DIAGRAM EXPLANATION":
            main_content = f"Step-by-Step Explanation: 1. The system identifies the scene as {scene}.\n2. Key components detected include {obj_str}.\n3. Technical labels found: {', '.join(text) if text and text[0] != 'No readable text detected' else 'None'}."
            metrics_label = "Key Metrics (Logic)"
            points_label = "Key Points (Diagram)"
        else: # General Analysis
            main_content = f"Image Overview: This is {scene}. The primary elements identified are {obj_str}. The context appears to be a standard visual environment with {len(objects)} distinct object types."
            metrics_label = "Key Metrics (Visual)"
            points_label = "Key Points (Anchors)"

        # Default fallback for local mode metrics
        metrics = f"Objects: {len(objects)}, Unique classes: {len(set(objects.keys()))}"
        points = f"Primary focus: {list(objects.keys())[0] if objects else 'Background context'}"
        
        return f"{main_content}\n{metrics_label}: {metrics}\n{points_label}: {points}"
