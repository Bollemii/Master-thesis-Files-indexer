import os
import pathlib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from app.TopicModeling.Reader import Reader
from app.TopicModeling.miner_v2 import Miner


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


def process_documents(doc_df):

    tesseract_path = os.getenv("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
    libreoffice_path = os.getenv("LIBREOFFICE_PATH", "/usr/bin/libreoffice")

    reader = Reader(
        cv_file_column="file_path",
        doc_reader_path=libreoffice_path,
        tesseract_path=tesseract_path,
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

    doc_df.to_pickle("./tmp/doc_df.transformer.pkl")

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
    transf_doc_df.to_pickle("./tmp/doc_df.miner.pkl")

    return transf_doc_df


def run_lda(transf_doc_df):

    no_error_df = transf_doc_df[transf_doc_df["error"].isnull()]
    corpus = no_error_df["without_stop_words"]

    vectorizer = CountVectorizer(ngram_range=(1, 2), max_df=0.8, min_df=0.05)
    X = vectorizer.fit_transform(corpus)

    doc_topic_prior = 0.085
    topic_word_prior = 0.225
    n_topics = 5

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=0,
        verbose=1,
        doc_topic_prior=doc_topic_prior,
        topic_word_prior=topic_word_prior,
        evaluate_every=50,
        n_jobs=-1,
        max_iter=500,
    )
    lda.fit(X)

    topic_words = vectorizer.get_feature_names_out()
    topics = []
    for topic in lda.components_:
        words_in_topic = zip(topic_words, topic)
        sorted_words = sorted(words_in_topic, key=lambda x: float(x[1]), reverse=True)[
            :10
        ]
        topics.append(sorted_words)

    doc_topic_dist = lda.transform(X)
    doc_topics = []
    for doc_idx, topic_dist in enumerate(doc_topic_dist):
        doc_file_name = no_error_df.iloc[doc_idx]["file_name"]
        doc_topics.append((doc_file_name, topic_dist.tolist()))

    return topics, doc_topics


def run(doc_df):
    if not os.path.exists("./tmp"):
        os.makedirs("./tmp")
    if not os.path.exists("./tmp/doc_df.miner.pkl"):
        transf_doc_df = process_documents(doc_df)
    else:
        existing_df = pd.read_pickle("./tmp/doc_df.miner.pkl")
        new_docs = doc_df[~doc_df["file_path"].isin(existing_df["file_path"])]
        if not new_docs.empty:
            new_transf_doc_df = process_documents(new_docs)
            transf_doc_df = pd.concat([existing_df, new_transf_doc_df])
            transf_doc_df.to_pickle("./tmp/doc_df.miner.pkl")
        else:
            transf_doc_df = existing_df

    topics, doc_topics = run_lda(transf_doc_df)
    return topics, doc_topics


def delete_document_from_cache(filepath: str):
    if not os.path.exists("./tmp/doc_df.miner.pkl"):
        return

    try:
        existing_df = pd.read_pickle("./tmp/doc_df.miner.pkl")

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
