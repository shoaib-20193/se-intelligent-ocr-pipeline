# gui/controllers/config_controller.py
# Reads and writes YAML configuration files
# See agents.md §MODULE_CONTRACTS → M8 Tab 2
#
# Responsibilities:
#   - Read current YAML values -> populate Tab 2 form fields
#   - Write Tab 2 form values -> YAML config files on "Apply"
#   - Trigger profile_loader.load_profile() after write
#
# Constraint: config editor writes to YAML files only — no in-memory config bypass
