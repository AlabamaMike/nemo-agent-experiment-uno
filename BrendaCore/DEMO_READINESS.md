# BrendaCore Demo Readiness Assessment

## Current State: **PARTIALLY DEMO-READY**

### ✅ What We Have Working

#### Phase 1: Core Foundation (READY TO DEMO)
- **Brenda Console** - Interactive CLI that runs successfully
- **Sass Engine** - 11 sass levels with contextual quips
- **Memory Store** - Persistent interaction tracking
- **Agent Management** - Basic agent registration and broadcasting
- **Personality System** - Full sass personality with escalation triggers

#### Phase 2: Voice Integration (NEEDS SETUP)
- **Code Complete** - All voice components are implemented
- **No External Dependencies** - Cartesia SDK not yet available
- **Configuration Ready** - YAML config structure in place
- **Test Harness** - Simulation framework ready

### ⚠️ What's Missing for Demo

1. **Dependencies**
   - No base `requirements.txt` (only phase2 exists)
   - Cartesia SDK not yet available (noted as placeholder)
   - NeMo Agent Toolkit integration stubbed out

2. **Configuration**
   - Need `.env` file with API keys
   - Cartesia webhook URL needs to be configured
   - Phone number provisioning required for voice

3. **External Services**
   - Cartesia account and API key
   - Phone number for inbound calls
   - Webhook endpoint (ngrok for local demo)

## Demo Scenarios Available NOW

### 🎯 Scenario 1: Console Demo (READY)
**What it shows:** Brenda's personality and sass management
```bash
python3 brenda_console.py
```
**Demo flow:**
1. Show sass level adjustment (1-11)
2. Demonstrate contextual responses
3. Show agent management
4. Trigger escalation scenarios
5. Display memory persistence

### 🎯 Scenario 2: Voice Simulation (READY WITH SETUP)
**What it shows:** Voice personality mapping without actual calls
```bash
python3 tests/test_voice_integration.py
```
**Demo flow:**
1. Show voice parameter mapping
2. Demonstrate sass-to-voice conversion
3. Display emotional state detection
4. Show interruption tolerance levels

## Quick Setup for Demo

### Step 1: Install Dependencies
```bash
cd BrendaCore

# Create base requirements.txt
cat > requirements.txt << 'EOF'
# Core Python dependencies
pyyaml>=6.0
aiohttp>=3.8.0
asyncio>=3.4.3
aiofiles>=23.0.0
python-dotenv>=1.0.0
EOF

# Install all requirements
pip install -r requirements.txt
pip install -r requirements_phase2.txt
```

### Step 2: Create Environment File
```bash
cat > .env << 'EOF'
# Cartesia Configuration (for future use)
CARTESIA_API_KEY=demo-key-not-active
CARTESIA_WEBHOOK_SECRET=demo-secret
CARTESIA_PHONE_NUMBER=+1-555-BRENDA-1
CARTESIA_VOICE_ID=brittany
EOF
```

### Step 3: Run Console Demo
```bash
python3 brenda_console.py
```

## Demo Talk Track

### Opening (30 seconds)
"BrendaCore is a sassy AI project manager built on the NVIDIA NeMo Agent Toolkit. She manages distributed agents with personality that scales from helpful to hilariously hostile based on project health."

### Console Demo (2 minutes)
1. Start with sass level 5 (moderate)
2. Show task assignment with contextual sass
3. Escalate to level 8 (show personality change)
4. Trigger crisis mode (level 11)
5. Show agent coordination

### Voice Capability Overview (1 minute)
1. Explain Cartesia integration architecture
2. Show voice personality mapping code
3. Run test simulation
4. Explain authentication flow

### Architecture Discussion (1 minute)
1. Show modular design
2. Explain NeMo integration points
3. Discuss scalability approach
4. Preview next phases

## Key Differentiators to Highlight

1. **Personality-Driven Management** - Not just another bot
2. **Dynamic Sass Scaling** - Responds to project health
3. **Voice-First Design** - Ready for phone escalations
4. **Memory Persistence** - Learns from interactions
5. **Agent Orchestration** - Manages multiple AI agents

## Demo Commands Cheat Sheet

```bash
# Console commands to showcase
help          # Show all commands
sass 8        # Set sass level
status        # Show project health
agents        # List registered agents
task "Fix the critical bug"  # Assign task
escalate      # Trigger human escalation
memory        # Show interaction history
crisis        # Enter crisis mode
quit          # Exit gracefully
```

## Backup Plan

If live demo fails:
1. Have screenshots ready
2. Pre-recorded terminal session (use `asciinema`)
3. Code walkthrough as fallback
4. Focus on architecture discussion

## Post-Demo Discussion Points

1. **Integration Timeline** - NeMo and Cartesia SDK availability
2. **Deployment Options** - Cloud, on-prem, hybrid
3. **Customization** - Industry-specific sass profiles
4. **Metrics** - Productivity improvements
5. **Next Phases** - GitHub, analytics, team expansion