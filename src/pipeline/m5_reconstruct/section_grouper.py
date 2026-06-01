# m5_reconstruct/section_grouper.py
# Groups regions into Section objects for M5
# See agents.md §MODULE_CONTRACTS → M5 step 10-12
#
# Rule: consecutive header + following paragraph(s) = one Section
#   section.heading = header region text
#   section.content = concatenated paragraph region texts
# If no preceding header: section.heading = ""
# StructuredDocument.title = text of first type="header" region (or "")
# StructuredDocument.raw_text = ordered concat of all section.content
