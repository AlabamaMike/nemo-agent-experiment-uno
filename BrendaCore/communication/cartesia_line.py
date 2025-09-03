"""
CartesiaLineAgent - Voice interface for Brenda using Cartesia.AI
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import hashlib
import hmac

logger = logging.getLogger(__name__)


class CallState(Enum):
    """Voice call states"""
    IDLE = "idle"
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    IN_CALL = "in_call"
    ON_HOLD = "on_hold"
    TRANSFERRING = "transferring"
    ENDED = "ended"


class CartesiaLineAgent:
    """
    Cartesia.AI Line Agent integration for voice-enabled Brenda
    
    Handles:
    - Voice call management
    - Speaker authentication
    - Sass-enhanced voice responses
    - Outbound escalation calls
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Cartesia Line Agent"""
        self.config = config or self._get_default_config()
        
        self.api_key = self.config.get('api_key')
        self.webhook_secret = self.config.get('webhook_secret')
        
        self.line_config = {
            "agent_name": self.config.get('agent_name', 'Brenda-PM'),
            "phone_number": self.config.get('phone_number'),
            "voice_model": self.config.get('voice_model', 'sassy-professional-female'),
            "webhook_endpoint": self.config.get('webhook_endpoint', '/webhooks/cartesia'),
            "authentication": self.config.get('authentication', 'speaker_id_enabled'),
            "language": self.config.get('language', 'en-US')
        }
        
        self.voice_settings = {
            "base_speed": 1.0,
            "sass_multiplier": 0.05,
            "max_speed": 1.5,
            "min_speed": 0.8,
            "pitch_base": 1.0,
            "pitch_variance": 0.1,
            "interruption_enabled": True,
            "interruption_threshold": 0.5
        }
        
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.authenticated_speakers: Dict[str, str] = {}
        self.call_metrics = {
            "total_calls": 0,
            "successful_authentications": 0,
            "failed_authentications": 0,
            "escalations_delivered": 0,
            "average_call_duration": 0
        }
        
        logger.info("CartesiaLineAgent initialized with voice model: %s", 
                   self.line_config['voice_model'])
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default Cartesia configuration"""
        import os
        return {
            "api_key": os.getenv("CARTESIA_API_KEY"),
            "webhook_secret": os.getenv("CARTESIA_WEBHOOK_SECRET"),
            "agent_name": "Brenda-PM",
            "phone_number": os.getenv("CARTESIA_PHONE_NUMBER"),
            "voice_model": "sassy-professional-female",
            "webhook_endpoint": "/webhooks/cartesia",
            "authentication": "speaker_id_enabled",
            "language": "en-US"
        }
    
    def map_sass_to_voice(self, sass_level: int) -> Dict[str, float]:
        """
        Map sass level to voice parameters
        
        Args:
            sass_level: Current sass level (1-11)
            
        Returns:
            Voice parameter adjustments
        """
        sass_factor = sass_level / 11.0
        
        return {
            "speech_rate": min(
                self.voice_settings['base_speed'] + 
                (sass_level * self.voice_settings['sass_multiplier']),
                self.voice_settings['max_speed']
            ),
            "pitch_variance": self.voice_settings['pitch_variance'] * sass_factor,
            "interruption_threshold": max(
                self.voice_settings['interruption_threshold'] - 
                (sass_level * 0.05),
                0.1
            ),
            "emphasis_strength": 0.5 + (sass_factor * 0.5),
            "sarcasm_detection": sass_factor > 0.5,
            "pause_duration": max(0.5 - (sass_factor * 0.3), 0.2)
        }
    
    async def handle_incoming_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming voice call
        
        Args:
            call_data: Call information from Cartesia
            
        Returns:
            Response configuration
        """
        call_id = call_data.get('call_id')
        caller_id = call_data.get('caller_id', 'unknown')
        
        self.active_calls[call_id] = {
            "call_id": call_id,
            "caller_id": caller_id,
            "state": CallState.CONNECTING,
            "start_time": datetime.now(),
            "authenticated": False,
            "sass_level": 5,
            "interaction_count": 0
        }
        
        self.call_metrics['total_calls'] += 1
        
        logger.info("Incoming call from %s (ID: %s)", caller_id, call_id)
        
        greeting = await self._generate_greeting(caller_id)
        
        return {
            "action": "answer",
            "greeting": greeting,
            "voice_params": self.map_sass_to_voice(5),
            "authentication_required": self.line_config['authentication'] == 'speaker_id_enabled'
        }
    
    async def authenticate_speaker(self, call_id: str, voice_sample: bytes) -> bool:
        """
        Authenticate speaker using voice biometrics
        
        Args:
            call_id: Active call ID
            voice_sample: Voice sample for authentication
            
        Returns:
            Authentication success status
        """
        if call_id not in self.active_calls:
            return False
        
        voice_hash = hashlib.sha256(voice_sample).hexdigest()[:8]
        
        if voice_hash in self.authenticated_speakers:
            speaker_id = self.authenticated_speakers[voice_hash]
            self.active_calls[call_id]['authenticated'] = True
            self.active_calls[call_id]['speaker_id'] = speaker_id
            self.call_metrics['successful_authentications'] += 1
            
            logger.info("Speaker authenticated: %s", speaker_id)
            return True
        
        self.call_metrics['failed_authentications'] += 1
        logger.warning("Authentication failed for call %s", call_id)
        return False
    
    async def process_voice_input(self, call_id: str, transcript: str, 
                                 audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process voice input from caller
        
        Args:
            call_id: Active call ID
            transcript: Speech-to-text transcript
            audio_features: Audio analysis features
            
        Returns:
            Response configuration
        """
        if call_id not in self.active_calls:
            return {"error": "Invalid call ID"}
        
        call_info = self.active_calls[call_id]
        call_info['interaction_count'] += 1
        
        emotion = audio_features.get('emotion', 'neutral')
        interruption = audio_features.get('interruption', False)
        
        if emotion == 'frustrated' or call_info['interaction_count'] > 10:
            call_info['sass_level'] = min(call_info['sass_level'] + 1, 11)
        
        from ..core import BrendaAgent
        brenda = BrendaAgent()
        
        request = {
            "type": "voice_input",
            "sender": call_info.get('speaker_id', 'voice_caller'),
            "message": transcript,
            "emotion": emotion,
            "call_id": call_id
        }
        
        response = await brenda.process_request(request)
        
        voice_response = {
            "message": response.message,
            "voice_params": self.map_sass_to_voice(call_info['sass_level']),
            "action": "speak",
            "allow_interruption": interruption and call_info['sass_level'] < 8
        }
        
        if response.metadata.get('sass_quip'):
            voice_response['sass_quip'] = response.metadata['sass_quip']
            voice_response['voice_params']['emphasis_strength'] += 0.2
        
        return voice_response
    
    async def initiate_escalation_call(self, target_number: str, 
                                      escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate outbound call for escalation
        
        Args:
            target_number: Phone number to call
            escalation_data: Escalation details
            
        Returns:
            Call initiation response
        """
        call_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        escalation_reason = escalation_data.get('reason', 'unspecified')
        sass_level = escalation_data.get('sass_level', 8)
        
        self.active_calls[call_id] = {
            "call_id": call_id,
            "type": "outbound_escalation",
            "target": target_number,
            "state": CallState.CONNECTING,
            "start_time": datetime.now(),
            "escalation_data": escalation_data,
            "sass_level": sass_level
        }
        
        opening_message = self._generate_escalation_opening(escalation_data)
        
        logger.info("Initiating escalation call to %s for reason: %s", 
                   target_number, escalation_reason)
        
        return {
            "call_id": call_id,
            "action": "dial",
            "target": target_number,
            "opening_message": opening_message,
            "voice_params": self.map_sass_to_voice(sass_level),
            "max_ring_time": 30,
            "voicemail_message": self._generate_voicemail_message(escalation_data)
        }
    
    async def handle_webhook_event(self, event: Dict[str, Any], 
                                  signature: str) -> Dict[str, Any]:
        """
        Handle webhook events from Cartesia
        
        Args:
            event: Webhook event data
            signature: Webhook signature for verification
            
        Returns:
            Event response
        """
        if not self._verify_webhook_signature(event, signature):
            logger.warning("Invalid webhook signature")
            return {"error": "Invalid signature"}
        
        event_type = event.get('type')
        call_id = event.get('call_id')
        
        if event_type == 'call.started':
            return await self.handle_incoming_call(event.get('call_data', {}))
        
        elif event_type == 'call.ended':
            return await self._handle_call_ended(call_id)
        
        elif event_type == 'speech.recognized':
            return await self.process_voice_input(
                call_id,
                event.get('transcript', ''),
                event.get('audio_features', {})
            )
        
        elif event_type == 'authentication.required':
            return {
                "action": "request_authentication",
                "message": "I need to verify who I'm talking to. Say your name clearly."
            }
        
        elif event_type == 'dtmf.received':
            return await self._handle_dtmf(call_id, event.get('digits', ''))
        
        else:
            logger.info("Unhandled webhook event type: %s", event_type)
            return {"status": "acknowledged"}
    
    def _verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature for security"""
        if not self.webhook_secret:
            return True
        
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def _generate_greeting(self, caller_id: str) -> str:
        """Generate contextual greeting"""
        hour = datetime.now().hour
        
        if hour < 12:
            time_greeting = "morning"
        elif hour < 17:
            time_greeting = "afternoon"
        else:
            time_greeting = "evening"
        
        if caller_id in self.authenticated_speakers.values():
            return f"Good {time_greeting}. Back again? What's broken now?"
        else:
            return f"Good {time_greeting}. This is Brenda from The Loom. What crisis are we dealing with today?"
    
    def _generate_escalation_opening(self, escalation_data: Dict[str, Any]) -> str:
        """Generate opening message for escalation call"""
        reason = escalation_data.get('reason', 'unspecified')
        priority = escalation_data.get('priority', 5)
        
        if priority >= 8:
            return f"Stop what you're doing. We have a {reason} situation that needs immediate attention."
        elif priority >= 5:
            return f"Hi, it's Brenda. We need to talk about the {reason} issue. It's getting out of hand."
        else:
            return f"Hey, Brenda here. When you get a chance, we should discuss the {reason} situation."
    
    def _generate_voicemail_message(self, escalation_data: Dict[str, Any]) -> str:
        """Generate voicemail message for missed escalation"""
        reason = escalation_data.get('reason')
        return f"This is Brenda from The Loom. Call me back about the {reason} issue. It won't fix itself."
    
    async def _handle_call_ended(self, call_id: str) -> Dict[str, Any]:
        """Handle call termination"""
        if call_id not in self.active_calls:
            return {"error": "Unknown call ID"}
        
        call_info = self.active_calls[call_id]
        duration = (datetime.now() - call_info['start_time']).total_seconds()
        
        if call_info.get('type') == 'outbound_escalation':
            self.call_metrics['escalations_delivered'] += 1
        
        current_avg = self.call_metrics['average_call_duration']
        total_calls = self.call_metrics['total_calls']
        self.call_metrics['average_call_duration'] = (
            (current_avg * (total_calls - 1) + duration) / total_calls
        )
        
        call_info['state'] = CallState.ENDED
        call_info['end_time'] = datetime.now()
        call_info['duration'] = duration
        
        logger.info("Call ended: %s (Duration: %.2f seconds)", call_id, duration)
        
        del self.active_calls[call_id]
        
        return {
            "status": "call_ended",
            "duration": duration,
            "metrics_updated": True
        }
    
    async def _handle_dtmf(self, call_id: str, digits: str) -> Dict[str, Any]:
        """Handle DTMF (phone keypad) input"""
        if call_id not in self.active_calls:
            return {"error": "Invalid call ID"}
        
        if digits == "0":
            return {
                "action": "transfer",
                "target": "human_operator",
                "message": "Fine. Transferring you to someone with more patience."
            }
        elif digits == "1":
            return {
                "action": "speak",
                "message": "Option 1. How original. What else?"
            }
        else:
            return {
                "action": "speak",
                "message": f"You pressed {digits}. That doesn't do anything. Try again."
            }
    
    def get_call_metrics(self) -> Dict[str, Any]:
        """Get voice call metrics"""
        return {
            "metrics": self.call_metrics,
            "active_calls": len(self.active_calls),
            "authenticated_speakers": len(self.authenticated_speakers)
        }
    
    async def end_all_calls(self):
        """End all active calls (for shutdown)"""
        for call_id in list(self.active_calls.keys()):
            await self._handle_call_ended(call_id)
        
        logger.info("All active calls terminated")