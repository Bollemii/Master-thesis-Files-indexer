import base64
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError, as_completed
from multiprocessing import cpu_count

import fitz
import pandas as pd
import pytesseract
import unidecode
from docx2txt import docx2txt
from PIL import Image


def process_single_file(config: dict) -> tuple[str, str | None, str | None, int, float]:
    """
    Reads and processes a single file based on the provided configuration.

    Args:
        config (dict): A dictionary containing:
            'file_path': Path to the document.
            'temporary_path': Path for temporary files.
            'doc_reader_path': Path to the document reader executable (if needed).
            'tesseract_path': Path to the tesseract executable.
            'image_resolution': Resolution for OCR image conversion.
            'n_char_min': Minimum characters to attempt vectorized text extraction.
            'debug': Debug flag.

    Returns:
        tuple: (file_path, content, error_message, n_pages, processing_time)
    """
    file_path = config["file_path"]
    start_time = time.time()
    reader_instance = Reader(
        temporary_path=config.get("temporary_path", "./tmp"),
        doc_reader_path=config.get("doc_reader_path"),
        tesseract_path=config.get("tesseract_path"),
        image_resolution=config.get("image_resolution", 500),
        n_char_min=config.get("n_char_min", 5),
        debug=config.get("debug", False),
    )

    content: str | None = None
    error_msg: str | None = None
    n_pages: int = 0

    try:
        n_pages = reader_instance.get_n_pages(file_path)
        content = reader_instance.read_one_file(file_path)
        if content is not None:
            content = unidecode.unidecode(content)

    except Exception as e:
        error_msg = f"Reader Error: {e}"
        print(f"Error processing {file_path}: {error_msg}")

    processing_time = time.time() - start_time
    return file_path, content, error_msg, n_pages, processing_time


class Reader:
    def __init__(
        self,
        cv_file_column="cv_file",
        cv_content_column="cv_content_base64",
        temporary_path="tmp",
        doc_reader_path="",
        tesseract_path="",
        image_resolution=500,
        n_char_min=5,
        debug=False,
    ):
        self.switcher = {
            ".txt": self.read_text,
            ".doc": self.read_doc,
            ".docx": self.read_docx,
            ".pdf": self.read_xps,
            ".png": self.read_image,
            ".xps": self.read_xps,
        }
        self.cv_file_column = cv_file_column
        self.temporary_path = temporary_path
        self.doc_reader_path = doc_reader_path
        self.tesseract_bin_path = tesseract_path
        self.image_resolution = image_resolution
        self.debug = debug
        self.n_char_min = n_char_min

        os.makedirs(self.temporary_path, exist_ok=True)

        if self.tesseract_bin_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_bin_path

    def get_n_pages(self, filepath):
        extension = pathlib.PurePosixPath(filepath).suffix.lower()
        if extension in (".txt", ".doc", ".docx"):
            return 0
        if extension == ".png":
            return 1
        try:
            doc = fitz.open(filepath)
            n_pages = doc.page_count
            doc.close()
            return n_pages
        except Exception as e:
            print(f"Warning: Could not get page count for {filepath}: {e}")
            return 0

    def pdf_to_image_to_text(self, fullpath):
        default_resolution = 96
        zoom_x = self.image_resolution / default_resolution
        zoom_y = zoom_x
        mat = fitz.Matrix(zoom_x, zoom_y)
        text = ""
        doc = None
        try:
            doc = fitz.open(fullpath)
            for page in doc:
                pix = page.get_pixmap(alpha=False, matrix=mat)
                image_path = os.path.join(
                    self.temporary_path,
                    f"{os.getpid()}_page_{page.number}_{os.path.basename(fullpath)}.png",
                )
                try:
                    pix.save(image_path)
                    text += self.read_image(image_path)
                finally:
                    if not self.debug and os.path.exists(image_path):
                        os.remove(image_path)
        except Exception as e:
            print(f"Error during OCR for {fullpath}: {e}")
        finally:
            if doc:
                doc.close()
        return text

    def read_text(self, file_path):
        content = ""
        try:
            with open(file_path, encoding="utf-8") as one_file:
                content = one_file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as one_file:
                    content = one_file.read()
            except Exception as e:
                raise OSError(
                    f"Not able to read text file:{file_path} in [utf-8,latin-1] coding. Error: {e}"
                ) from e
        except Exception as e:
            raise OSError(f"Error reading text file {file_path}: {e}") from e
        return content

    def read_doc(self, file_path):
        content = ""
        text_file_path = os.path.join(
            self.temporary_path, pathlib.PurePosixPath(file_path).stem + ".txt"
        )
        try:
            if not self.doc_reader_path or not os.path.exists(self.doc_reader_path):
                raise OSError(
                    f"doc_reader_path not configured or not found: {self.doc_reader_path}"
                )

            result = subprocess.run(
                [
                    self.doc_reader_path,
                    "--headless",
                    "--convert-to",
                    "txt:Text",
                    "--outdir",
                    self.temporary_path,
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            result.check_returncode()

            if not os.path.exists(text_file_path):
                raise OSError(
                    f"Converted text file not found: {text_file_path}. "
                    f"Converter output: {result.stdout} {result.stderr}"
                )

            content = self.read_text(text_file_path)
        except subprocess.TimeoutExpired:
            raise OSError(f"Timeout converting .doc file: {file_path}")
        except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
            raise OSError(
                f"Not able to read/convert doc file: {file_path}. Error: {e}"
            ) from e
        finally:
            if not self.debug and os.path.exists(text_file_path):
                os.remove(text_file_path)
        return content

    def read_docx(self, file_path):
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            raise OSError(f"Not able to read docx file:{file_path}. Error: {e}") from e

    def read_pdf(self, file_path):
        return self.read_xps(file_path)

    def read_xps(self, file_path):
        doc = None
        try:
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)

            if len(text.strip()) < self.n_char_min * doc.page_count:
                print(
                    f"Low text yield ({len(text.strip())} chars) for {file_path}, attempting OCR."
                )
                text = self.pdf_to_image_to_text(file_path)
            else:
                text = unidecode.unidecode(text)

        except Exception as e:
            print(f"Error reading XPS/PDF file {file_path}: {e}")
            raise OSError(f"Failed to process XPS/PDF: {file_path}. Error: {e}") from e
        finally:
            if doc:
                doc.close()
        return text

    def read_image(self, fullpath):
        try:
            text = pytesseract.image_to_string(
                Image.open(fullpath),
            )
            return text
        except pytesseract.TesseractNotFoundError:
            raise OSError(
                f"Tesseract executable not found at {self.tesseract_bin_path} or in PATH."
            )
        except Exception as e:
            raise OSError(f"Error during OCR for image {fullpath}: {e}") from e

    def read_one_file(self, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"file_path:'{file_path}' is not a file or does not exist!"
            )

        extension = pathlib.PurePosixPath(file_path).suffix.lower()
        read_function = self.switcher.get(extension)

        if read_function:
            try:
                return read_function(file_path)
            except Exception as e:
                raise OSError(
                    f"Failed to read file {file_path} using {read_function.__name__}. Error: {e}"
                ) from e
        else:
            supported_extensions = list(self.switcher.keys())
            raise OSError(
                f"File extension:'{extension}' for file '{file_path}' is not supported. "
                f"Supported: {supported_extensions}"
            )

    def read(
        self, doc_df: pd.DataFrame, timeout_per_task: float = 300.0
    ) -> pd.DataFrame:
        if self.cv_file_column not in doc_df.columns:
            raise ValueError(f"Column '{self.cv_file_column}' not found in DataFrame.")

        filepath_list = doc_df[self.cv_file_column].dropna().unique().tolist()
        print(f"[DOCUMENT PROCESSING] Processing {len(filepath_list)} unique files...")

        tasks_config = []
        for path in filepath_list:
            is_string = isinstance(path, str)
            exists = False
            if is_string:
                try:
                    exists = os.path.exists(path)
                except Exception as e:
                    print(f"  Error checking path existence: {e}")

            if is_string and exists:
                tasks_config.append(
                    {
                        "file_path": path,
                        "temporary_path": self.temporary_path,
                        "doc_reader_path": self.doc_reader_path,
                        "tesseract_path": self.tesseract_bin_path,
                        "image_resolution": self.image_resolution,
                        "n_char_min": self.n_char_min,
                        "debug": self.debug,
                    }
                )
            else:
                print(
                    "  Path is invalid or does not exist. Skipping."
                )  # Modified message

        print(f"[DOCUMENT PROCESSING] Number of tasks configured: {len(tasks_config)}")
        results_map = {}
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            future_to_config = {
                executor.submit(process_single_file, config): config
                for config in tasks_config
            }

            processed_count = 0
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                file_path = config["file_path"]
                try:
                    _fp, content, error, n_pages, dt = future.result(
                        timeout=timeout_per_task
                    )
                    results_map[file_path] = (content, error, n_pages, dt)
                    if error:
                        print(f"Processed {file_path} with error: {error} in {dt:.2f}s")
                except TimeoutError:
                    results_map[file_path] = (
                        None,
                        f"Timeout after {timeout_per_task}s",
                        0,
                        timeout_per_task,
                    )
                    print(f"Timeout processing {file_path}")
                except Exception as exc:
                    results_map[file_path] = (None, f"Future Error: {exc}", 0, 0.0)
                    print(f"Error retrieving result for {file_path}: {exc}")

                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count}/{len(tasks_config)} files...")

        print(f"[DOCUMENT PROCESSING] Finished processing {len(results_map)} files.")

        results_series = pd.Series(results_map, name="results").reindex(
            doc_df[self.cv_file_column]
        )

        content_list = []
        error_list = []
        n_pages_list = []
        dt_list = []

        for result_tuple in results_series:
            if pd.notna(result_tuple):
                content, error, n_pages, dt = result_tuple
                content_list.append(content)
                error_list.append(error)
                n_pages_list.append(n_pages)
                dt_list.append(dt)
            else:
                # Handle cases where reindex might have resulted in NaN (shouldn't happen based on logs, but safe)
                content_list.append(None)
                error_list.append("Path skipped or invalid")
                n_pages_list.append(0)
                dt_list.append(0.0)

        try:
            doc_df["content"] = content_list
            doc_df["error"] = error_list
            doc_df["n_pages"] = n_pages_list
            doc_df["n_pages"] = doc_df["n_pages"].astype("Int64")
            doc_df["dt"] = dt_list

        except Exception as e:
            print(f"!!! Error during list assignment: {e}")
            print(
                f"Length Check: results_series={len(results_series)}, "
                f"content_list={len(content_list)}, doc_df={len(doc_df)}"
            )

        skipped_mask = ~doc_df[self.cv_file_column].isin(results_map.keys())
        doc_df.loc[skipped_mask, "error"] = "Path skipped or invalid"

        return doc_df

    @staticmethod
    def convert(input_file_path, output_file_path=None):
        binary_content = b""
        try:
            with open(input_file_path, "rb") as one_file:
                binary_content = one_file.read()
        except FileNotFoundError:
            print(f"Error: Input file not found for conversion: {input_file_path}")
            return None
        except Exception as e:
            print(f"Error reading input file {input_file_path}: {e}")
            return None

        encoded_content = base64.b64encode(binary_content)
        if output_file_path is not None:
            try:
                with open(output_file_path, "wb") as one_file:
                    one_file.write(encoded_content)
                return None
            except Exception as e:
                print(f"Error writing output file {output_file_path}: {e}")
                return False
        else:
            return encoded_content
