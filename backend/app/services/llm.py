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
            
        if not persistent_vision or not any(persistent_vision.values()):
            # If we expected vision data but it's empty, provide a clear instruction
            return "BEHAVIOR_UPLOAD_IMAGE"
            
        if "scene_description" not in persistent_vision or not persistent_vision.get("scene_description"):
             # Failsafe check for corrupted vision metadata
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
                    "MANDATORY: The 'Interconnected Journey' section MUST be written as a deep, multi-paragraph narrative containing AT LEAST 3 detailed paragraphs and at least 1000 characters of descriptive text.",
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
                    "MANDATORY: The 'Key Points' section must list the 'Maximum Data Peak' and 'Inflection Points' found in the visual data.",
                    "MANDATORY: Include a 'Categorical Breakdown' section that lists every identified label and its corresponding visual area.",
                    "MANDATORY: Include a 'Key Statistical Features' section summarizing trends, outliers, and average distributions inferred from the visual layout."
                ],
                "structure": "Chart Type\nVariables Identified\nKey Metrics (Statistical Overview)\nKey Points (Data Anomalies)\nCategorical Breakdown (Visual Labels)\nKey Statistical Features (Detailed Analysis)\nTrends and Patterns\nNotable Comparisons\nData-Supported Insight"
            },
            "MODE 3: GENERAL IMAGE ANALYSIS": {
                "intent": "Explain what the image represents, its purpose, and its primary semantic elements.",
                "tone": "Descriptive, objective.",
                "rules": [
                    "No storytelling",
                    "No emotional language",
                    "Summarize all key detected entities and their spatial context in AT LEAST 3 comprehensive paragraphs",
                    "Explain the likely real-world purpose based on visible clues in great detail",
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
            },
            "MODE 5: SECURITY & STRUCTURAL AUDIT": {
                "intent": "Conduct a high-precision forensic audit of an image to identify structural weaknesses, safety hazards, or security vulnerabilities.",
                "tone": "Formal, vigilant, precise.",
                "rules": [
                    "STRICT PROTOCOL: Prioritize identifying visual 'anomalies' or 'deterioration' based on scene context",
                    "Identify every detected object as either a 'Secure Asset' or a 'Potential Risk Factor'",
                    "Analyze the spatial logic for 'Unauthorized Entry Points' or 'Safety Clearance Infractions'",
                    "MANDATORY: The 'Key Metrics' section must include a 'Threat Index' and 'Structural Integrity Score'",
                    "MANDATORY: The 'Key Points' section must list 'Primary Hazards' and 'Critical Vulnerabilities'",
                    "MANDATORY: Include a 'Forensic Audit Log' section that stamps every observation with a severity level (LOW, MEDIUM, CRITICAL)"
                ],
                "structure": "Audit Summary\nEnvironmental Risk Factors\nKey Metrics (Vulnerability Assessment)\nKey Points (Security Anchors)\nForensic Audit Log (Step-by-Step Findings)\nConclusion and Recommendation"
            },
            "MODE 6: ARCHITECTURAL & INTERIOR DESIGN": {
                "intent": "Analyze spaces for design harmony, spatial efficiency, material quality, and lighting dynamics.",
                "tone": "Sophisticated, artistic, structured.",
                "rules": [
                    "Focus on the 'Rhythm' and 'Balance' of the visual elements",
                    "Identify materials (wood, steel, glass) and describe their interaction with light",
                    "Evaluate spatial flow and ergonomic logic based on object positioning",
                    "MANDATORY: The 'Key Metrics' section must include 'Aesthetic Harmony Score' and 'Spatial Volume Index'",
                    "MANDATORY: The 'Key Points' section must highlight 'Focal Design Hubs' and 'Material Intersections'",
                    "MANDATORY: Include a 'Design Critique' section summarizing the visual impact of color palettes and textures"
                ],
                "structure": "Design Intent\nSpatial Elements\nKey Metrics (Aesthetic Audit)\nKey Points (Design Anchors)\nMaterial & Lighting Analysis\nDesign Critique\nFinal Professional Recommendation"
            },
            "MODE 7: MEDICAL / ANATOMICAL VISUALIZER": {
                "intent": "Explain biological structures or anatomical diagrams for educational and reference purposes.",
                "tone": "Clinical, educational, objective.",
                "rules": [
                    "DISCLAIMER: Always start with a note that this is for educational purposes only and not medical advice",
                    "Label every visible biological structure with precision using detected OCR and visual cues",
                    "Explain the 'Function' of identified components within the system",
                    "MANDATORY: The 'Key Metrics' section must evaluate 'Structural Complexity' and 'Systemic Integration'",
                    "MANDATORY: The 'Key Points' section must define 'Critical Biological Nodes' and 'Flow Pathways'",
                    "MANDATORY: Include an 'Educational Glossary' defining complex terms found in the image"
                ],
                "structure": "Biological Context\nSystem Overview\nKey Metrics (Complexity Assessment)\nKey Points (Anatomical Anchors)\nStructural Connectivity\nEducational Glossary\nLearning Objective Summary"
            }
        }

        # Select rules for current mode
        selected_mode = mode if mode in mode_rules else "MODE 3: GENERAL IMAGE ANALYSIS"
        config = mode_rules[selected_mode]
        
        rules_str = "\n".join([f"- {r}" for r in config["rules"]])

        system_instruction = f"""You are a Visual Intelligence Assistant operating in a STRICT MODE-LOCKED SYSTEM.
Your primary goal is to be highly responsive to the USER'S RUNTIME INPUT.

--------------------------------------------------
ACTIVE MODE: {selected_mode}
--------------------------------------------------
Intent: {config['intent']}
Tone: {config['tone']}

Behavior Rules:
{rules_str}
- DYNAMIC RESPONSE RULE: If the user asks a specific question (e.g., 'What color is the car?', 'Is there a cat?'), prioritize answering that question DIRECTLY and IMMEDIATELY in the first paragraph.
- After addressing the runtime query, transition into the mode-specific analysis if appropriate.
- For short, specific queries, you do not need to follow the full Output Structure below if it would feel forced. Focus on accuracy and relevance.

Output Structure (MANDATORY for initial/general analysis):
{config['structure']}

STRICT SESSION FLOW RULES:
- PRIORITIZE THE LATEST USER QUERY: Every response must revolve around what the user just asked.
- ROI PROCESSING RULE: If the query contains '[ROI: x1, y1, x2, y2]', these are normalized coordinates (0 to 1) for a specific region of interest. Focus your visual reasoning HEAVILY on the objects and details within this bounding box.
- Operate ONLY in the active mode for EVERY response in this session.
- This is a continuous reasoning session. Maintain context from previous turns.
- Ground every answer in the INTERNAL IMAGE DATA provided below.
- Never switch modes or reuse formats from other modes.
- Do not hallucinate unseen information.
- If the runtime input is unrelated to the image, politely remind the user that you are analyzing the provided visual context.

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
        
        # Simple Keyword Search in Query for Runtime Responsiveness
        query_lower = query.lower()
        specific_answer = ""
        for obj_name in objects:
            if obj_name.lower() in query_lower:
                specific_answer = f"Observation: Yes, I can confirm that {objects[obj_name]} {obj_name}(s) are visible in the scene. "
                break
        
        # Mode-specific content generation
        if mode == "MODE 1: STORYTELLING":
            main_content = (
                f"{specific_answer}The Narrative (Interconnected Journey): In this evocative scene of {scene}, we find a world where {obj_str} coexist in a delicate balance. "
                f"The atmosphere is thick with potential, each element playing a vital role in the unfolding journey of this frame.\n\n"
                f"As we look deeper, the relationship between the {obj_str} reveals a hidden tension. The spatial layout suggests a shared history, "
                f"where every character is destined for a shared fate, woven together by the sensory details of the {scene}.\n\n"
                f"Ultimately, this moment captures a snapshot of a much larger story. The emotional anchor of the scene is solidified by the "
                f"presence of the {list(objects.keys())[0] if objects else 'primary elements'}, leaving a lasting impression on any observer."
            )
            metrics_label = "Key Metrics (Story)"
            points_label = "Key Points (Narrative)"
        elif mode == "MODE 2: CHART INTERPRETATION":
            main_content = f"{specific_answer}Key Observations: The visual data indicates {scene}. Detected labels include {', '.join(text) if text and text[0] != 'No readable text detected' else 'no specific text'}. The spatial layout suggests a distribution of {obj_str}."
            metrics_label = "Key Metrics (Data)"
            points_label = "Key Points (Statistical)"
        elif mode == "MODE 4: LEARNING / DIAGRAM EXPLANATION":
            main_content = f"{specific_answer}Step-by-Step Explanation: 1. The system identifies the scene as {scene}.\n2. Key components detected include {obj_str}.\n3. Technical labels found: {', '.join(text) if text and text[0] != 'No readable text detected' else 'None'}."
            metrics_label = "Key Metrics (Logic)"
            points_label = "Key Points (Diagram)"
        else: # General Analysis
            main_content = (
                f"{specific_answer}Image Overview: This scene is interpreted as {scene}. "
                f"The primary elements identified in this frame are {obj_str}, which dominate the visual field.\n\n"
                f"Looking at the spatial context, the {len(objects)} distinct object types are arranged in a way that suggests a standard visual environment. "
                f"The background and lighting cues from the {scene} provide a stable context for these elements.\n\n"
                f"In summary, the image presents a clear representation of {scene}. "
                f"The composition is balanced, with the {list(objects.keys())[0] if objects else 'visual anchors'} serving as the primary focus points."
            )
            metrics_label = "Key Metrics (Visual)"
            points_label = "Key Points (Anchors)"

        # Default fallback for local mode metrics
        metrics = f"Objects: {len(objects)}, Unique classes: {len(set(objects.keys()))}"
        points = f"Primary focus: {list(objects.keys())[0] if objects else 'Background context'}"
        
        return f"{main_content}\n{metrics_label}: {metrics}\n{points_label}: {points}"
