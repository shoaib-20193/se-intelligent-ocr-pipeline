class PipelineOrchestratorError(Exception):
    """Base exception for all M7 orchestrator errors."""
    pass

class FatalPipelineError(PipelineOrchestratorError):
    """
    An unrecoverable error that requires halting the entire document processing.
    Examples: Corrupted input file, missing output DTOs, illegal stage transitions.
    """
    pass

class RecoverablePipelineError(PipelineOrchestratorError):
    """
    An error that can be recovered from, allowing the pipeline to continue.
    Examples: A single OCR crop failing, a debug overlay failing to write.
    """
    pass

class ContractViolationError(FatalPipelineError):
    """Raised when an M-stage outputs an invalid or missing DTO."""
    pass

class InvalidStateTransitionError(FatalPipelineError):
    """Raised when an illegal pipeline state transition is attempted."""
    pass
