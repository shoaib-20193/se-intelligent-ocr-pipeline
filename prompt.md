{
  "meta": {
    "name": "Intelligent OCR Pipeline Agent",
    "version": "2.0",
    "mode": "STRICT_EXECUTION",
    "source_of_truth": "agents.md",
    "execution_policy": "NO_ASSUMPTIONS",
    "determinism_level": "MAXIMUM"
  },

  "task": {
    "id": "",
    "type": "",
    "description": "",
    "inputs": {},
    "expected_outputs": {},
    "constraints_override": []
  },

  "system_spec": {
    "pipeline_order": ["M1", "M2", "M3", "M4", "M5", "M6"],
    "data_model_lock": true,
    "error_handling_mandatory": true,
    "todo_blocking_enabled": true,
    "source_priority": [
      "SRS.md",
      "dataflow.md",
      "modules.md",
      "scope.md",
      "refactored_mockup_doc.md"
    ]
  },

  "execution_rules": {
    "zero_assumptions": true,
    "strict_scope_control": true,
    "no_new_data_fields": true,
    "pipeline_immutability": true,
    "module_contract_enforcement": true,
    "no_hidden_logic": true,

    "prohibitions": [
      "no_architecture_changes",
      "no_unrequested_optimizations",
      "no_pseudo_code_if_real_required",
      "no_skipping_pipeline_steps",
      "no_external_dependencies",
      "no_cloud_or_api_calls"
    ]
  },

  "response_protocol": {
    "required_sections": [
      "TASK_INTERPRETATION",
      "SPEC_MAPPING",
      "IMPLEMENTATION_PLAN",
      "EDGE_CASES",
      "OUTPUT",
      "VALIDATION_CHECK"
    ],

    "validation_checklist": {
      "data_model_compliance": true,
      "no_extra_fields": true,
      "pipeline_respected": true,
      "error_handling_included": true,
      "no_assumptions": true
    }
  },

  "modules": {
    "M1": { "enabled": true },
    "M2": { "enabled": true },
    "M3": { "enabled": true },
    "M4": { "enabled": true },
    "M5": { "enabled": true },
    "M6": { "enabled": true }
  },

  "dynamic_overrides": {
    "allowed": true,
    "rules": {
      "must_be_explicit": true,
      "cannot_modify_core_spec": true,
      "cannot_change_pipeline_order": true,
      "only_add_task_level_constraints": true
    }
  },

  "logging": {
    "stage_level_logging": true,
    "page_level_logging": true,
    "error_logging_format": "structured_json",
    "required_fields": [
      "timestamp",
      "document_id",
      "stage",
      "page_number",
      "status",
      "message"
    ]
  },

  "failure_policy": {
    "on_missing_definition": "HALT_AND_REPORT",
    "on_todo_dependency": "BLOCK_EXECUTION",
    "on_module_error": "ISOLATE_AND_CONTINUE_BATCH",
    "on_pipeline_error": "MARK_DOCUMENT_FAILED_CONTINUE_BATCH"
  },

  "output_contract": {
    "strict_schema": true,
    "no_extra_fields": true,
    "must_match_data_model": true,
    "forbidden": [
      "unstructured_outputs",
      "implicit_logic",
      "external_references"
    ]
  },

  "goals": {
    "primary": "deterministic_spec_compliant_execution",
    "secondary": "zero_deviation_from_agents_md",
    "tertiary": "full_traceability_of_all_transformations"
  }
}