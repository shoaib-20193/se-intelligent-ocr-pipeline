"""
M5 — Text Refinement & Structural Reconstruction interface  [V0 STUB]
Assembles a StructuredDocument from fake recognized regions.
Real implementation: V5 (§ALGO-ARTIFACT, §ALGO-PARA, §ALGO-TABLE).
See agents.md §MODULE_CONTRACTS → M5
"""
from __future__ import annotations
from src.data_model.recognized import RecognizedDocument
from src.data_model.structured import StructuredDocument, Section, Table
from src.data_model.configs import PostProcessConfig


def reconstruct(document: RecognizedDocument, config: PostProcessConfig) -> StructuredDocument:
    """
    V0 STUB — Groups regions into sections and tables.
    Input:  RecognizedDocument, PostProcessConfig
    Output: StructuredDocument
    """
    title: str = ""
    sections: list[Section] = []
    tables: list[Table] = []
    all_text_parts: list[str] = []

    for page in document.pages:
        current_heading: str = ""
        content_parts: list[str] = []

        for region in page.regions:
            if region.type == "header":
                # Flush previous section
                if content_parts:
                    sections.append(Section(heading=current_heading, content=" ".join(content_parts)))
                    all_text_parts.extend(content_parts)
                    content_parts = []
                current_heading = region.text
                if not title:
                    title = region.text

            elif region.type == "paragraph":
                content_parts.append(region.text)

            elif region.type == "table":
                # Stub: split pipe-delimited text into a single-row table
                cells = [c.strip() for c in region.text.split("|") if c.strip()]
                tables.append(Table(rows=[cells]))

            elif region.type == "footer":
                # Footers: append to last section content, not a new section
                content_parts.append(region.text)

        # Flush last section for this page
        if content_parts:
            sections.append(Section(heading=current_heading, content=" ".join(content_parts)))
            all_text_parts.extend(content_parts)

    return StructuredDocument(
        metadata=document.metadata,
        title=title,
        sections=sections,
        tables=tables,
        raw_text=" ".join(all_text_parts),
    )
