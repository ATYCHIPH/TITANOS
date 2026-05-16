from __future__ import annotations

from .brain import TitanosBrain
from .body import (
    CortexAdapter,
    CraftAdapter,
    EyesAdapter,
    HandsAdapter,
    LabAdapter,
    MemoryAdapter,
    VoiceAdapter,
)


from .sources import inject_source_paths


def create_titanos() -> TitanosBrain:
    inject_source_paths()
    
    # Initialize adapters
    memory = MemoryAdapter()
    craft = CraftAdapter()
    hands = HandsAdapter()
    eyes = EyesAdapter()
    voice = VoiceAdapter()
    lab = LabAdapter()
    
    # Initialize Cortex with access to other systems as tools
    cortex = CortexAdapter(tools=[memory, craft, hands, eyes, voice, lab])
    
    brain = TitanosBrain()
    brain.attach(memory)
    brain.attach(craft)
    brain.attach(hands)
    brain.attach(eyes)
    brain.attach(voice)
    brain.attach(lab)
    brain.attach(cortex)
    return brain

