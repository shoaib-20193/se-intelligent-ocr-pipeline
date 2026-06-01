import time
from typing import Dict, List, Any
from src.pipeline.m7_orchestrator.state.pipeline_state import PipelineState

class StateTracker:
    """
    Tracks the current state of the document pipeline, preventing illegal state jumps.
    """
    
    # Valid forward transitions
    _VALID_TRANSITIONS = {
        PipelineState.INITIALIZED: [PipelineState.LOADED, PipelineState.FAILED],
        PipelineState.LOADED: [PipelineState.PREPROCESSED, PipelineState.FAILED],
        PipelineState.PREPROCESSED: [PipelineState.LAYOUT_ANALYZED, PipelineState.FAILED],
        PipelineState.LAYOUT_ANALYZED: [PipelineState.OCR_COMPLETED, PipelineState.FAILED, PipelineState.PARTIAL_FAILURE],
        PipelineState.OCR_COMPLETED: [PipelineState.M5_SEMANTIC_RECONSTRUCTION, PipelineState.COMPLETED, PipelineState.PARTIAL_FAILURE, PipelineState.FAILED, PipelineState.M5_FAILURE],
        PipelineState.M5_SEMANTIC_RECONSTRUCTION: [PipelineState.COMPLETED, PipelineState.PARTIAL_FAILURE, PipelineState.FAILED],
        PipelineState.PARTIAL_FAILURE: [PipelineState.COMPLETED, PipelineState.FAILED],
        PipelineState.M5_FAILURE: [PipelineState.COMPLETED, PipelineState.PARTIAL_FAILURE, PipelineState.FAILED],
        PipelineState.COMPLETED: [],
        PipelineState.FAILED: []
    }

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.current_state = PipelineState.INITIALIZED
        self.stage_timestamps: Dict[PipelineState, float] = {self.current_state: time.time()}
        self.failure_causes: List[str] = []

    def transition_to(self, new_state: PipelineState, failure_cause: str = None):
        """
        Transitions the pipeline to a new state.
        Raises ValueError if the transition is illegal.
        """
        if new_state not in self._VALID_TRANSITIONS.get(self.current_state, []):
            raise ValueError(f"Illegal pipeline state transition from {self.current_state.name} to {new_state.name}")
            
        self.current_state = new_state
        self.stage_timestamps[new_state] = time.time()
        
        if failure_cause:
            self.failure_causes.append(failure_cause)

    def is_failed(self) -> bool:
        return self.current_state == PipelineState.FAILED

    def get_duration(self, start_state: PipelineState, end_state: PipelineState) -> float:
        """Returns duration between two states in seconds, or 0.0 if either state wasn't reached."""
        if start_state in self.stage_timestamps and end_state in self.stage_timestamps:
            return self.stage_timestamps[end_state] - self.stage_timestamps[start_state]
        return 0.0
