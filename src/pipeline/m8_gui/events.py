"""
src/pipeline/m8_gui/events.py
Core event bus and state management for decoupled M7 -> M8 communication.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

class BatchState(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class EventType(Enum):
    STAGE = "STAGE"
    PROGRESS = "PROGRESS"
    ERROR = "ERROR"
    COMPLETE = "COMPLETE"

@dataclass
class PipelineEvent:
    document_id: str
    event_type: EventType
    stage_name: str
    progress: float  # 0.0 to 1.0
    message: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CancellationToken:
    """
    Cooperative cancellation token checked between M7 stages.
    """
    def __init__(self):
        self.cancelled = False
        
    def cancel(self):
        self.cancelled = True
        
    def is_cancelled(self) -> bool:
        return self.cancelled

class PipelineEventBus(QObject):
    """
    Global event bus to decouple M7 execution from M8 UI updates.
    """
    event_emitted = pyqtSignal(PipelineEvent)
    
    def emit_event(self, event: PipelineEvent):
        self.event_emitted.emit(event)

# Global singleton for UI wiring
global_event_bus = PipelineEventBus()
