from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(slots=True)
class RunContext:
    """
    Encapsulates all runtime parameters and configurations for a single pipeline execution.
    """
    document_id: str
    input_path: str
    debug_mode: bool = False
    config_flags: Dict[str, Any] = field(default_factory=dict)
    output_dir: Optional[str] = None
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_flag(self, key: str, default: Any = None) -> Any:
        return self.config_flags.get(key, default)
