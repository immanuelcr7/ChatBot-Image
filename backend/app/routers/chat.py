from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import time
import json

from ..services.validation import RequestValidationLayer
from ..services.vision import ImagePreProcessingLayer, VisionProcessingLayer
from ..services.memory import MemoryLayer
from ..services.llm import VisionLanguageFusionLayer, ConversationalReasoningLayer, LocalResponseLayer
from ..services.monitoring import monitor

router = APIRouter()

# Core Contextual Infrastructure
validator = RequestValidationLayer()
image_processor = ImagePreProcessingLayer()
vision_engine = VisionProcessingLayer() 
memory = MemoryLayer()
fusion = VisionLanguageFusionLayer()
reasoner = ConversationalReasoningLayer()
local_replier = LocalResponseLayer()


@router.post("/chat")
async def chat_endpoint(
    image: Optional[UploadFile] = File(None),
    query: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """
    Hybrid Response Gateway with Graceful Degradation.
    Prioritizes Gemini Reasoning, falls back to Local Vision Response on failure.
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
            prompt_data = fusion.construct_prompt(persistent_vision, history, clean_query)
            raw_response = await reasoner.generate_response(prompt_data)
            
            # Reset initial state message if needed
            if raw_response == "initial_state":
                raw_response = "I'm ready to help! Please upload an image, and we can explore it together."
                
        except (ConnectionError, Exception) as e:
            # --- FAILSUB: GRACEFUL DEGRADATION TO LOCAL MODE ---
            print(f"API Failure Detected: {str(e)}. Switching to Local Response Mode.")
            api_failed = True
            
            # Generate response from local vision data directly
            raw_response = local_replier.generate_local_reply(clean_query, persistent_vision)
            
            # Add a single non-repeating notification if it's the first time in this turn
            if not any("Advanced reasoning is temporarily unavailable" in turn["content"] for turn in history[-2:]):
                raw_response = "*(Notice: Advanced reasoning is temporarily unavailable. Using local context.)* " + raw_response

        # 4. Dialogue Memory Update
        memory.add_interaction(session_id, clean_query, raw_response)
        
        latency = time.time() - start_time
        return {
            "session_id": session_id,
            "response": {
                "text": raw_response,
                "has_list": any(x in raw_response for x in ["•", "-", "1."]),
                "mode": "local" if api_failed else "hybrid"
            },
            "visual_summary": "Active",
            "latency": round(latency, 2)
        }
        
    except Exception as e:
        latency = time.time() - start_time
        print(f"CRITICAL SYSTEM ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error.")
