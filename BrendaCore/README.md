# BrendaCore - Phase 1 Implementation

## Overview

BrendaCore is a sassy project manager agent built on the NVIDIA NeMo Agent Toolkit. This Phase 1 implementation provides the core foundation for Brenda's personality, agent management, and memory systems.

## Current Implementation Status

### ✅ Phase 1: Core Foundation (Completed)

#### Implemented Components:

1. **BrendaAgent Core Class** (`core/brenda_agent.py`)
   - Full NeMo Agent Toolkit integration
   - Agent registration and monitoring
   - Task assignment and tracking
   - Escalation system with priority levels
   - Blocker resolution attempts
   - Performance metrics tracking
   - Strike system for repeated failures

2. **SassEngine** (`core/sass_engine.py`)
   - Dynamic sass level (1-11, goes to 11!)
   - Context-aware quip selection
   - Quip rotation to avoid repetition
   - Agent-specific sass tracking
   - Multiple quip categories
   - Signature phrases
   - Crisis mode sass

3. **MemoryStore** (`core/memory_store.py`)
   - Persistent context management
   - Agent-specific memory and patterns
   - Project memory and trends
   - Pattern recognition for recurring issues
   - Short-term and working memory
   - Interaction history with context window
   - Save/load functionality

4. **Console Interface** (`brenda_console.py`)
   - Interactive testing console
   - Mock agent simulation
   - All core commands implemented
   - Real-time status monitoring
   - Sass level adjustment
   - Memory inspection

5. **Configuration** (`config/sass_quips.json`)
   - Extensive quip database
   - Category-based organization
   - Cartesia voice-ready quips
   - GitHub integration quips
   - Crisis mode quips

## Quick Start

### Installation

```bash
# Activate the virtual environment
cd /workspaces/nemo-agent-experiment-uno/AgentIQ
source .venv/bin/activate

# Run Brenda Console
cd BrendaCore
python brenda_console.py
```

### Console Commands

```
Core Commands:
- status              : Check all agent status
- assign <id> <task>  : Assign task to agent
- escalate <reason>   : Trigger escalation
- sass [level]        : Get sass or set level (1-11)
- metrics            : Show performance metrics
- memory [agent_id]  : Check memory stats
- blocker <id> <type>: Simulate blocker
- health <1-10>      : Set project health
- simulate [mode]    : Simulate agent activity
- save               : Save memory to disk
- exit/quit          : Exit console

Escalation Reasons:
- infinite_loop
- conflicting_instructions
- repeated_failures
- permission_issue
- ambiguous_requirements
- human_approval_required
- critical_path_delay
- swarm_coordination_issue
```

## Architecture

```
BrendaCore/
├── core/
│   ├── brenda_agent.py    # Main agent with NeMo integration
│   ├── sass_engine.py      # Sass generation and management
│   └── memory_store.py     # Persistent context management
├── config/
│   └── sass_quips.json     # Quip database
├── brenda_console.py       # Interactive console
└── README.md              # This file
```

## Key Features Implemented

### Agent Management
- ✅ In-memory agent registry
- ✅ Real-time status tracking
- ✅ Performance metrics per agent
- ✅ Three-strike failure policy
- ✅ Reliability scoring

### Sass System
- ✅ Dynamic sass level based on project health
- ✅ Context-aware quip selection
- ✅ No quip repetition within window
- ✅ Agent-specific sass history
- ✅ Crisis mode (sass level 11)

### Memory System
- ✅ Persistent storage
- ✅ Agent interaction history
- ✅ Pattern detection
- ✅ Recurring issue tracking
- ✅ Context recall

### Escalation System
- ✅ Multiple escalation reasons
- ✅ Priority calculation
- ✅ Context preservation
- ✅ Sass-enhanced messages

## Next Phases Implementation Plan

### Phase 2: Cartesia Integration (Weeks 3-4)
```python
# Key tasks:
1. Implement CartesiaLineAgent class
2. Set up webhook handlers for Cartesia events
3. Create message bridge between Line and BrendaCore
4. Configure voice personality parameters
5. Implement conversation context sharing
6. Test voice-based sass delivery
```

### Phase 3: Agent Management (Weeks 5-6)
```python
# Key tasks:
1. Implement A2A protocol for agent communication
2. Create real agent connectors (replace mocks)
3. Build blocker pattern recognition
4. Implement automated blocker resolution strategies
5. Create performance improvement system
6. Build Wall of Fame/Shame
```

### Phase 4: PM Tool Integration (Weeks 7-8)
```python
# Key tasks:
1. Implement GitHubAdapter class
2. Create JiraAdapter class
3. Build AzureDevOpsAdapter class
4. Implement sync conflict detection
5. Create project health scoring
6. Build bi-directional data sync
```

### Phase 5: Polish & Personality (Weeks 9-10)
```python
# Key tasks:
1. Advanced sass engine with ML
2. Factory dashboard UI
3. Cartesia voice fine-tuning
4. Multi-channel continuity
5. Performance optimization
6. Production deployment prep
```

## API Usage Examples

### Creating Brenda Instance
```python
from BrendaCore.core import BrendaAgent

# Initialize Brenda
brenda = BrendaAgent()

# Register an agent
brenda.register_agent("agent-001", {
    "type": "developer",
    "capabilities": ["python", "javascript"]
})

# Process a request
request = {
    "type": "status_update",
    "sender": "agent-001",
    "status": "completed"
}
response = await brenda.process_request(request)
print(response.message)
print(response.metadata['sass_quip'])
```

### Using SassEngine
```python
from BrendaCore.core import SassEngine

sass = SassEngine()
sass.set_sass_level(8)  # High sass

# Get contextual quip
quip = sass.get_contextual_quip("escalation")
print(quip)

# Get performance roast
roast = sass.get_performance_quip("agent-001", 0.4)
print(roast)
```

### Memory Operations
```python
from BrendaCore.core import MemoryStore

memory = MemoryStore()

# Add interaction
memory.add_interaction({
    "timestamp": datetime.now(),
    "sender": "agent-001",
    "type": "status_update",
    "request": {"status": "failed"},
    "sass_level": 8
})

# Get agent context
context = memory.get_agent_context("agent-001")
print(f"Reliability: {context['reliability']:.1%}")

# Check recurring issues
issues = memory.get_recurring_issues()
for issue, details in issues.items():
    print(f"{issue}: {details['count']} occurrences")
```

## Testing

Run the console for interactive testing:
```bash
python brenda_console.py
```

Example test sequence:
```
brenda> status
brenda> simulate chaos
brenda> status
brenda> sass 11
brenda> escalate repeated_failures Testing escalation
brenda> metrics
brenda> memory
```

## Configuration

### Sass Levels
- 1-3: Mild sass (concerned but professional)
- 4-6: Moderate sass (getting annoyed)
- 7-9: High sass (very sarcastic)
- 10: Maximum normal sass
- 11: Crisis mode (ALL CAPS, maximum spite)

### Project Health Mapping
- CRITICAL (1-2): Sass level 10-11
- POOR (3-4): Sass level 8-9
- CONCERNING (5-6): Sass level 6-7
- MODERATE (7-8): Sass level 4-5
- GOOD (9-10): Sass level 1-3

## Known Limitations (Phase 1)

1. **No Real Agent Communication**: Using mock agents only
2. **No PM Tool Integration**: GitHub/Jira/Azure adapters not implemented
3. **No Voice Interface**: Cartesia integration pending
4. **In-Memory Registry Only**: No distributed agent tracking
5. **Basic Blocker Resolution**: Simple logic, no ML
6. **No Dashboard UI**: Console interface only

## Development Notes

### For Cartesia Integration (Phase 2)
- Webhook endpoint needed at `/webhooks/cartesia`
- Voice model configuration in `communication/cartesia_line.py`
- Context bridge in `communication/line_agent_handler.py`
- Sass-to-voice parameter mapping ready in sass_engine

### For GitHub Integration (Phase 4)
- Use PyGithub or GitHub REST API
- Implement in `integrations/github_adapter.py`
- Handle rate limits (5000/hour authenticated)
- Subscribe to webhooks for real-time updates

### For Production Deployment
- Replace in-memory storage with Redis/PostgreSQL
- Implement proper authentication
- Add comprehensive logging
- Set up monitoring and alerts
- Configure horizontal scaling

## Contributing

When adding new features:
1. Maintain sass consistency - never reduce sass
2. Update quip database in `config/sass_quips.json`
3. Add memory tracking for new interaction types
4. Include sass metadata in all responses
5. Test with console before integration

## License

Part of The Loom - Autonomous Software Factory

---

*Remember: Brenda's sass is not a bug, it's the feature. When in doubt, add more sass.*