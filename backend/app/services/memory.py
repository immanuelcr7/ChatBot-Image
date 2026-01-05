from typing import List, Dict, Any, Optional
import json

class MemoryLayer:
    """Layer 6: Advanced Memory & Context Persistence Layer"""
    
    def __init__(self):
        # session_id -> { history: [...], vision_context: {} }
        self._store: Dict[str, Dict[str, Any]] = {}
    
    def set_vision_context(self, session_id: str, vision_data: Dict[str, Any]):
        """Persist visual analysis for the entire conversation lifetime."""
        if session_id not in self._store:
            self._store[session_id] = {"history": [], "vision_context": {}}
        self._store[session_id]["vision_context"] = vision_data

    def get_vision_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the pinned visual state for a session."""
        if session_id in self._store:
            return self._store[session_id].get("vision_context")
        return None

    def add_interaction(self, session_id: str, user_query: str, system_response: str):
        """Update the dialogue memory."""
        if session_id not in self._store:
            self._store[session_id] = {"history": [], "vision_context": {}}
        
        self._store[session_id]["history"].append({
            "role": "user",
            "content": user_query
        })
        
        self._store[session_id]["history"].append({
            "role": "assistant",
            "content": system_response
        })
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Bundle full context (History + Vision) for the Reasoning Layer.
        """
        session_data = self._store.get(session_id, {"history": [], "vision_context": {}})
        return {
            "conversation_history": session_data["history"],
            "persistent_vision": session_data["vision_context"]
        }
