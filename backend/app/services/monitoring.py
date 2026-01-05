import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MonitoringLayer:
    """Layer 12: Monitoring, Logging & Improvement"""
    
    def __init__(self):
        self.logger = logging.getLogger("ChatbotMonitoring")
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency": 0.0,
            "total_latency": 0.0
        }
    
    def log_request(self, session_id: str, endpoint: str, metadata: Optional[Dict] = None):
        """Log incoming request"""
        self.logger.info(f"[REQUEST] Session: {session_id} | Endpoint: {endpoint} | Metadata: {metadata}")
        self.metrics["total_requests"] += 1
    
    def log_response(self, session_id: str, latency: float, success: bool, error: Optional[str] = None):
        """Log response with latency tracking"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"[RESPONSE] Session: {session_id} | Status: {status} | Latency: {latency:.2f}s")
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            if error:
                self.logger.error(f"[ERROR] Session: {session_id} | Error: {error}")
        
        # Update latency metrics
        self.metrics["total_latency"] += latency
        self.metrics["average_latency"] = self.metrics["total_latency"] / self.metrics["total_requests"]
    
    def log_vision_metrics(self, session_id: str, confidence_scores: Dict[str, float]):
        """Log vision accuracy metrics"""
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        self.logger.info(f"[VISION] Session: {session_id} | Avg Confidence: {avg_confidence:.2f}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return current metrics"""
        return {
            **self.metrics,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
monitor = MonitoringLayer()
