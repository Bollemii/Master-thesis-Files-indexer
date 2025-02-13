import os
import fitz


DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
PREVIEW_PATH = os.path.join(DOCUMENT_STORAGE_PATH, "previews")
os.makedirs(PREVIEW_PATH, exist_ok=True)

def generate_preview(document_path: str, document_id: str) -> str | None:
    """Generate a preview image for the first page of a PDF document"""
    try:
        preview_filename = f"{document_id}.png"
        preview_path = os.path.join(PREVIEW_PATH, preview_filename)
        
        # Return existing preview if already generated
        if os.path.exists(preview_path):
            return preview_path
            
        # Only handle PDFs for now
        if not document_path.lower().endswith('.pdf'):
            return None
            
        doc = fitz.open(document_path)
        if doc.page_count > 0:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            pix.save(preview_path)
            return preview_path
        return None
    except Exception as e:
        print(f"Preview generation error: {str(e)}")
        return None