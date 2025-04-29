import io
import os
import pathlib
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Literal, Tuple
import fitz
from PIL import Image

from app.database.documents import get_all_documents

PreviewSize = Literal["thumbnail", "detail"]


class PreviewManager:
    def __init__(self):
        self.preview_cache: Dict[str, Dict[PreviewSize, str]] = {}
        self.DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
        self.PREVIEW_PATH = os.path.join(self.DOCUMENT_STORAGE_PATH, "previews")
        os.makedirs(self.PREVIEW_PATH, exist_ok=True)

        # Create subdirectories for different sizes
        self.THUMBNAIL_PATH = os.path.join(self.PREVIEW_PATH, "thumbnails")
        self.DETAIL_PATH = os.path.join(self.PREVIEW_PATH, "details")
        os.makedirs(self.THUMBNAIL_PATH, exist_ok=True)
        os.makedirs(self.DETAIL_PATH, exist_ok=True)

    def _cache_existing_preview(
        self, document_id: str
    ) -> Dict[PreviewSize, str | None]:
        """Check if previews exist and cache them"""
        result = {}

        # Check thumbnail
        thumbnail_filename = f"{document_id}.webp"
        thumbnail_path = os.path.join(self.THUMBNAIL_PATH, thumbnail_filename)
        if os.path.exists(thumbnail_path):
            if document_id not in self.preview_cache:
                self.preview_cache[document_id] = {}
            self.preview_cache[document_id]["thumbnail"] = thumbnail_path
            result["thumbnail"] = thumbnail_path
        else:
            result["thumbnail"] = None

        # Check detail preview
        detail_filename = f"{document_id}.webp"
        detail_path = os.path.join(self.DETAIL_PATH, detail_filename)
        if os.path.exists(detail_path):
            if document_id not in self.preview_cache:
                self.preview_cache[document_id] = {}
            self.preview_cache[document_id]["detail"] = detail_path
            result["detail"] = detail_path
        else:
            result["detail"] = None

        return result

    def generate_preview(
        self,
        document_path: str,
        document_id: str,
        size: PreviewSize = "thumbnail",
        force: bool = False,
    ) -> str | None:
        """Generate a preview image for a document"""
        if not os.path.exists(document_path) or not os.path.isfile(document_path):
            print(f"Document does not exist: {document_path}")
            return None
        if pathlib.Path(document_path).suffix != ".pdf":
            return None
        try:
            if document_id not in self.preview_cache:
                self.preview_cache[document_id] = {}

            # Return cached version if available and not forcing regeneration
            if size in self.preview_cache.get(document_id, {}) and not force:
                return self.preview_cache[document_id][size]

            # Define sizes based on preview type
            if size == "thumbnail":
                target_width = 300
                quality = 20
                preview_dir = self.THUMBNAIL_PATH
            else:  # detail
                target_width = 1200
                quality = 70
                preview_dir = self.DETAIL_PATH

            preview_filename = f"{document_id}.webp"
            preview_path = os.path.join(preview_dir, preview_filename)

            # Generate preview based on file type
            if document_path.lower().endswith(".pdf"):
                doc = fitz.open(document_path)
                if doc.page_count > 0:
                    page = doc[0]
                    # Higher resolution for detail view
                    scale = 4 if size == "detail" else 2
                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Calculate aspect ratio and resize
                    aspect_ratio = img.height / img.width
                    target_height = int(target_width * aspect_ratio)
                    img = img.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )

                    # Save with appropriate quality settings
                    img.save(preview_path, "WEBP", quality=quality, method=6)

                    # Cache the result
                    if document_id not in self.preview_cache:
                        self.preview_cache[document_id] = {}
                    self.preview_cache[document_id][size] = preview_path
                    return preview_path
            return None
        except Exception as e:
            print(f"Preview generation error for {document_id} ({size}): {str(e)}")
            return None

    def _generate_preview_worker(
        self, args: Tuple[str, str]
    ) -> Tuple[str, Dict[PreviewSize, str | None]]:
        """Worker function for parallel preview generation"""
        document_path, document_id = args

        # Generate both sizes
        thumbnail_path = self.generate_preview(document_path, document_id, "thumbnail")
        detail_path = self.generate_preview(document_path, document_id, "detail")

        return document_id, {"thumbnail": thumbnail_path, "detail": detail_path}

    async def generate_all_previews(self):
        """Generate previews for all documents at startup using process pool"""
        try:
            documents = get_all_documents()
            preview_tasks: List[Tuple[str, str]] = []

            # Check for existing previews
            for doc in documents:
                if not doc.path:
                    continue
                if pathlib.Path(doc.path).suffix != ".pdf":
                    continue

                existing_previews = self._cache_existing_preview(str(doc.id))

                # If both sizes exist, skip
                if existing_previews.get("thumbnail") and existing_previews.get(
                    "detail"
                ):
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

            for document_id, preview_paths in results:
                if not preview_paths["thumbnail"] or not preview_paths["detail"]:
                    print(f"Could not generate all previews for document {document_id}")

        except Exception as e:
            print(f"Error generating previews: {str(e)}")
