"""
Webhook Handler - Manages Cartesia webhook events and routing
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from aiohttp import web
import hashlib
import hmac

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles incoming webhooks from Cartesia.AI
    
    Manages:
    - Event routing
    - Signature verification
    - Response formatting
    - Error handling
    """
    
    def __init__(self, cartesia_agent, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            cartesia_agent: CartesiaLineAgent instance
            webhook_secret: Secret for webhook signature verification
        """
        self.cartesia_agent = cartesia_agent
        self.webhook_secret = webhook_secret
        
        self.event_handlers: Dict[str, Callable] = {
            "call.started": self._handle_call_started,
            "call.ended": self._handle_call_ended,
            "call.updated": self._handle_call_updated,
            "speech.started": self._handle_speech_started,
            "speech.ended": self._handle_speech_ended,
            "speech.recognized": self._handle_speech_recognized,
            "dtmf.received": self._handle_dtmf_received,
            "authentication.requested": self._handle_authentication_requested,
            "authentication.completed": self._handle_authentication_completed,
            "error.occurred": self._handle_error_occurred,
            "voicemail.left": self._handle_voicemail_left,
            "transfer.initiated": self._handle_transfer_initiated,
            "transfer.completed": self._handle_transfer_completed
        }
        
        self.event_metrics = {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "invalid_signatures": 0,
            "unknown_events": 0
        }
        
        logger.info("WebhookHandler initialized with %d event handlers", 
                   len(self.event_handlers))
    
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """
        Main webhook endpoint handler
        
        Args:
            request: Incoming HTTP request
            
        Returns:
            HTTP response
        """
        try:
            body = await request.text()
            signature = request.headers.get('X-Cartesia-Signature', '')
            
            if not self._verify_signature(body, signature):
                self.event_metrics['invalid_signatures'] += 1
                logger.warning("Invalid webhook signature from %s", request.remote)
                return web.json_response(
                    {"error": "Invalid signature"},
                    status=401
                )
            
            event_data = json.loads(body)
            event_type = event_data.get('type')
            
            self.event_metrics['total_events'] += 1
            
            logger.info("Received webhook event: %s", event_type)
            
            if event_type in self.event_handlers:
                response = await self.event_handlers[event_type](event_data)
                self.event_metrics['successful_events'] += 1
                
                return web.json_response(response)
            else:
                self.event_metrics['unknown_events'] += 1
                logger.warning("Unknown event type: %s", event_type)
                
                return web.json_response({
                    "status": "acknowledged",
                    "message": f"Unknown event type: {event_type}"
                })
                
        except json.JSONDecodeError as e:
            self.event_metrics['failed_events'] += 1
            logger.error("Invalid JSON in webhook: %s", e)
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400
            )
        except Exception as e:
            self.event_metrics['failed_events'] += 1
            logger.error("Webhook handler error: %s", e)
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )
    
    def _verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Request body
            signature: Provided signature
            
        Returns:
            Signature validity
        """
        if not self.webhook_secret:
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, f"sha256={expected_signature}")
    
    async def _handle_call_started(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call started event"""
        call_data = {
            "call_id": event.get("call_id"),
            "caller_id": event.get("from"),
            "called_id": event.get("to"),
            "direction": event.get("direction", "inbound"),
            "timestamp": event.get("timestamp")
        }
        
        response = await self.cartesia_agent.handle_incoming_call(call_data)
        
        return {
            "action": response.get("action", "answer"),
            "greeting": response.get("greeting"),
            "voice_params": response.get("voice_params"),
            "authentication": {
                "required": response.get("authentication_required", False),
                "method": "voice_biometric"
            }
        }
    
    async def _handle_call_ended(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call ended event"""
        call_id = event.get("call_id")
        duration = event.get("duration")
        end_reason = event.get("end_reason", "normal")
        
        await self.cartesia_agent._handle_call_ended(call_id)
        
        return {
            "status": "acknowledged",
            "call_id": call_id,
            "duration": duration,
            "end_reason": end_reason
        }
    
    async def _handle_call_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call status update"""
        call_id = event.get("call_id")
        status = event.get("status")
        
        if call_id in self.cartesia_agent.active_calls:
            self.cartesia_agent.active_calls[call_id]["status"] = status
        
        return {"status": "acknowledged"}
    
    async def _handle_speech_started(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle speech started event"""
        call_id = event.get("call_id")
        
        if call_id in self.cartesia_agent.active_calls:
            self.cartesia_agent.active_calls[call_id]["speaking"] = True
        
        return {"status": "acknowledged"}
    
    async def _handle_speech_ended(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle speech ended event"""
        call_id = event.get("call_id")
        
        if call_id in self.cartesia_agent.active_calls:
            self.cartesia_agent.active_calls[call_id]["speaking"] = False
        
        return {"status": "acknowledged"}
    
    async def _handle_speech_recognized(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle speech recognition event"""
        call_id = event.get("call_id")
        transcript = event.get("transcript", "")
        confidence = event.get("confidence", 0.0)
        is_final = event.get("is_final", False)
        
        audio_features = {
            "emotion": event.get("emotion", "neutral"),
            "sentiment": event.get("sentiment", 0.0),
            "energy": event.get("energy", 0.5),
            "interruption": event.get("interruption", False),
            "speech_rate": event.get("speech_rate", 1.0)
        }
        
        if not is_final:
            return {
                "status": "processing",
                "message": "Listening..."
            }
        
        response = await self.cartesia_agent.process_voice_input(
            call_id, transcript, audio_features
        )
        
        return {
            "action": response.get("action", "speak"),
            "message": response.get("message"),
            "voice_params": response.get("voice_params"),
            "allow_interruption": response.get("allow_interruption", True),
            "sass_quip": response.get("sass_quip")
        }
    
    async def _handle_dtmf_received(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DTMF (keypad) input"""
        call_id = event.get("call_id")
        digits = event.get("digits", "")
        
        dtmf_responses = {
            "0": {
                "action": "transfer",
                "target": "human",
                "message": "Fine. Transferring you to someone with more patience."
            },
            "1": {
                "action": "speak",
                "message": "Option 1 selected. Processing..."
            },
            "2": {
                "action": "speak",
                "message": "Option 2. Interesting choice."
            },
            "9": {
                "action": "speak",
                "message": "Emergency escalation initiated. This better be good."
            },
            "*": {
                "action": "speak",
                "message": "Main menu. What now?"
            },
            "#": {
                "action": "end_call",
                "message": "Ending call. Finally."
            }
        }
        
        response = dtmf_responses.get(digits, {
            "action": "speak",
            "message": f"You pressed {digits}. That doesn't do anything useful."
        })
        
        return response
    
    async def _handle_authentication_requested(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication request"""
        call_id = event.get("call_id")
        
        return {
            "action": "request_voice_sample",
            "message": "I need to verify who I'm talking to. State your name clearly.",
            "timeout": 10,
            "max_attempts": 3
        }
    
    async def _handle_authentication_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication completion"""
        call_id = event.get("call_id")
        success = event.get("success", False)
        speaker_id = event.get("speaker_id")
        
        if success:
            if call_id in self.cartesia_agent.active_calls:
                self.cartesia_agent.active_calls[call_id]["authenticated"] = True
                self.cartesia_agent.active_calls[call_id]["speaker_id"] = speaker_id
            
            return {
                "action": "speak",
                "message": f"Authentication successful. Welcome back, {speaker_id}. What's broken now?"
            }
        else:
            return {
                "action": "speak",
                "message": "Authentication failed. Try again or press 0 for a human."
            }
    
    async def _handle_error_occurred(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error event"""
        error_type = event.get("error_type")
        error_message = event.get("error_message")
        call_id = event.get("call_id")
        
        logger.error("Cartesia error for call %s: %s - %s", 
                    call_id, error_type, error_message)
        
        if error_type == "speech_recognition_failed":
            return {
                "action": "speak",
                "message": "I didn't catch that. Speak up."
            }
        elif error_type == "connection_lost":
            return {
                "action": "redial",
                "max_attempts": 2
            }
        else:
            return {
                "action": "speak",
                "message": "Technical difficulties. How surprising. Try again later."
            }
    
    async def _handle_voicemail_left(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voicemail event"""
        call_id = event.get("call_id")
        recording_url = event.get("recording_url")
        duration = event.get("duration")
        
        logger.info("Voicemail left for call %s (duration: %s seconds)", 
                   call_id, duration)
        
        return {
            "status": "acknowledged",
            "action": "process_voicemail",
            "recording_url": recording_url
        }
    
    async def _handle_transfer_initiated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer initiation"""
        call_id = event.get("call_id")
        target = event.get("target")
        
        return {
            "action": "speak",
            "message": f"Transferring you to {target}. Good luck with that.",
            "then": "transfer"
        }
    
    async def _handle_transfer_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer completion"""
        call_id = event.get("call_id")
        success = event.get("success")
        
        if success:
            return {"status": "transfer_successful"}
        else:
            return {
                "action": "speak",
                "message": "Transfer failed. You're stuck with me."
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get webhook metrics"""
        return {
            "metrics": self.event_metrics,
            "handlers": list(self.event_handlers.keys()),
            "signature_verification": self.webhook_secret is not None
        }
    
    def create_app(self) -> web.Application:
        """
        Create aiohttp application with webhook routes
        
        Returns:
            Configured web application
        """
        app = web.Application()
        app.router.add_post('/webhooks/cartesia', self.handle_webhook)
        app.router.add_get('/webhooks/health', self._health_check)
        app.router.add_get('/webhooks/metrics', self._get_metrics)
        
        return app
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_calls": len(self.cartesia_agent.active_calls)
        })
    
    async def _get_metrics(self, request: web.Request) -> web.Response:
        """Metrics endpoint"""
        return web.json_response(self.get_metrics())