from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import time
import json

from ..services.validation import RequestValidationLayer
from ..services.vision import ImagePreProcessingLayer, VisionProcessingLayer
from ..services.memory import MemoryLayer
from ..services.llm import VisionLanguageFusionLayer, ConversationalReasoningLayer, LocalResponseLayer
from ..services.monitoring import monitor
from ..database import save_chat_session

router = APIRouter()

# Core Contextual Infrastructure
validator = RequestValidationLayer()
image_processor = ImagePreProcessingLayer()
vision_engine = VisionProcessingLayer() 
memory = MemoryLayer()
fusion = VisionLanguageFusionLayer()
reasoner = ConversationalReasoningLayer()
local_replier = LocalResponseLayer()


@router.get("/health")
async def health_check():
    return monitor.get_metrics()



@router.post("/chat")
async def chat_endpoint(
    image: Optional[UploadFile] = File(None),
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    mode: str = Form("standard"),
    depth: str = Form("standard"),
    image_preview: Optional[str] = Form(None)
):
    """
    Hybrid Response Gateway with expanded Reasoning and Insight metadata.
    """
    start_time = time.time()
    api_failed = False
    
    try:
        session_id = validator.get_or_create_session_id(session_id)
        clean_query = validator.sanitize_text(query)
        
        # 1. Image Lifecycle & Persistence
        if image:
            image_data = await validator.validate_image(image)
            processed_image = image_processor.process(image_data)
            vision_data = await vision_engine.analyze(processed_image)
            memory.set_vision_context(session_id, vision_data)
        
        # 2. Retrieve Full Context
        full_context = memory.get_context(session_id)
        persistent_vision = full_context.get("persistent_vision", {})
        history = full_context.get("conversation_history", [])

        # 3. Decision Logic: Try Conversational AI (API)
        try:
            prompt_data = fusion.construct_prompt(persistent_vision, history, clean_query, mode=mode)
            
            if prompt_data == "BEHAVIOR_SELECT_MODE":
                raw_response = "Please select a mode to continue."
            elif prompt_data == "BEHAVIOR_UPLOAD_IMAGE":
                raw_response = "Please upload an image to begin."
            else:
                raw_response = await reasoner.generate_response(prompt_data)
                
                if raw_response == "initial_state":
                    raw_response = "Please upload an image to begin."
                
        except (ConnectionError, Exception) as e:
            api_failed = True
            raw_response = local_replier.generate_local_reply(clean_query, persistent_vision, mode=mode)
            
            if not persistent_vision:
                raw_response = "Please upload an image to begin."

        # 4. Dialogue Memory Update
        memory.add_interaction(session_id, clean_query, raw_response)
        
        # 5. Persist to DB if Authenticated
        updated_context = memory.get_context(session_id)
        if user_id:
            save_chat_session(
                session_id=session_id,
                user_id=user_id,
                messages=updated_context.get("conversation_history", []),
                image_preview=image_preview
            )
        
        # 6. Build Smart Suggestions
        suggestions = ["Tell me more about the layout", "Are there any risks?", "Describe the colors"]
        if persistent_vision.get("risk_assessment") and "standard" not in persistent_vision["risk_assessment"].lower():
            suggestions.append("How can the risks be mitigated?")

        latency = time.time() - start_time
        return {
            "session_id": session_id,
            "response": {
                "text": raw_response,
                "smart_suggestions": suggestions,
                "mode": "local" if api_failed else "hybrid"
            },
            "visual_summary": persistent_vision.get("scene_description", "Active"),
            "vision_metadata": persistent_vision,
            "risk_assessment": persistent_vision.get("risk_assessment", "Safe"),
            "narrative": persistent_vision.get("scene_description", "No narrative yet."),
            "latency": round(latency, 2)
        }
        
    except Exception as e:
        latency = time.time() - start_time
        print(f"CRITICAL SYSTEM ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
