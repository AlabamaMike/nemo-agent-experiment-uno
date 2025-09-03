"""
Voice Personality Mapper - Maps Brenda's sass levels to voice characteristics
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Brenda's emotional states for voice modulation"""
    PATIENT = "patient"
    NEUTRAL = "neutral"
    ANNOYED = "annoyed"
    FRUSTRATED = "frustrated"
    EXASPERATED = "exasperated"
    SARCASTIC = "sarcastic"
    URGENT = "urgent"
    CRISIS = "crisis"


@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    speed: float
    pitch: float
    pitch_variance: float
    volume: float
    emphasis: float
    pause_duration: float
    interruption_tolerance: float
    sarcasm_level: float
    formality: float
    patience_level: float


class VoicePersonalityMapper:
    """
    Maps Brenda's personality traits and sass levels to voice parameters
    
    Creates dynamic voice profiles based on:
    - Sass level (1-11)
    - Project health
    - Conversation context
    - Speaker behavior
    """
    
    def __init__(self):
        """Initialize voice personality mapper"""
        self.base_profile = VoiceProfile(
            speed=1.0,
            pitch=1.0,
            pitch_variance=0.1,
            volume=1.0,
            emphasis=0.5,
            pause_duration=0.5,
            interruption_tolerance=0.5,
            sarcasm_level=0.0,
            formality=0.7,
            patience_level=0.7
        )
        
        self.sass_profiles = self._initialize_sass_profiles()
        self.context_modifiers = self._initialize_context_modifiers()
        self.phrase_emphasis = self._initialize_phrase_emphasis()
        
        logger.info("VoicePersonalityMapper initialized with %d sass profiles", 
                   len(self.sass_profiles))
    
    def _initialize_sass_profiles(self) -> Dict[int, VoiceProfile]:
        """Initialize voice profiles for each sass level"""
        return {
            1: VoiceProfile(
                speed=0.95, pitch=0.98, pitch_variance=0.05,
                volume=0.95, emphasis=0.3, pause_duration=0.6,
                interruption_tolerance=0.8, sarcasm_level=0.0,
                formality=0.9, patience_level=0.9
            ),
            2: VoiceProfile(
                speed=0.97, pitch=0.99, pitch_variance=0.07,
                volume=0.97, emphasis=0.35, pause_duration=0.55,
                interruption_tolerance=0.75, sarcasm_level=0.1,
                formality=0.85, patience_level=0.85
            ),
            3: VoiceProfile(
                speed=1.0, pitch=1.0, pitch_variance=0.1,
                volume=1.0, emphasis=0.4, pause_duration=0.5,
                interruption_tolerance=0.7, sarcasm_level=0.2,
                formality=0.8, patience_level=0.8
            ),
            4: VoiceProfile(
                speed=1.02, pitch=1.01, pitch_variance=0.12,
                volume=1.02, emphasis=0.45, pause_duration=0.48,
                interruption_tolerance=0.65, sarcasm_level=0.3,
                formality=0.75, patience_level=0.75
            ),
            5: VoiceProfile(
                speed=1.05, pitch=1.02, pitch_variance=0.15,
                volume=1.05, emphasis=0.5, pause_duration=0.45,
                interruption_tolerance=0.6, sarcasm_level=0.4,
                formality=0.7, patience_level=0.7
            ),
            6: VoiceProfile(
                speed=1.08, pitch=1.03, pitch_variance=0.18,
                volume=1.08, emphasis=0.55, pause_duration=0.42,
                interruption_tolerance=0.55, sarcasm_level=0.5,
                formality=0.65, patience_level=0.65
            ),
            7: VoiceProfile(
                speed=1.12, pitch=1.04, pitch_variance=0.2,
                volume=1.1, emphasis=0.6, pause_duration=0.4,
                interruption_tolerance=0.5, sarcasm_level=0.6,
                formality=0.6, patience_level=0.6
            ),
            8: VoiceProfile(
                speed=1.15, pitch=1.05, pitch_variance=0.22,
                volume=1.12, emphasis=0.65, pause_duration=0.35,
                interruption_tolerance=0.4, sarcasm_level=0.7,
                formality=0.55, patience_level=0.5
            ),
            9: VoiceProfile(
                speed=1.2, pitch=1.07, pitch_variance=0.25,
                volume=1.15, emphasis=0.7, pause_duration=0.3,
                interruption_tolerance=0.3, sarcasm_level=0.8,
                formality=0.5, patience_level=0.4
            ),
            10: VoiceProfile(
                speed=1.25, pitch=1.09, pitch_variance=0.28,
                volume=1.18, emphasis=0.8, pause_duration=0.25,
                interruption_tolerance=0.2, sarcasm_level=0.9,
                formality=0.4, patience_level=0.3
            ),
            11: VoiceProfile(
                speed=1.3, pitch=1.12, pitch_variance=0.3,
                volume=1.2, emphasis=0.9, pause_duration=0.2,
                interruption_tolerance=0.1, sarcasm_level=1.0,
                formality=0.3, patience_level=0.1
            )
        }
    
    def _initialize_context_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Initialize context-based voice modifiers"""
        return {
            "escalation": {
                "speed": 1.1,
                "volume": 1.15,
                "emphasis": 1.2,
                "formality": 0.8,
                "patience_level": 0.5
            },
            "blocker_resolution": {
                "speed": 0.95,
                "emphasis": 1.1,
                "pause_duration": 1.2,
                "patience_level": 1.2
            },
            "status_update": {
                "speed": 1.05,
                "formality": 1.1,
                "sarcasm_level": 0.8
            },
            "repeated_failure": {
                "speed": 0.9,
                "pitch": 0.95,
                "volume": 1.1,
                "emphasis": 1.3,
                "sarcasm_level": 1.5,
                "patience_level": 0.3
            },
            "success": {
                "speed": 1.02,
                "pitch": 1.05,
                "pitch_variance": 1.2,
                "sarcasm_level": 0.7,
                "patience_level": 1.3
            },
            "crisis": {
                "speed": 1.2,
                "volume": 1.2,
                "emphasis": 1.4,
                "pause_duration": 0.5,
                "interruption_tolerance": 0.1,
                "formality": 0.5
            }
        }
    
    def _initialize_phrase_emphasis(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emphasis patterns for specific phrases"""
        return {
            "obviously": {
                "emphasis": 1.5,
                "pause_before": 0.3,
                "speed": 0.8
            },
            "really": {
                "emphasis": 1.4,
                "pitch": 1.1,
                "elongate": True
            },
            "seriously": {
                "emphasis": 1.6,
                "pause_before": 0.4,
                "pitch": 0.95
            },
            "fine": {
                "emphasis": 1.3,
                "speed": 0.7,
                "pitch": 0.9
            },
            "whatever": {
                "emphasis": 0.6,
                "speed": 1.2,
                "pitch": 0.95
            },
            "typical": {
                "emphasis": 1.4,
                "pause_before": 0.2,
                "sarcasm": 1.5
            },
            "great": {
                "emphasis": 1.5,
                "pitch": 1.1,
                "sarcasm": 1.8
            },
            "wonderful": {
                "emphasis": 1.6,
                "pitch": 1.15,
                "sarcasm": 2.0
            },
            "perfect": {
                "emphasis": 1.4,
                "pitch": 1.1,
                "sarcasm": 1.7
            }
        }
    
    def get_voice_profile(self, sass_level: int, context: Optional[str] = None,
                         emotional_state: Optional[EmotionalState] = None) -> Dict[str, Any]:
        """
        Get voice profile for given parameters
        
        Args:
            sass_level: Current sass level (1-11)
            context: Conversation context
            emotional_state: Current emotional state
            
        Returns:
            Complete voice configuration
        """
        sass_level = max(1, min(11, sass_level))
        
        profile = self.sass_profiles[sass_level]
        
        if context and context in self.context_modifiers:
            profile = self._apply_modifiers(profile, self.context_modifiers[context])
        
        if emotional_state:
            profile = self._apply_emotional_state(profile, emotional_state)
        
        return self._profile_to_dict(profile)
    
    def _apply_modifiers(self, profile: VoiceProfile, 
                        modifiers: Dict[str, float]) -> VoiceProfile:
        """Apply context modifiers to voice profile"""
        modified = VoiceProfile(
            speed=profile.speed * modifiers.get('speed', 1.0),
            pitch=profile.pitch * modifiers.get('pitch', 1.0),
            pitch_variance=profile.pitch_variance * modifiers.get('pitch_variance', 1.0),
            volume=profile.volume * modifiers.get('volume', 1.0),
            emphasis=profile.emphasis * modifiers.get('emphasis', 1.0),
            pause_duration=profile.pause_duration * modifiers.get('pause_duration', 1.0),
            interruption_tolerance=profile.interruption_tolerance * modifiers.get('interruption_tolerance', 1.0),
            sarcasm_level=min(1.0, profile.sarcasm_level * modifiers.get('sarcasm_level', 1.0)),
            formality=profile.formality * modifiers.get('formality', 1.0),
            patience_level=profile.patience_level * modifiers.get('patience_level', 1.0)
        )
        
        return self._clamp_profile(modified)
    
    def _apply_emotional_state(self, profile: VoiceProfile, 
                              state: EmotionalState) -> VoiceProfile:
        """Apply emotional state adjustments"""
        state_adjustments = {
            EmotionalState.PATIENT: {
                'speed': 0.95, 'pause_duration': 1.2, 'patience_level': 1.5
            },
            EmotionalState.ANNOYED: {
                'speed': 1.05, 'pitch': 1.02, 'sarcasm_level': 1.3
            },
            EmotionalState.FRUSTRATED: {
                'speed': 1.1, 'volume': 1.1, 'emphasis': 1.2, 'patience_level': 0.5
            },
            EmotionalState.EXASPERATED: {
                'speed': 0.9, 'pitch': 0.95, 'emphasis': 1.4, 'pause_duration': 1.3
            },
            EmotionalState.SARCASTIC: {
                'pitch_variance': 1.3, 'sarcasm_level': 1.5, 'emphasis': 1.2
            },
            EmotionalState.URGENT: {
                'speed': 1.2, 'volume': 1.15, 'pause_duration': 0.7
            },
            EmotionalState.CRISIS: {
                'speed': 1.3, 'volume': 1.2, 'emphasis': 1.5, 'interruption_tolerance': 0.1
            }
        }
        
        adjustments = state_adjustments.get(state, {})
        return self._apply_modifiers(profile, adjustments)
    
    def _clamp_profile(self, profile: VoiceProfile) -> VoiceProfile:
        """Clamp profile values to valid ranges"""
        return VoiceProfile(
            speed=max(0.5, min(2.0, profile.speed)),
            pitch=max(0.5, min(2.0, profile.pitch)),
            pitch_variance=max(0.0, min(0.5, profile.pitch_variance)),
            volume=max(0.5, min(1.5, profile.volume)),
            emphasis=max(0.0, min(1.0, profile.emphasis)),
            pause_duration=max(0.1, min(2.0, profile.pause_duration)),
            interruption_tolerance=max(0.0, min(1.0, profile.interruption_tolerance)),
            sarcasm_level=max(0.0, min(1.0, profile.sarcasm_level)),
            formality=max(0.0, min(1.0, profile.formality)),
            patience_level=max(0.0, min(1.0, profile.patience_level))
        )
    
    def _profile_to_dict(self, profile: VoiceProfile) -> Dict[str, Any]:
        """Convert voice profile to dictionary"""
        return {
            "speed": profile.speed,
            "pitch": profile.pitch,
            "pitch_variance": profile.pitch_variance,
            "volume": profile.volume,
            "emphasis": profile.emphasis,
            "pause_duration": profile.pause_duration,
            "interruption_tolerance": profile.interruption_tolerance,
            "sarcasm_level": profile.sarcasm_level,
            "formality": profile.formality,
            "patience_level": profile.patience_level
        }
    
    def get_phrase_emphasis(self, text: str) -> List[Dict[str, Any]]:
        """
        Get emphasis instructions for specific phrases
        
        Args:
            text: Text to analyze
            
        Returns:
            List of emphasis instructions
        """
        emphasis_instructions = []
        
        for phrase, emphasis_config in self.phrase_emphasis.items():
            if phrase.lower() in text.lower():
                emphasis_instructions.append({
                    "phrase": phrase,
                    "config": emphasis_config,
                    "position": text.lower().find(phrase.lower())
                })
        
        return sorted(emphasis_instructions, key=lambda x: x['position'])
    
    def get_emotional_state(self, sass_level: int, 
                           failure_count: int = 0,
                           escalation_count: int = 0) -> EmotionalState:
        """
        Determine emotional state from metrics
        
        Args:
            sass_level: Current sass level
            failure_count: Recent failure count
            escalation_count: Recent escalation count
            
        Returns:
            Appropriate emotional state
        """
        if escalation_count > 2:
            return EmotionalState.CRISIS
        elif failure_count > 5:
            return EmotionalState.EXASPERATED
        elif sass_level >= 9:
            return EmotionalState.SARCASTIC
        elif sass_level >= 7:
            return EmotionalState.FRUSTRATED
        elif sass_level >= 5:
            return EmotionalState.ANNOYED
        elif sass_level >= 3:
            return EmotionalState.NEUTRAL
        else:
            return EmotionalState.PATIENT
    
    def get_voice_directive(self, message: str, sass_level: int, 
                           context: str = None) -> Dict[str, Any]:
        """
        Get complete voice directive for a message
        
        Args:
            message: Message to speak
            sass_level: Current sass level
            context: Message context
            
        Returns:
            Complete voice directive with all parameters
        """
        profile = self.get_voice_profile(sass_level, context)
        emphasis_instructions = self.get_phrase_emphasis(message)
        
        message_segments = self._segment_message(message, emphasis_instructions)
        
        return {
            "base_profile": profile,
            "segments": message_segments,
            "emphasis_instructions": emphasis_instructions,
            "overall_emotion": self.get_emotional_state(sass_level).value,
            "allow_interruption": profile['interruption_tolerance'] > 0.3,
            "end_with_pause": context in ['escalation', 'blocker_resolution']
        }
    
    def _segment_message(self, message: str, 
                        emphasis_instructions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Segment message for varied delivery"""
        segments = []
        current_pos = 0
        
        for instruction in emphasis_instructions:
            phrase_pos = instruction['position']
            phrase = instruction['phrase']
            
            if phrase_pos > current_pos:
                segments.append({
                    "text": message[current_pos:phrase_pos],
                    "type": "normal"
                })
            
            segments.append({
                "text": phrase,
                "type": "emphasis",
                "config": instruction['config']
            })
            
            current_pos = phrase_pos + len(phrase)
        
        if current_pos < len(message):
            segments.append({
                "text": message[current_pos:],
                "type": "normal"
            })
        
        return segments