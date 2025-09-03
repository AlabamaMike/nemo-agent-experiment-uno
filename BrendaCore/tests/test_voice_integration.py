#!/usr/bin/env python3
"""
Voice Integration Test Harness for BrendaCore
Tests Cartesia.AI voice capabilities without actual phone calls
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from BrendaCore.core import BrendaAgent
from BrendaCore.communication import (
    CartesiaLineAgent,
    VoicePersonalityMapper,
    LineAgentHandler,
    WebhookHandler
)
from BrendaCore.config import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceTestHarness:
    """
    Test harness for voice interactions
    
    Simulates:
    - Incoming calls
    - Voice input processing
    - Sass level adjustments
    - Escalation scenarios
    - Authentication flows
    """
    
    def __init__(self):
        """Initialize test harness"""
        self.config_loader = ConfigLoader(environment='development')
        self.cartesia_config = self.config_loader.get_cartesia_config()
        
        self.brenda = BrendaAgent()
        self.cartesia = CartesiaLineAgent(self.cartesia_config)
        self.voice_mapper = VoicePersonalityMapper()
        self.line_handler = LineAgentHandler(self.brenda, self.cartesia)
        self.webhook_handler = WebhookHandler(self.cartesia)
        
        self.test_results: List[Dict[str, Any]] = []
        
        logger.info("Voice Test Harness initialized")
    
    async def run_all_tests(self):
        """Run all voice integration tests"""
        print("\n" + "="*60)
        print("BRENDA VOICE INTEGRATION TEST SUITE")
        print("="*60 + "\n")
        
        tests = [
            self.test_incoming_call,
            self.test_voice_personality_mapping,
            self.test_sass_escalation,
            self.test_authentication_flow,
            self.test_message_bridging,
            self.test_outbound_escalation,
            self.test_webhook_handling,
            self.test_emotion_detection,
            self.test_interruption_handling,
            self.test_context_preservation
        ]
        
        for test_func in tests:
            test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
            print(f"Running: {test_name}...")
            
            try:
                result = await test_func()
                self.test_results.append({
                    "test": test_name,
                    "passed": result['passed'],
                    "message": result.get('message', 'Success'),
                    "duration": result.get('duration', 0)
                })
                
                if result['passed']:
                    print(f"✓ {test_name} - PASSED")
                else:
                    print(f"✗ {test_name} - FAILED: {result.get('message')}")
                    
            except Exception as e:
                print(f"✗ {test_name} - ERROR: {e}")
                self.test_results.append({
                    "test": test_name,
                    "passed": False,
                    "message": str(e)
                })
            
            print("-" * 40)
        
        self._print_summary()
    
    async def test_incoming_call(self) -> Dict[str, Any]:
        """Test incoming call handling"""
        start_time = datetime.now()
        
        call_data = {
            "call_id": "TEST-001",
            "caller_id": "+1234567890",
            "called_id": self.cartesia_config.get('line_agent', {}).get('phone_number'),
            "direction": "inbound",
            "timestamp": datetime.now().isoformat()
        }
        
        response = await self.cartesia.handle_incoming_call(call_data)
        
        assert response.get('action') == 'answer', "Should answer the call"
        assert 'greeting' in response, "Should provide greeting"
        assert 'voice_params' in response, "Should include voice parameters"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_voice_personality_mapping(self) -> Dict[str, Any]:
        """Test voice personality mapping for different sass levels"""
        start_time = datetime.now()
        
        test_cases = [
            {"sass_level": 1, "expected_speed": 0.95},
            {"sass_level": 5, "expected_speed": 1.05},
            {"sass_level": 11, "expected_speed": 1.3}
        ]
        
        for test_case in test_cases:
            profile = self.voice_mapper.get_voice_profile(
                test_case['sass_level'],
                context='general'
            )
            
            assert abs(profile['speed'] - test_case['expected_speed']) < 0.01, \
                f"Speed mismatch for sass level {test_case['sass_level']}"
        
        emphasis_test = self.voice_mapper.get_phrase_emphasis("This is obviously a test")
        assert len(emphasis_test) > 0, "Should detect emphasis phrases"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_sass_escalation(self) -> Dict[str, Any]:
        """Test sass escalation through voice interactions"""
        start_time = datetime.now()
        
        call_id = "TEST-002"
        self.cartesia.active_calls[call_id] = {
            "call_id": call_id,
            "sass_level": 5,
            "interaction_count": 0
        }
        
        frustration_inputs = [
            {"transcript": "This isn't working", "emotion": "frustrated"},
            {"transcript": "I've tried everything", "emotion": "frustrated"},
            {"transcript": "This is ridiculous", "emotion": "angry"}
        ]
        
        initial_sass = self.cartesia.active_calls[call_id]['sass_level']
        
        for input_data in frustration_inputs:
            response = await self.cartesia.process_voice_input(
                call_id,
                input_data['transcript'],
                {"emotion": input_data['emotion']}
            )
        
        final_sass = self.cartesia.active_calls[call_id]['sass_level']
        
        assert final_sass > initial_sass, "Sass level should increase with frustration"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_authentication_flow(self) -> Dict[str, Any]:
        """Test speaker authentication flow"""
        start_time = datetime.now()
        
        call_id = "TEST-003"
        voice_sample = b"simulated_voice_sample_data"
        
        self.cartesia.active_calls[call_id] = {
            "call_id": call_id,
            "authenticated": False
        }
        
        auth_result = await self.cartesia.authenticate_speaker(call_id, voice_sample)
        
        assert isinstance(auth_result, bool), "Should return boolean result"
        
        webhook_event = {
            "type": "authentication.requested",
            "call_id": call_id
        }
        
        response = await self.webhook_handler._handle_authentication_requested(webhook_event)
        
        assert response.get('action') == 'request_voice_sample', \
            "Should request voice sample"
        assert 'timeout' in response, "Should include timeout"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_message_bridging(self) -> Dict[str, Any]:
        """Test message bridging between Brenda and Cartesia"""
        start_time = datetime.now()
        
        await self.line_handler.start()
        
        test_message = {
            "call_id": "TEST-004",
            "transcript": "I need help with the deployment",
            "audio_features": {
                "emotion": "neutral",
                "is_final": True
            }
        }
        
        result = await self.line_handler.bridge_message(
            test_message,
            source="cartesia"
        )
        
        assert result['status'] == 'queued', "Message should be queued"
        assert 'message_id' in result, "Should return message ID"
        
        await asyncio.sleep(0.5)
        
        await self.line_handler.stop()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_outbound_escalation(self) -> Dict[str, Any]:
        """Test outbound escalation call initiation"""
        start_time = datetime.now()
        
        escalation_data = {
            "reason": "critical_path_delay",
            "sass_level": 9,
            "priority": 8,
            "context": "Multiple agent failures detected"
        }
        
        result = await self.cartesia.initiate_escalation_call(
            "+1234567890",
            escalation_data
        )
        
        assert 'call_id' in result, "Should return call ID"
        assert result['action'] == 'dial', "Should initiate dial action"
        assert 'opening_message' in result, "Should include opening message"
        assert 'voicemail_message' in result, "Should include voicemail message"
        
        voice_params = result.get('voice_params', {})
        assert voice_params.get('speech_rate', 0) > 1.1, \
            "Should have elevated speech rate for high sass"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_webhook_handling(self) -> Dict[str, Any]:
        """Test webhook event handling"""
        start_time = datetime.now()
        
        test_events = [
            {
                "type": "call.started",
                "call_id": "TEST-005",
                "from": "+1234567890",
                "to": "+0987654321"
            },
            {
                "type": "speech.recognized",
                "call_id": "TEST-005",
                "transcript": "Hello Brenda",
                "confidence": 0.95,
                "is_final": True
            },
            {
                "type": "call.ended",
                "call_id": "TEST-005",
                "duration": 120,
                "end_reason": "normal"
            }
        ]
        
        for event in test_events:
            handler = self.webhook_handler.event_handlers.get(event['type'])
            assert handler is not None, f"Should have handler for {event['type']}"
            
            response = await handler(event)
            assert 'status' in response or 'action' in response, \
                "Should return valid response"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_emotion_detection(self) -> Dict[str, Any]:
        """Test emotion-based voice adjustments"""
        start_time = datetime.now()
        
        emotions = ['neutral', 'frustrated', 'angry', 'confused']
        
        for emotion in emotions:
            emotional_state = self.voice_mapper.get_emotional_state(
                sass_level=5,
                failure_count=3 if emotion == 'frustrated' else 0
            )
            
            assert emotional_state is not None, f"Should determine state for {emotion}"
            
            profile = self.voice_mapper.get_voice_profile(
                sass_level=5,
                emotional_state=emotional_state
            )
            
            assert profile is not None, f"Should generate profile for {emotion}"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_interruption_handling(self) -> Dict[str, Any]:
        """Test interruption tolerance based on sass level"""
        start_time = datetime.now()
        
        test_cases = [
            {"sass_level": 1, "min_tolerance": 0.7},
            {"sass_level": 5, "min_tolerance": 0.4},
            {"sass_level": 11, "min_tolerance": 0.0}
        ]
        
        for test_case in test_cases:
            voice_params = self.cartesia.map_sass_to_voice(test_case['sass_level'])
            
            assert voice_params['interruption_threshold'] >= test_case['min_tolerance'], \
                f"Interruption tolerance out of range for sass {test_case['sass_level']}"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    async def test_context_preservation(self) -> Dict[str, Any]:
        """Test context preservation across voice interactions"""
        start_time = datetime.now()
        
        call_id = "TEST-006"
        context_id = f"voice_{call_id}"
        
        messages = [
            {"transcript": "I'm working on the authentication module"},
            {"transcript": "It keeps failing with a timeout error"},
            {"transcript": "I've tried increasing the timeout but no luck"}
        ]
        
        for msg in messages:
            await self.line_handler.bridge_message({
                "call_id": call_id,
                "transcript": msg['transcript'],
                "audio_features": {"is_final": True}
            }, source="cartesia")
        
        context = self.line_handler._get_conversation_context(context_id)
        
        assert context.get('message_count', 0) > 0, "Should track message count"
        assert 'last_updated' in context, "Should track last update time"
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "passed": True,
            "duration": duration
        }
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nSass Commentary:")
        if passed == total:
            print("💬 All tests passed. I'm almost impressed. Almost.")
        elif passed > total * 0.8:
            print("💬 Most tests passed. Could be worse, I suppose.")
        elif passed > total * 0.5:
            print("💬 Half passed. Perfectly balanced, as all things shouldn't be.")
        else:
            print("💬 More failures than successes. Typical.")
        
        print("="*60 + "\n")


async def main():
    """Main test runner"""
    harness = VoiceTestHarness()
    
    try:
        await harness.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted. How predictable.\n")
    except Exception as e:
        logger.error("Test harness error: %s", e)
        print(f"\nTest harness failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())