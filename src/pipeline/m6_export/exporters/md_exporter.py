"""
src/pipeline/m6_export/exporters/md_exporter.py
Exports RenderableDocument to Markdown.
Block-level output with proper table rendering and heading hierarchy.
"""
from pathlib import Path
from src.pipeline.m6_export.contracts import RenderableDocument

class MdExporter:
    @staticmethod
    def export(document: RenderableDocument, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for page in document.pages:
            for token in sorted(page.tokens, key=lambda t: t.reading_order):
                b_type = token.block_type.lower()

                if b_type == "heading":
                    lines.append(f"# {token.text}")
                    lines.append("")

                elif b_type == "table":
                    # Render as markdown table
                    table_rows = token.spatial_metadata.get("table_rows")
                    if table_rows and len(table_rows) > 0:
                        header_cells = table_rows[0]
                        lines.append("| " + " | ".join(c.strip() for c in header_cells) + " |")
                        lines.append("| " + " | ".join("---" for _ in header_cells) + " |")
                        for row in table_rows[1:]:
                            lines.append("| " + " | ".join(c.strip() for c in row) + " |")
                    else:
                        rows = token.text.split("\n")
                        if rows:
                            # Header row
                            header_cells = rows[0].split(" | ")
                            lines.append("| " + " | ".join(c.strip() for c in header_cells) + " |")
                            lines.append("| " + " | ".join("---" for _ in header_cells) + " |")
                            # Data rows
                            for row in rows[1:]:
                                cells = row.split(" | ")
                                lines.append("| " + " | ".join(c.strip() for c in cells) + " |")
                    lines.append("")

                elif b_type == "key_value_pair":
                    for kv_line in token.text.split("\n"):
                        if ":" in kv_line:
                            key, _, val = kv_line.partition(":")
                            lines.append(f"**{key.strip()}:** {val.strip()}")
                        else:
                            lines.append(kv_line)
                    lines.append("")

                elif b_type == "list":
                    for list_line in token.text.split("\n"):
                        clean = list_line.lstrip("•-*●○▪► ")
                        lines.append(f"- {clean}")
                    lines.append("")

                else:
                    # paragraph / unknown
                    lines.append(token.text)
                    lines.append("")

            lines.append("---")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(path.absolute())
