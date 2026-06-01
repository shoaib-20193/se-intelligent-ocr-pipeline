"""
src/pipeline/m6_export/exporters/json_exporter.py
Exports RenderableDocument to JSON.
"""
import json
import dataclasses
from pathlib import Path
from src.pipeline.m6_export.contracts import RenderableDocument

class JsonExporter:
    @staticmethod
    def export(document: RenderableDocument, output_path: str) -> str:
        """
        Exports the document to a JSON file.
        Returns the absolute path of the created file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        doc_dict = {
            "document_id": document.document_id,
            "metadata": document.metadata,
            "pages": []
        }
        
        for page in document.pages:
            page_dict = {
                "page_number": page.page_number,
                "width": page.width,
                "height": page.height,
                "num_columns": page.num_columns,
                "tokens": []
            }
            for token in page.tokens:
                token_dict = {
                    "token_id": token.token_id,
                    "text": token.text,
                    "block_type": token.block_type,
                    "bbox": {
                        "x": token.x,
                        "y": token.y,
                        "width": token.width,
                        "height": token.height
                    },
                    "reading_order": token.reading_order,
                    "column_id": token.column_id,
                    "spatial_metadata": token.spatial_metadata,
                    "source_region_id": token.source_region_ids[0] if token.source_region_ids else None,
                    "confidence": token.confidence
                }
                page_dict["tokens"].append(token_dict)
            doc_dict["pages"].append(page_dict)
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)
            
        return str(path.absolute())
