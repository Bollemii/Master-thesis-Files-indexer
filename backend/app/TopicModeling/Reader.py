import pandas as pd
import numpy as np
import os
import pathlib
import subprocess
import base64
from multiprocessing import Process, Queue, Pipe, cpu_count
from multiprocessing.connection import wait
from datetime import datetime
import signal
from docx2txt import docx2txt
import unidecode
import pytesseract
from PIL import Image
import fitz

#
# Do not install fitz package in parallel with pymupdf (there's a local installation of fitz within pymupdf package!!!)
# But still we have to include 'import fitz' and NOT pymupdf something... it's strange but it is like this!!!
#


def work(
    worker_id,
    queue,
    wEnd,
    temporary_path,
    doc_reader_path,
    tesseract_path,
    image_resolution,
    debug,
):
    reader = Reader(
        temporary_path=temporary_path,
        doc_reader_path=doc_reader_path,
        tesseract_path=tesseract_path,
        image_resolution=image_resolution,
        debug=debug,
    )
    flag_stop = False
    request_id = None
    file_path = None
    while True:
        start_sent_flag = False

        cmd = None
        timestamp = None
        request_id = None
        file_path = None
        n_pages = 0
        content = None

        try:
            cmd, request_id, file_path = queue.get()
            print(worker_id, cmd, request_id, file_path)
            if cmd == "STOP":
                print("STOP command received in worker:{}".format(worker_id))
                flag_stop = True
            if cmd == "READ":
                timestamp = datetime.now()
                n_pages = reader.get_n_pages(file_path)
                wEnd.send(
                    [
                        "START",
                        timestamp,
                        worker_id,
                        request_id,
                        file_path,
                        n_pages,
                        None,
                        None,
                    ]
                )
                start_sent_flag = True
                print(worker_id, "read_one_file")
                content = reader.read_one_file(file_path)
                # time.sleep(10)
                print(worker_id, "...done")
                timestamp = datetime.now()
                wEnd.send(
                    [
                        "STOP",
                        timestamp,
                        worker_id,
                        request_id,
                        file_path,
                        None,
                        None,
                        content,
                    ]
                )
            if flag_stop:
                break
        except Exception as exception:
            print("Exception:{}".format(exception.__str__()))
            timestamp = datetime.now()
            if start_sent_flag is False:
                wEnd.send(
                    [
                        "START",
                        timestamp,
                        worker_id,
                        request_id,
                        file_path,
                        n_pages,
                        None,
                        None,
                    ]
                )
            wEnd.send(
                [
                    "STOP",
                    timestamp,
                    worker_id,
                    request_id,
                    file_path,
                    None,
                    exception.__str__(),
                    None,
                ]
            )
    print("Normal end of worker:{}".format(worker_id))
    wEnd.close()
    return


def read_one_file(
    file_path, temporary_path, doc_reader_path, tesseract_path, image_resolution=500
):
    reader = Reader(
        temporary_path=temporary_path,
        doc_reader_path=doc_reader_path,
        tesseract_path=tesseract_path,
        image_resolution=image_resolution,
    )
    content = reader.read_one_file(file_path)
    with open(file_path + ".content.txt", "w") as one_file:
        one_file.write(unidecode.unidecode(content))


class Reader:

    def __init__(
        self,
        cv_file_column="cv_file",
        cv_content_column="cv_content_base64",
        temporary_path="tmp",
        doc_reader_path="",
        tesseract_path="",
        image_resolution=500,
        n_char_min=5,  # min char per page before being considered as a bad vectorized reading and
        # switching to OCR
        debug=False,
    ):

        self.switcher = {
            ".txt": self.read_text,
            ".doc": self.read_doc,
            # '.docx':self.read_docx,
            ".pdf": self.read_xps,
            ".png": self.read_image,
            ".xps": self.read_xps,
            # '.oxps':self.read_xps
        }
        self.cv_file_column = cv_file_column
        self.cv_content_column = cv_content_column
        self.temporary_path = temporary_path
        self.doc_reader_path = doc_reader_path
        self.tesseract_bin_path = tesseract_path
        self.image_resolution = image_resolution
        self.debug = debug
        self.n_char_min = n_char_min

        return

    def get_n_pages(self, filepath):
        extension = pathlib.PurePosixPath(filepath).suffix.replace(".", "")
        if extension in ("txt", "doc", "docx"):
            return 0
        if extension == "png":
            return 1
        doc = fitz.open(filepath)
        n_pages = doc.page_count
        doc.close()
        return n_pages

    def pdf_to_image_to_text(self, fullpath):
        default_resolution = 96  # dpi
        zoom_x = self.image_resolution / default_resolution  # horizontal zoom
        zoom_y = zoom_x  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)
        doc = fitz.open(fullpath)
        text = ""
        for page in doc:  # iterate through the pages
            pix = page.get_pixmap(alpha=False, matrix=mat)  # render page to an image
            image_path = (
                self.temporary_path
                + "/"
                + "{}.{}.page-{}.png".format(os.getppid(), os.getpid(), page.number)
            )
            pix.save(image_path)
            text += self.read_image(image_path)
            if self.debug is False:
                os.remove(image_path)
        doc.close()
        return text

    def read_text(self, file_path):
        content = ""
        try:
            with open(file_path, encoding="utf-8") as one_file:
                content = one_file.read()
        except Exception:
            try:
                with open(file_path, encoding="latin-1") as one_file:
                    content = one_file.read()
            except Exception:
                raise OSError(
                    "Not able to read text file:{} in [utf-8,latin-1] coding".format(
                        file_path
                    )
                )
        return content

    def read_doc(self, file_path):
        content = ""
        try:
            subprocess.call(
                [
                    self.doc_reader_path,
                    "--headless",
                    "--convert-to",
                    "txt",
                    file_path,
                    "--outdir",
                    self.temporary_path,
                ]
            )
            text_file_path = (
                self.temporary_path
                + "/"
                + pathlib.PurePosixPath(file_path).stem
                + ".txt"
            )
            content = self.read_text(text_file_path)
            if self.debug is False:
                os.remove(text_file_path)
        except Exception as exception:
            raise OSError(
                "Not able to read doc file:{} because:{}".format(
                    file_path, exception.__str__()
                )
            )
        return content

    def read_docx(self, file_path):
        try:
            converter = docx2txt
            return converter.process(file_path)
        except Exception as exception:
            raise OSError(
                "Not able to read docx file:{} because:{}".format(
                    file_path, exception.__str__()
                )
            )

    def read_pdf(self, file_path):
        return self.read_xps(file_path)

    def read_xps(self, file_path):
        doc = fitz.open(file_path)
        text = ""
        for i_page in range(doc.page_count):
            page = doc[i_page]
            text += page.get_text()
        clean_text = text.replace("\n", "")
        doc.close()
        if (
            len(clean_text) >= self.n_char_min
        ):  # probable better solution: consider this size vs total binary page size
            return unidecode.unidecode(text)
        else:
            text = self.pdf_to_image_to_text(file_path)
            return text

    def read_one_file(self, file_path):
        if not os.path.isfile(file_path):
            raise OSError("file_path:'{}' is not a real file!".format(file_path))

        extension = pathlib.PurePosixPath(file_path).suffix
        if extension in self.switcher.keys():
            read_function = self.switcher.get(extension)
            return read_function(file_path)
        else:
            raise OSError(
                "file extension:'{}' not found in '{}'".format(
                    extension, self.switcher.keys()
                )
            )

    def read(self, doc_df):
        filepath_list = doc_df[self.cv_file_column].to_list()
        #
        # Check that both list have the same length!!!
        #
        reply_df = pd.DataFrame()

        reply_filepath_list = []
        error_msg_list = []
        content_list = []
        n_pages_list = []
        dt_list = []

        queue = Queue()
        readers = []
        workers = []
        n_workers = cpu_count()
        for i_worker in range(n_workers):
            rEnd, wEnd = Pipe(duplex=False)
            readers.append(rEnd)
            w = Process(
                target=work,
                args=(
                    i_worker,
                    queue,
                    wEnd,
                    "./tmp",
                    self.doc_reader_path,
                    self.tesseract_bin_path,
                    500,
                    False,
                ),
            )
            workers.append(w)
            workers[i_worker].start()
            wEnd.close()

        task_process_map = {}
        task_map = {}
        n_pages_map = {}
        for i_task in range(filepath_list.__len__()):
            queue.put(["READ", i_task, filepath_list[i_task]])

        for i_worker in range(n_workers):
            queue.put(["STOP", None, None])

        wait_timeout = 1.0
        task_timeout = 60.0
        while readers:
            # print('readers:{}'.format(readers))
            # print('workers:{}'.format(workers))
            for r in wait(readers, timeout=wait_timeout):
                try:
                    msg = r.recv()
                except EOFError:
                    readers.remove(r)
                else:
                    if msg[0] == "START":
                        request_id = msg[3]
                        task_id = request_id
                        timestamp = msg[1]
                        task_map[task_id] = timestamp
                        worker_id = msg[2]
                        task_process_map[task_id] = worker_id
                        n_pages_map[task_id] = msg[5]
                    if msg[0] == "STOP":
                        timestamp = msg[1]
                        task_id = msg[3]
                        dt = (timestamp - task_map[task_id]).total_seconds()
                        task_map[task_id] = dt

                        reply_filepath_list.append(msg[4])
                        error_msg_list.append(msg[6])
                        content_list.append(msg[7])
                        n_pages_list.append(n_pages_map[task_id])

                        dt_list.append(dt)
                    # print('parent received:{}'.format(msg))
            # print('len(task_map):{}'.format(len(task_map)))
            # print('task_map:{}'.format(task_map))
            for i_task in task_map.keys():
                t = task_map[i_task]
                if type(t) is not float:
                    t1 = datetime.now()
                    dt = (t1 - t).total_seconds()
                    if dt > task_timeout * (1 + n_pages_map[i_task]):
                        task_map[i_task] = dt
                        # kill process associated to this task
                        worker_id = task_process_map[i_task]
                        print("worker_id:{}".format(worker_id))
                        pid = workers[worker_id].pid
                        print(
                            "parent: task_id[{}]:{} is in timeout...".format(
                                i_task, pid
                            )
                        )
                        os.kill(
                            pid, signal.SIGTERM
                        )  # or signal.SIGKILL (linux only) # process continues
                        # processing but pipe is broken => not possible to receive any update => safe
                        # create a new fresh process to add to process list
                        rEnd, wEnd = Pipe(duplex=False)
                        readers.append(rEnd)
                        n_workers += 1
                        w = Process(
                            target=work,
                            args=(
                                n_workers - 1,
                                queue,
                                wEnd,
                                "./tmp",
                                self.doc_reader_path,
                                self.tesseract_bin_path,
                                500,
                                False,
                            ),
                        )
                        workers.append(w)
                        workers[n_workers - 1].start()
                        wEnd.close()

                        reply_filepath_list.append(filepath_list[i_task])
                        error_msg_list.append("timeout")
                        n_pages_list.append(n_pages_map[i_task])
                        dt_list.append(dt)
                        content_list.append(None)

        reply_df["file_path"] = reply_filepath_list
        reply_df["content"] = content_list
        reply_df["error"] = error_msg_list
        reply_df["n_pages"] = n_pages_list
        reply_df["dt"] = dt_list

        doc_df = doc_df.join(reply_df.set_index("file_path"), on="file_path")

        return doc_df

    def modified_read(
        self, doc_df
    ):  # Note that due to GIL, there's no real full potential multi-threading in
        # cPython :( => we prefer using Process!!! even if we have overhead for very
        # simple file (as text, doc, docs,... without OCR)
        #
        # As usual, probably the best solution will be in the middle: synchroneous
        # for simple text (txt, doc, docx, vectorize pdf,...) and asynchroneous when OCR is required
        #
        # In all cases, the most efficient will be to use a Process pool with task Queue
        #
        #
        #
        cv_file_array = np.asarray(doc_df[self.cv_file_column])
        cv_content_array = np.asarray(doc_df[self.cv_content_column])
        #
        # Check that both list have the same length!!!
        #
        error_msg_list = []
        content_list = []
        for i in range(len(cv_file_array)):
            content = None
            error_msg = None
            tmp_file_path = ""
            result_file_path = ""
            try:
                print(
                    "read file[{}] on {}:{}".format(
                        i, len(cv_file_array), cv_file_array[i]
                    ),
                    end="",
                )
                tmp_file_path = self.temporary_path + "/" + cv_file_array[i]
                with open(tmp_file_path, "wb") as one_file:
                    one_file.write(base64.b64decode(cv_content_array[i]))
                process = Process(
                    target=read_one_file,
                    args=(
                        tmp_file_path,
                        self.temporary_path,
                        self.doc_reader_path,
                        self.tesseract_bin_path,
                        self.image_resolution,
                    ),
                )
                process.start()
                max_total_timeout = 600
                timeout = 0.1
                t0 = datetime.now()
                total_time = 0
                rc = None
                while (rc is None) & (total_time < max_total_timeout):
                    process.join(timeout)
                    rc = process.exitcode
                    t1 = datetime.now()
                    total_time = (t1 - t0).total_seconds()
                if rc is None:
                    raise Exception(
                        "Request timeout:{} seconds".format(max_total_timeout)
                    )
                if rc < 0:
                    raise Exception("read_one_file in error:{}".format(-rc))
                result_file_path = tmp_file_path + ".content.txt"
                with open(result_file_path, "r") as one_file:
                    content = one_file.read()
                if self.debug is False:
                    os.remove(result_file_path)
                    os.remove(tmp_file_path)
                print(" ... done in {} seconds".format(total_time))
                pass
            except Exception as exception:
                content = None
                error_msg = "Reader:" + exception.__str__()
                print(" ... done with exception:{}".format(error_msg))
                if self.debug is False:
                    if os.path.isfile(tmp_file_path):
                        os.remove(tmp_file_path)
                    if os.path.isfile(result_file_path):
                        os.remove(result_file_path)

            content_list.append(content)
            error_msg_list.append(error_msg)

        doc_df["content"] = content_list
        doc_df["error"] = error_msg_list
        return doc_df

    def read_image(self, fullpath):
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_bin_path
        text = pytesseract.image_to_string(
            Image.open(fullpath),
        )
        return text

    @staticmethod
    def convert(input_file_path, output_file_path=None):
        binary_content = ""
        with open(input_file_path, "rb") as one_file:
            binary_content = one_file.read()
        encoded_content = base64.b64encode(binary_content)
        if output_file_path is not None:
            with open(output_file_path, "wb") as one_file:
                one_file.write(encoded_content)
                return None
        else:
            return encoded_content
