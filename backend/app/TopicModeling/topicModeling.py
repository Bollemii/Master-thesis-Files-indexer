import pandas as pd
from datetime import datetime
import pathlib
import shutil
import numpy as np

# import matplotlib.pyplot as plt
# from scipy.optimize import minimize
from time import time
from sklearn.decomposition import LatentDirichletAllocation

# from tqdm import tqdm
# from gensim.models.ldamulticore import LdaMulticore
# from gensim.models import LdaModel, CoherenceModel
# from gensim import corpora

from Reader import *
from Miner import *


def delete_eol(content):
    if type(content) is str:
        content = content.replace("-\n", " ")
        content = content.replace("-\r", " ")
        content = content.replace("\n", " ")
        content = content.replace("\r", " ")
        return content


def get_length(content):
    if content is None:
        return 0
    else:
        return len(content)


def run():
    # data_root = '../../../../../../../../Proximus Cloud/FigSciAndCo/Downloads/'
    # data_root = 'C:/Users/lphilippe/Proximus Cloud/FigSciAndCo/Downloads/'
    # data_root = 'C:/Users/lphilippe/Documents/Henallux/MASI/Cours/TFE/lphPortagePython.SimonBaudart/input/'
    data_root = "../../documents/"
    # Create the tmp folder
    if os.path.exists("./tmp"):
        shutil.rmtree("./tmp")
    os.makedirs("./tmp")

    if 1 == 1:  # Reader
        orig_dir = os.getcwd()
        print("orig_dir:{}".format(orig_dir))
        os.chdir(data_root)
        path_list = os.listdir(".")
        #        path_list = path_list[0:100]

        file_list = []
        time_list = []
        size_list = []
        #        encoded_content_list = []
        i_file = 1
        for path in path_list:
            if os.path.isfile(path):
                # if pathlib.Path(path).suffix in ['.pdf', '.doc', '.docx', '.xps', '.txt']:
                # if pathlib.Path(path).suffix in ['.pdf', '.xps']:
                if pathlib.Path(path).suffix in [".pdf"]:
                    # print('file:{}-path:{}'.format(i_file,path))
                    file_list.append(data_root + path)
                    time_list.append(os.path.getmtime(path))
                    size_list.append(os.path.getsize(path))
                    #                    encoded_content_list.append(Reader.convert(path))
                    i_file += 1
        os.chdir(orig_dir)
        doc_df = pd.DataFrame()
        doc_df["file_path"] = file_list
        doc_df["creation_time"] = time_list
        doc_df["file_size"] = size_list

        doc_df = doc_df.sort_values(by="creation_time")
        #        doc_df = doc_df.head(120)

        # reader = Reader(cv_file_column='file_path',
        #                 tesseract_path='C:/Users/lphilippe/Documents/Agilytic/Daoust/automatch/arc/tesseract-4.0.0-alpha/tesseract.exe',
        #                 image_resolution=150)

        reader = Reader(
            cv_file_column="file_path",
            tesseract_path="/usr/bin/tesseract",
            image_resolution=150,
        )

        doc_df = reader.read(doc_df)

        # print(doc_df)

        doc_df.to_pickle("./tmp/doc_df.append.pkl")

    if 1 == 0:
        # Incremental Reader
        orig_dir = os.getcwd()
        os.chdir(data_root)
        path_list = os.listdir(".")

        file_list = []
        time_list = []
        size_list = []
        for path in path_list:
            if os.path.isfile(path):
                if pathlib.Path(path).suffix in [
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".xps",
                    ".txt",
                ]:
                    file_list.append(data_root + path)
                    time_list.append(os.path.getmtime(path))
                    size_list.append(os.path.getsize(path))
        os.chdir(orig_dir)

        meta_df = pd.DataFrame()
        meta_df["file_path"] = file_list
        meta_df["creation_time"] = time_list
        meta_df["file_size"] = size_list

        result_file = "./tmp/doc_df.append.pkl"
        if os.path.isfile(result_file):
            old_doc_df = pd.read_pickle(result_file)
            old_meta_df = old_doc_df[["file_path", "creation_time", "file_size"]]

            diff_meta_df = pd.concat(
                [meta_df, old_meta_df, old_meta_df]
            ).drop_duplicates(keep=False)
        else:
            old_doc_df = (
                pd.DataFrame().reindex_like(meta_df).head(0)
            )  # copy structure and types but NOT data
            diff_meta_df = meta_df

        # print(diff_meta_df)

        if diff_meta_df.empty:
            print("Nothing to do...")
        else:
            reader = Reader(
                cv_file_column="file_path",
                tesseract_path="C:/Users/lphilippe/Documents/Agilytic/Daoust/automatch/arc/tesseract-4.0.0-alpha/tesseract.exe",
                image_resolution=150,
            )

            diff_doc_df = reader.read(diff_meta_df)

            # print(diff_doc_df)

            merged_doc_df = pd.concat([old_doc_df, diff_doc_df])

            merged_doc_df = merged_doc_df.sort_values(by="creation_time")
            merged_doc_df.to_pickle("./tmp/doc_df.append.pkl")

    if 1 == 1:
        # Transformer
        doc_df = pd.read_pickle("./tmp/doc_df.append.pkl")
        # doc_df = pd.read_pickle('./tmp/doc_df.test.pkl')
        # print(doc_df)
        doc_df["raw_content"] = doc_df["content"]
        doc_df["content"] = doc_df.apply(
            lambda row: delete_eol(row["raw_content"]), axis=1
        )
        doc_df["file_name"] = doc_df.apply(
            lambda row: pathlib.PurePosixPath(row["file_path"]).stem, axis=1
        )
        doc_df["file_type"] = doc_df.apply(
            lambda row: pathlib.PurePosixPath(row["file_path"]).suffix.replace(".", ""),
            axis=1,
        )
        doc_df = doc_df.drop(columns=["file_path"])
        doc_df["content_size"] = doc_df.apply(
            lambda row: get_length(row["content"]), axis=1
        )
        doc_df["raw_content_size"] = doc_df.apply(
            lambda row: get_length(row["raw_content"]), axis=1
        )
        doc_df = doc_df[
            [
                "file_name",
                "file_type",
                "creation_time",
                "file_size",
                "n_pages",
                "dt",
                "error",
                "content_size",
                "content",
                "raw_content_size",
                "raw_content",
            ]
        ]
        # print(doc_df)
        doc_df.to_csv("./tmp/doc_df.test.csv", sep="|", escapechar="\\")
        doc_df.to_pickle("./tmp/doc_df.transf1.pkl")

    if 1 == 0:
        # Incremental transformer

        doc_df = pd.read_pickle(
            "./tmp/doc_df.append.pkl",
        )
        doc_df["file_name"] = doc_df.apply(
            lambda row: pathlib.PurePosixPath(row["file_path"]).stem, axis=1
        )
        #  print(doc_df)
        meta_df = doc_df[["file_name", "creation_time", "file_size"]]

        result_file = "./tmp/doc_df.transf1.pkl"
        if os.path.isfile(result_file):
            old_doc_df = pd.read_pickle(result_file)
            old_meta_df = old_doc_df[["file_name", "creation_time", "file_size"]]

            diff_meta_df = pd.concat(
                [meta_df, old_meta_df, old_meta_df]
            ).drop_duplicates(keep=False)
        else:
            old_doc_df = (
                pd.DataFrame().reindex_like(meta_df).head(0)
            )  # copy structure and types but NOT data
            diff_meta_df = meta_df

        if diff_meta_df.empty:
            print("Nothing to do...")
        else:
            print("Transform {} record(s)".format(diff_meta_df.shape[0]))

            diff_doc_df = doc_df.join(
                diff_meta_df.set_index(["file_name", "creation_time", "file_size"]),
                on=["file_name", "creation_time", "file_size"],
                how="inner",
            )

            diff_doc_df["raw_content"] = diff_doc_df["content"]
            diff_doc_df["content"] = diff_doc_df.apply(
                lambda row: delete_eol(row["raw_content"]), axis=1
            )
            diff_doc_df["file_type"] = diff_doc_df.apply(
                lambda row: pathlib.PurePosixPath(row["file_path"]).suffix.replace(
                    ".", ""
                ),
                axis=1,
            )
            diff_doc_df = diff_doc_df.drop(columns=["file_path"])
            diff_doc_df["content_size"] = diff_doc_df.apply(
                lambda row: get_length(row["content"]), axis=1
            )
            diff_doc_df["raw_content_size"] = diff_doc_df.apply(
                lambda row: get_length(row["raw_content"]), axis=1
            )
            diff_doc_df = diff_doc_df[
                [
                    "file_name",
                    "file_type",
                    "creation_time",
                    "file_size",
                    "n_pages",
                    "dt",
                    "error",
                    "content_size",
                    "content",
                    "raw_content_size",
                    "raw_content",
                ]
            ]
            print(diff_doc_df)

            merged_doc_df = pd.concat([old_doc_df, diff_doc_df], sort=False)
            merged_doc_df = merged_doc_df.sort_values(by="creation_time")

            merged_doc_df.to_csv("./tmp/doc_df.transf1.csv", sep="|", escapechar="\\")
            merged_doc_df.to_pickle("./tmp/doc_df.transf1.pkl")

    if 1 == 1:

        doc_df = pd.read_pickle("./tmp/doc_df.transf1.pkl")
        # doc_df = doc_df.head(100)

        miner = Miner()
        transf_doc_df = miner.mine(doc_df)
        transf_doc_df = transf_doc_df[
            [
                "file_name",
                "file_type",
                "creation_time",
                "file_size",
                "n_pages",
                "dt",
                "error",
                "language",
                "without_stop_words",
            ]
        ]
        transf_doc_df.to_csv("./tmp/doc_df.transf2.csv", sep="|", escapechar="\\")
        #
        # Force a specific protocol to be able to load in jupyter notebook...
        # https://brainsteam.co.uk/2021/01/14/pickle-5-madness-with-mlflow/
        #
        transf_doc_df.to_pickle("./tmp/doc_df.transf2.pkl", protocol=4)

    if 1 == 1:

        np.set_printoptions(precision=3)
        np.set_printoptions(suppress=True)

        # data_root = '..'

        transf_doc_df = pd.read_csv("./tmp/doc_df.transf2.csv", sep="|")

        transf_doc_df.count()

        # print(transf_doc_df.tail(10)['without_stop_words'])

        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer = CountVectorizer(ngram_range=(1, 2), max_df=0.8, min_df=0.01)

        no_error_df = transf_doc_df[transf_doc_df["error"].isnull()]
        english_df = no_error_df[no_error_df["language"] == "EN"]
        corpus = english_df["without_stop_words"]

        X = vectorizer.fit_transform(corpus)

        print(vectorizer.get_feature_names_out())

        doc_topic_prior = 0.085
        topic_word_prior = 0.225

        n_topics = 10

        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=0,
            verbose=1,
            doc_topic_prior=doc_topic_prior,
            topic_word_prior=topic_word_prior,
            evaluate_every=10,
            n_jobs=2,
            max_iter=100,
        )
        lda.fit(X.toarray())
        perplexity = lda.perplexity(X.toarray())
        print("Perplexity", perplexity)

    # print("That's All, Folks!!!")


if __name__ == "__main__":

    run()
