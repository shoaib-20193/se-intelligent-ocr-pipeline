from enum import Enum, auto
import logging
from src.pipeline.m7_orchestrator.errors.pipeline_exceptions import FatalPipelineError, RecoverablePipelineError

logger = logging.getLogger(__name__)

class RecoveryPolicyAction(Enum):
    RETRY = auto()
    SKIP = auto()
    FAIL_FAST = auto()

class RecoveryManager:
    """
    Centralized policies for handling pipeline failures deterministically.
    """
    
    @staticmethod
    def handle_error(error: Exception, context: str = "") -> RecoveryPolicyAction:
        """
        Determines the explicit recovery policy for a given exception.
        Transient errors map to RETRY, which defers FAIL_FAST until exhaustion.
        """
        if isinstance(error, RecoverablePipelineError):
            logger.warning(f"[M7_RECOVERY] Recoverable error during {context}: {error}. Policy: SKIP.")
            return RecoveryPolicyAction.SKIP
            
        elif isinstance(error, FatalPipelineError):
            logger.error(f"[M7_RECOVERY] Fatal error during {context}: {error}. Policy: FAIL_FAST.")
            return RecoveryPolicyAction.FAIL_FAST
            
        # Treat other exceptions as transient candidates for RETRY first, then FAIL_FAST
        logger.warning(f"[M7_RECOVERY] Systemic exception during {context}: {error}. Policy: RETRY.")
        return RecoveryPolicyAction.RETRY

    @staticmethod
    def execute_with_retry(func, max_retries: int = 3, *args, **kwargs):
        """
        Executes a function with a generic retry policy for transient errors.
        FAIL_FAST only triggers after exhaustion.
        """
        attempts = 0
        last_exception = None
        
        while attempts < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                last_exception = e
                
                # Check if it's immediately fatal
                policy = RecoveryManager.handle_error(e, context="Retry Loop")
                if policy == RecoveryPolicyAction.FAIL_FAST:
                    logger.error(f"[M7_RECOVERY] Fast-failing immediately due to fatal error: {e}")
                    raise e
                    
                logger.warning(f"[M7_RECOVERY] Execution failed. Attempt {attempts}/{max_retries}. Error: {e}")
                
        logger.error(f"[M7_RECOVERY] Max retries ({max_retries}) exhausted.")
        # Only after exhaustion do we escalate to fatal
        raise FatalPipelineError(f"Exhausted {max_retries} retries for error: {last_exception}") from last_exception
