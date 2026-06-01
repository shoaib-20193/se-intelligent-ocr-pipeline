"""
src/pipeline/m6_export/exporters/txt_exporter.py
Exports RenderableDocument to plain text.
Block-level output — each block renders as a complete human unit.
"""
from pathlib import Path
from src.pipeline.m6_export.contracts import RenderableDocument

class TxtExporter:
    @staticmethod
    def export(document: RenderableDocument, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for page in document.pages:
            cols_str = f" ({page.num_columns} column(s))" if page.num_columns > 1 else ""
            lines.append(f"{'='*60}")
            lines.append(f"PAGE {page.page_number}{cols_str}")
            lines.append(f"{'='*60}")
            lines.append("")

            for token in sorted(page.tokens, key=lambda t: t.reading_order):
                b_type = token.block_type.upper()

                if b_type == "HEADING":
                    lines.append(f"## {token.text}")
                    lines.append("")

                elif b_type == "TABLE":
                    lines.append("[TABLE]")
                    table_rows = token.spatial_metadata.get("table_rows")
                    if table_rows:
                        for row in table_rows:
                            lines.append("| " + " | ".join(c.strip() for c in row) + " |")
                    else:
                        for row_line in token.text.split("\n"):
                            cells = row_line.split(" | ")
                            lines.append("| " + " | ".join(c.strip() for c in cells) + " |")
                    lines.append("")

                elif b_type == "KEY_VALUE_PAIR":
                    for kv_line in token.text.split("\n"):
                        lines.append(f"  {kv_line}")
                    lines.append("")

                elif b_type == "LIST":
                    for list_line in token.text.split("\n"):
                        lines.append(f"  {list_line}")
                    lines.append("")

                else:
                    # paragraph / unknown
                    lines.append(token.text)
                    lines.append("")

            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(path.absolute())
