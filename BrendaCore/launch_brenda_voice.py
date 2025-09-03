#!/usr/bin/env python3
"""
Launch Script for Voice-Enabled Brenda
Starts all Phase 2 components with Cartesia integration
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from aiohttp import web
import signal

sys.path.insert(0, str(Path(__file__).parent.parent))

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


class BrendaVoiceServer:
    """
    Main server for voice-enabled Brenda
    Integrates all Phase 2 components
    """
    
    def __init__(self):
        """Initialize voice server"""
        self.config_loader = ConfigLoader()
        self.cartesia_config = self.config_loader.get_cartesia_config()
        
        self.brenda = BrendaAgent()
        self.cartesia = CartesiaLineAgent(self.cartesia_config)
        self.voice_mapper = VoicePersonalityMapper()
        self.line_handler = LineAgentHandler(self.brenda, self.cartesia)
        self.webhook_handler = WebhookHandler(self.cartesia)
        
        self.app = self.webhook_handler.create_app()
        self.runner = None
        
        self._setup_signal_handlers()
        
        logger.info("BrendaVoiceServer initialized")
        print(self._get_startup_banner())
    
    def _get_startup_banner(self) -> str:
        """Get startup banner with sass"""
        return """
╔══════════════════════════════════════════════════════════════╗
║  BRENDA PM - VOICE ENABLED (Phase 2)                        ║
║  Cartesia.AI Integration Active                             ║
║  "Now I can sass you over the phone too"                    ║
╚══════════════════════════════════════════════════════════════╝
        """
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.shutdown()))
    
    async def start(self):
        """Start all server components"""
        try:
            await self.line_handler.start()
            logger.info("Line handler started")
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            port = int(os.getenv('WEBHOOK_PORT', 8080))
            site = web.TCPSite(self.runner, '0.0.0.0', port)
            await site.start()
            
            logger.info("Webhook server started on port %d", port)
            print(f"\n✓ Voice server running on http://0.0.0.0:{port}")
            print(f"✓ Webhook endpoint: http://0.0.0.0:{port}/webhooks/cartesia")
            print(f"✓ Health check: http://0.0.0.0:{port}/webhooks/health")
            print(f"✓ Metrics: http://0.0.0.0:{port}/webhooks/metrics")
            
            phone_number = self.cartesia_config.get('line_agent', {}).get('phone_number')
            if phone_number:
                print(f"✓ Voice line active: {phone_number}")
            
            print("\n💬 Brenda says: \"Call me. Or don't. I'll be here either way.\"\n")
            print("Press Ctrl+C to shutdown...")
            
            while True:
                await asyncio.sleep(60)
                await self._periodic_health_check()
                
        except Exception as e:
            logger.error("Server error: %s", e)
            await self.shutdown()
    
    async def _periodic_health_check(self):
        """Perform periodic health check"""
        active_calls = len(self.cartesia.active_calls)
        queue_size = self.line_handler.message_queue.qsize()
        
        if active_calls > 0:
            logger.info("Active calls: %d, Message queue: %d", active_calls, queue_size)
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating shutdown...")
        
        print("\n💬 Brenda says: \"Fine. I'm going. Don't call me when everything breaks.\"\n")
        
        await self.cartesia.end_all_calls()
        
        await self.line_handler.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        self.brenda.memory_store.save_memory()
        
        logger.info("Shutdown complete")
        sys.exit(0)
    
    def print_status(self):
        """Print current server status"""
        print("\n" + "="*60)
        print("BRENDA VOICE SERVER STATUS")
        print("="*60)
        
        print(f"Active Calls: {len(self.cartesia.active_calls)}")
        print(f"Message Queue: {self.line_handler.message_queue.qsize()}")
        print(f"Authenticated Speakers: {len(self.cartesia.authenticated_speakers)}")
        
        metrics = self.cartesia.get_call_metrics()
        print(f"\nCall Metrics:")
        for key, value in metrics['metrics'].items():
            print(f"  {key}: {value}")
        
        line_metrics = self.line_handler.get_metrics()
        print(f"\nMessage Bridge Metrics:")
        for key, value in line_metrics['metrics'].items():
            print(f"  {key}: {value}")
        
        print("="*60 + "\n")


async def main():
    """Main entry point"""
    server = BrendaVoiceServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Fatal error: %s", e)
    finally:
        await server.shutdown()


if __name__ == "__main__":
    print("""
    Starting Brenda Voice Server...
    
    Environment Variables Required:
    - CARTESIA_API_KEY: Your Cartesia API key
    - CARTESIA_WEBHOOK_SECRET: Webhook signing secret
    - CARTESIA_PHONE_NUMBER: Assigned phone number
    
    Optional:
    - WEBHOOK_PORT: Port for webhook server (default: 8080)
    - BRENDA_ENV: Environment (development/staging/production)
    - DEBUG_MODE: Enable debug logging
    """)
    
    required_env_vars = ['CARTESIA_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("For testing, you can set dummy values:")
        for var in missing_vars:
            print(f"  export {var}=test_{var.lower()}")
        print()
    
    asyncio.run(main())