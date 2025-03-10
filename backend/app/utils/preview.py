import io
import os
import fitz
from PIL import Image
from typing import Dict, List, Tuple
from sqlmodel import Session, select
from app.models import Document
from multiprocessing import Pool, cpu_count


class PreviewManager:
    def __init__(self):
        self.preview_cache: Dict[str, str] = {}
        self.DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
        self.PREVIEW_PATH = os.path.join(self.DOCUMENT_STORAGE_PATH, "previews")
        os.makedirs(self.PREVIEW_PATH, exist_ok=True)

    def _cache_existing_preview(self, document_id: str) -> str | None:
        """Check if preview exists and cache it"""
        preview_filename = f"{document_id}.webp"
        preview_path = os.path.join(self.PREVIEW_PATH, preview_filename)
        if os.path.exists(preview_path):
            self.preview_cache[document_id] = preview_path
            return preview_path
        return None

    def generate_preview(self, document_path: str, document_id: str, force: bool = False) -> str | None:
        """Generate a preview image for a document"""
        try:
            preview_filename = f"{document_id}.webp"
            preview_path = os.path.join(self.PREVIEW_PATH, preview_filename)

            # Return cached preview unless force is True
            if document_id in self.preview_cache and not force:
                return self.preview_cache[document_id]

            if document_path.lower().endswith(".pdf"):
                doc = fitz.open(document_path)
                if doc.page_count > 0:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    target_width = 500
                    aspect_ratio = img.height / img.width
                    target_height = int(target_width * aspect_ratio)
                    img = img.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )

                    img.save(preview_path, "WEBP", quality=20, method=6)
                    self.preview_cache[document_id] = preview_path
                    return preview_path
            return None
        except Exception as e:
            print(f"Preview generation error for {document_id}: {str(e)}")
            return None

    def _generate_preview_worker(self, args: Tuple[str, str]) -> Tuple[str, str | None]:
        """Worker function for parallel preview generation"""
        document_path, document_id = args
        preview_path = self.generate_preview(document_path, document_id)
        return document_id, preview_path

    async def generate_all_previews(self, session: Session):
        """Generate previews for all documents at startup using process pool"""
        try:
            documents = session.exec(select(Document)).all()
            preview_tasks: List[Tuple[str, str]] = []

            # check for existing previews
            for doc in documents:
                if not doc.path:
                    continue

                existing_preview = self._cache_existing_preview(str(doc.id))
                if existing_preview:
                    # print(f"Found existing preview for document {doc.id}")
                    continue

                preview_tasks.append((doc.path, str(doc.id)))

            if not preview_tasks:
                print("No new previews to generate")
                return

            num_processes = min(cpu_count(), len(preview_tasks))
            print(
                f"Generating {len(preview_tasks)} previews using {num_processes} processes"
            )

            with Pool(processes=num_processes) as pool:
                results = pool.map(self._generate_preview_worker, preview_tasks)

            for document_id, preview_path in results:
                if preview_path:
                    continue
                else:
                    print(f"Could not generate preview for document {document_id}")

        except Exception as e:
            print(f"Error generating previews: {str(e)}")
