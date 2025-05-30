import os
import pathlib
from multiprocessing import cpu_count
import pandas as pd
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from app.config import settings
from app.TopicModeling.miner_v2 import Miner
from app.TopicModeling.Reader import Reader

LIBREOFFICE_PATH = settings.LIBREOFFICE_PATH
if not LIBREOFFICE_PATH:
    raise ValueError("LIBREOFFICE_PATH must be set in environment variables.")
TESSERACT_PATH = settings.TESSERACT_PATH
if not TESSERACT_PATH:
    raise ValueError("TESSERACT_PATH must be set in environment variables.")
NB_TOPICS = settings.LDA_NB_TOPICS if settings.LDA_NB_TOPICS else 5
NB_TOP_WORDS = settings.LDA_NB_TOP_WORDS if settings.LDA_NB_TOP_WORDS else 10


def delete_eol(content):
    if isinstance(content, str):
        content = content.replace("-\n", " ")
        content = content.replace("-\r", " ")
        content = content.replace("\n", " ")
        content = content.replace("\r", " ")
        return content


def get_length(content):
    if not isinstance(content, str):
        return 0
    return len(content)


def process_documents(doc_df):
    print("[DOCUMENT PROCESSING] Processing documents...")

    reader = Reader(
        cv_file_column="file_path",
        doc_reader_path=LIBREOFFICE_PATH,
        tesseract_path=TESSERACT_PATH,
        image_resolution=150,
    )

    doc_df = reader.read(doc_df)

    doc_df.to_pickle("./tmp/doc_df.reader.pkl")

    doc_df["raw_content"] = doc_df["content"]
    doc_df["content"] = doc_df.apply(lambda row: delete_eol(row["raw_content"]), axis=1)
    doc_df["file_type"] = doc_df.apply(
        lambda row: pathlib.PurePosixPath(row["file_path"]).suffix.replace(".", ""),
        axis=1,
    )
    doc_df["content_size"] = doc_df.apply(
        lambda row: get_length(row["content"]), axis=1
    )
    doc_df["raw_content_size"] = doc_df.apply(
        lambda row: get_length(row["raw_content"]), axis=1
    )
    doc_df = doc_df[
        [
            "file_name",
            "file_path",
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

    doc_df.to_pickle("./tmp/doc_df.transformer.pkl")

    miner = Miner()
    transf_doc_df = miner.mine(doc_df)
    transf_doc_df = transf_doc_df[
        [
            "file_name",
            "file_path",
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
    transf_doc_df.to_pickle("./tmp/doc_df.miner.pkl")

    return transf_doc_df


def run_lda(doc_df):
    print("[DOCUMENT PROCESSING] Starting LDA...")
    vectorizer = CountVectorizer(ngram_range=(1, 2), max_df=0.8, min_df=0.05)
    X = vectorizer.fit_transform(doc_df["content"])

    doc_topic_prior = 0.085
    topic_word_prior = 0.225

    lda = LatentDirichletAllocation(
        n_components=NB_TOPICS,
        random_state=0,
        verbose=1,
        doc_topic_prior=doc_topic_prior,
        topic_word_prior=topic_word_prior,
        evaluate_every=50,
        n_jobs=cpu_count() - 1,
        max_iter=500,
    )
    lda.fit(X)

    topic_words = vectorizer.get_feature_names_out()
    topic_word_prob = lda.components_ / lda.components_.sum(axis=1)[:, np.newaxis]
    topics = []
    for topic in topic_word_prob:
        words_in_topic = zip(topic_words, topic)
        sorted_words = sorted(words_in_topic, key=lambda x: float(x[1]), reverse=True)[
            :NB_TOP_WORDS
        ]
        topics.append(sorted_words)

    doc_topic_dist = lda.transform(X)
    doc_topics = []
    for doc_idx, topic_dist in enumerate(doc_topic_dist):
        doc_file_name = doc_df.iloc[doc_idx]["file_name"]
        doc_topics.append((doc_file_name, topic_dist.tolist()))

    return topics, doc_topics


def run(doc_df):
    print("[DOCUMENT PROCESSING] Starting Topic Modeling...")
    topics, doc_topics = run_lda(doc_df)
    return topics, doc_topics


def delete_document_from_cache(filepath: str):
    if not os.path.exists("./tmp/doc_df.miner.pkl"):
        return

    try:
        existing_df = pd.read_pickle("./tmp/doc_df.miner.pkl")
        print(f"New file path: {filepath}")
        print(f"Existing file paths: {existing_df['file_name'].values}")
        if filepath in existing_df["file_name"].values:
            updated_df = existing_df[existing_df["file_name"] != filepath]
            updated_df.to_pickle("./tmp/doc_df.miner.pkl")

            for cache_file in [
                "./tmp/doc_df.reader.pkl",
                "./tmp/doc_df.transformer.pkl",
            ]:
                cache_path = f"./tmp/{cache_file}"
                if os.path.exists(cache_path):
                    try:
                        cache_df = pd.read_pickle(cache_path)
                        if filepath in cache_df["file_name"].values:
                            cache_df = cache_df[cache_df["file_name"] != filepath]
                            cache_df.to_pickle(cache_path)
                    except Exception:
                        # If there's an error with the other caches, we can still continue
                        pass
        return True
    except Exception as e:
        print(f"Error deleting document {filepath}: {str(e)}")
        return False
