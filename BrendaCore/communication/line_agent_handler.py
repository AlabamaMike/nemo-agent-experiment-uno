"""
Line Agent Handler - Bidirectional message bridge between Brenda and Cartesia
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from collections import deque
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 7
    URGENT = 9
    CRITICAL = 10


class MessageType(Enum):
    """Message types for routing"""
    VOICE_INPUT = "voice_input"
    TEXT_INPUT = "text_input"
    ESCALATION = "escalation"
    STATUS_UPDATE = "status_update"
    COMMAND = "command"
    RESPONSE = "response"
    SYSTEM = "system"


class LineAgentHandler:
    """
    Manages bidirectional communication between Brenda and Cartesia
    
    Features:
    - Message queuing and prioritization
    - Context preservation across channels
    - Real-time synchronization
    - Conversation continuity
    """
    
    def __init__(self, brenda_agent, cartesia_agent, config: Optional[Dict[str, Any]] = None):
        """
        Initialize line agent handler
        
        Args:
            brenda_agent: BrendaAgent instance
            cartesia_agent: CartesiaLineAgent instance
            config: Optional configuration
        """
        self.brenda = brenda_agent
        self.cartesia = cartesia_agent
        self.config = config or self._get_default_config()
        
        self.message_queue = asyncio.PriorityQueue()
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self.active_conversations: Dict[str, str] = {}
        
        self.message_history = deque(maxlen=1000)
        self.voice_to_text_buffer: Dict[str, List[str]] = {}
        
        self.handlers: Dict[MessageType, Callable] = {
            MessageType.VOICE_INPUT: self._handle_voice_input,
            MessageType.TEXT_INPUT: self._handle_text_input,
            MessageType.ESCALATION: self._handle_escalation,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.COMMAND: self._handle_command,
            MessageType.RESPONSE: self._handle_response,
            MessageType.SYSTEM: self._handle_system
        }
        
        self.metrics = {
            "messages_processed": 0,
            "voice_messages": 0,
            "text_messages": 0,
            "escalations_bridged": 0,
            "context_switches": 0,
            "queue_overflows": 0
        }
        
        self.running = False
        self.processor_task = None
        
        logger.info("LineAgentHandler initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "max_queue_size": 100,
            "processing_interval": 0.1,
            "context_timeout": 300,
            "voice_buffer_timeout": 2.0,
            "priority_boost_for_voice": 2,
            "enable_context_merging": True
        }
    
    async def start(self):
        """Start the message processor"""
        if self.running:
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_messages())
        logger.info("LineAgentHandler started")
    
    async def stop(self):
        """Stop the message processor"""
        self.running = False
        
        if self.processor_task:
            await self.processor_task
        
        logger.info("LineAgentHandler stopped")
    
    async def bridge_message(self, message: Dict[str, Any], 
                            source: str = "unknown",
                            priority: MessagePriority = MessagePriority.NORMAL) -> Dict[str, Any]:
        """
        Bridge a message between Brenda and Cartesia
        
        Args:
            message: Message to bridge
            source: Message source (brenda/cartesia/external)
            priority: Message priority
            
        Returns:
            Processing result
        """
        try:
            message_type = self._determine_message_type(message)
            
            enriched_message = {
                "id": f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "type": message_type,
                "priority": priority,
                "content": message,
                "context_id": self._get_or_create_context_id(message)
            }
            
            if self.message_queue.qsize() >= self.config['max_queue_size']:
                self.metrics['queue_overflows'] += 1
                logger.warning("Message queue overflow, dropping lowest priority message")
                
                temp_queue = []
                while not self.message_queue.empty():
                    temp_queue.append(await self.message_queue.get())
                
                temp_queue.sort(key=lambda x: x[0])
                temp_queue.pop()
                
                for item in temp_queue:
                    await self.message_queue.put(item)
            
            await self.message_queue.put((
                -priority.value,
                enriched_message['timestamp'],
                enriched_message
            ))
            
            self.message_history.append(enriched_message)
            
            return {
                "status": "queued",
                "message_id": enriched_message['id'],
                "queue_size": self.message_queue.qsize()
            }
            
        except Exception as e:
            logger.error("Error bridging message: %s", e)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_messages(self):
        """Main message processing loop"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    _, _, message = await self.message_queue.get()
                    
                    await self._process_single_message(message)
                    self.metrics['messages_processed'] += 1
                
                await asyncio.sleep(self.config['processing_interval'])
                
            except Exception as e:
                logger.error("Error in message processor: %s", e)
    
    async def _process_single_message(self, message: Dict[str, Any]):
        """Process a single message"""
        message_type = message['type']
        
        if message_type in self.handlers:
            await self.handlers[message_type](message)
        else:
            logger.warning("Unknown message type: %s", message_type)
    
    async def _handle_voice_input(self, message: Dict[str, Any]):
        """Handle voice input message"""
        content = message['content']
        call_id = content.get('call_id')
        transcript = content.get('transcript', '')
        audio_features = content.get('audio_features', {})
        
        self.metrics['voice_messages'] += 1
        
        if call_id not in self.voice_to_text_buffer:
            self.voice_to_text_buffer[call_id] = []
        
        self.voice_to_text_buffer[call_id].append(transcript)
        
        if audio_features.get('is_final', False):
            full_transcript = ' '.join(self.voice_to_text_buffer[call_id])
            self.voice_to_text_buffer[call_id] = []
            
            brenda_request = {
                "type": "voice_input",
                "sender": f"voice_caller_{call_id}",
                "message": full_transcript,
                "emotion": audio_features.get('emotion', 'neutral'),
                "call_context": self._get_conversation_context(message['context_id'])
            }
            
            response = await self.brenda.process_request(brenda_request)
            
            voice_response = await self.cartesia.process_voice_input(
                call_id,
                full_transcript,
                audio_features
            )
            
            self._update_conversation_context(
                message['context_id'],
                {
                    "last_transcript": full_transcript,
                    "last_response": response.message,
                    "sass_level": response.metadata.get('sass_level', 5)
                }
            )
    
    async def _handle_text_input(self, message: Dict[str, Any]):
        """Handle text input message"""
        content = message['content']
        self.metrics['text_messages'] += 1
        
        response = await self.brenda.process_request(content)
        
        if response.metadata.get('requires_voice'):
            await self._initiate_voice_channel(response)
    
    async def _handle_escalation(self, message: Dict[str, Any]):
        """Handle escalation message"""
        content = message['content']
        escalation_data = content.get('escalation_data', {})
        target_number = content.get('target_number')
        
        self.metrics['escalations_bridged'] += 1
        
        if target_number:
            call_result = await self.cartesia.initiate_escalation_call(
                target_number,
                escalation_data
            )
            
            self._update_conversation_context(
                message['context_id'],
                {
                    "escalation_call_id": call_result.get('call_id'),
                    "escalation_reason": escalation_data.get('reason'),
                    "escalation_time": datetime.now().isoformat()
                }
            )
    
    async def _handle_status_update(self, message: Dict[str, Any]):
        """Handle status update message"""
        content = message['content']
        
        if content.get('source') == 'voice':
            call_id = content.get('call_id')
            if call_id in self.cartesia.active_calls:
                call_info = self.cartesia.active_calls[call_id]
                
                brenda_update = {
                    "type": "agent_status",
                    "sender": f"voice_agent_{call_id}",
                    "status": content.get('status'),
                    "metadata": {
                        "channel": "voice",
                        "authenticated": call_info.get('authenticated', False)
                    }
                }
                
                await self.brenda.process_request(brenda_update)
    
    async def _handle_command(self, message: Dict[str, Any]):
        """Handle command message"""
        content = message['content']
        command = content.get('command')
        
        if command == 'sync_context':
            await self._sync_contexts()
        elif command == 'clear_buffers':
            self.voice_to_text_buffer.clear()
        elif command == 'force_escalation':
            await self._force_escalation(content.get('reason'))
    
    async def _handle_response(self, message: Dict[str, Any]):
        """Handle response message"""
        pass
    
    async def _handle_system(self, message: Dict[str, Any]):
        """Handle system message"""
        content = message['content']
        
        if content.get('event') == 'shutdown':
            await self.stop()
        elif content.get('event') == 'reset':
            await self._reset_handler()
    
    def _determine_message_type(self, message: Dict[str, Any]) -> MessageType:
        """Determine message type from content"""
        if 'call_id' in message:
            return MessageType.VOICE_INPUT
        elif 'escalation' in message.get('type', ''):
            return MessageType.ESCALATION
        elif 'status' in message:
            return MessageType.STATUS_UPDATE
        elif 'command' in message:
            return MessageType.COMMAND
        elif 'response' in message.get('type', ''):
            return MessageType.RESPONSE
        else:
            return MessageType.TEXT_INPUT
    
    def _get_or_create_context_id(self, message: Dict[str, Any]) -> str:
        """Get or create context ID for conversation tracking"""
        if 'context_id' in message:
            return message['context_id']
        
        if 'call_id' in message:
            context_id = f"voice_{message['call_id']}"
        elif 'sender' in message:
            context_id = f"text_{message['sender']}"
        else:
            context_id = f"unknown_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if context_id not in self.conversation_contexts:
            self.conversation_contexts[context_id] = {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "message_count": 0,
                "channel": "voice" if "voice" in context_id else "text"
            }
        
        return context_id
    
    def _get_conversation_context(self, context_id: str) -> Dict[str, Any]:
        """Get conversation context"""
        return self.conversation_contexts.get(context_id, {})
    
    def _update_conversation_context(self, context_id: str, updates: Dict[str, Any]):
        """Update conversation context"""
        if context_id not in self.conversation_contexts:
            self.conversation_contexts[context_id] = {}
        
        self.conversation_contexts[context_id].update(updates)
        self.conversation_contexts[context_id]['last_updated'] = datetime.now().isoformat()
        self.conversation_contexts[context_id]['message_count'] = \
            self.conversation_contexts[context_id].get('message_count', 0) + 1
    
    async def _initiate_voice_channel(self, response):
        """Initiate voice channel for important messages"""
        if hasattr(response, 'data') and 'escalation_id' in response.data:
            escalation_data = {
                "reason": response.data.get('reason', 'urgent'),
                "sass_level": response.metadata.get('sass_level', 8),
                "message": response.message
            }
            
            await self.cartesia.initiate_escalation_call(
                response.data.get('target_number'),
                escalation_data
            )
    
    async def _sync_contexts(self):
        """Synchronize contexts between channels"""
        self.metrics['context_switches'] += 1
        
        for context_id, context in self.conversation_contexts.items():
            if 'voice' in context_id and 'text' in self.active_conversations.get(context_id, ''):
                merged_context = self._merge_contexts(
                    context,
                    self.conversation_contexts.get(
                        self.active_conversations[context_id], {}
                    )
                )
                
                self.conversation_contexts[context_id] = merged_context
    
    def _merge_contexts(self, primary: Dict[str, Any], 
                       secondary: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two conversation contexts"""
        merged = primary.copy()
        
        for key, value in secondary.items():
            if key not in merged:
                merged[key] = value
            elif key == 'message_count':
                merged[key] = primary[key] + value
            elif key == 'sass_level':
                merged[key] = max(primary.get(key, 0), value)
        
        return merged
    
    async def _force_escalation(self, reason: str):
        """Force an escalation"""
        from ..core.brenda_agent import EscalationReason
        
        escalation_reason = EscalationReason(reason) if reason else EscalationReason.HUMAN_APPROVAL_REQUIRED
        
        escalation_result = await self.brenda.escalate_to_human(
            escalation_reason,
            {"forced": True, "timestamp": datetime.now().isoformat()}
        )
        
        logger.info("Forced escalation: %s", escalation_result)
    
    async def _reset_handler(self):
        """Reset handler state"""
        self.conversation_contexts.clear()
        self.active_conversations.clear()
        self.voice_to_text_buffer.clear()
        
        while not self.message_queue.empty():
            await self.message_queue.get()
        
        logger.info("LineAgentHandler reset completed")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get handler metrics"""
        return {
            "metrics": self.metrics,
            "queue_size": self.message_queue.qsize(),
            "active_contexts": len(self.conversation_contexts),
            "buffered_calls": len(self.voice_to_text_buffer),
            "history_size": len(self.message_history)
        }
    
    def get_conversation_history(self, context_id: Optional[str] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if context_id:
            return [
                msg for msg in self.message_history
                if msg.get('context_id') == context_id
            ][-limit:]
        else:
            return list(self.message_history)[-limit:]