import os
import shutil
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pathlib
from Reader import *
from Miner import *

def delete_eol(content):
    if type(content) is str:
        content = content.replace('-\n', ' ')
        content = content.replace('-\r', ' ')
        content = content.replace('\n', ' ')
        content = content.replace('\r', ' ')
        return content


def get_length(content):
    if content is None:
        return 0
    else:
        return len(content)

def run():
    data_root = '../../documents/'  # Set your data root directory

    if os.path.exists('./tmp'):
        shutil.rmtree('./tmp')
    os.makedirs('./tmp')

    orig_dir = os.getcwd()
    print('orig_dir:{}'.format(orig_dir))
    os.chdir(data_root)
    path_list = os.listdir('.')

    file_list = []
    time_list = []
    size_list = []
    i_file = 1
    for path in path_list:
        if os.path.isfile(path) and pathlib.Path(path).suffix == '.pdf':
            file_list.append(data_root + path)
            time_list.append(os.path.getmtime(path))
            size_list.append(os.path.getsize(path))
            i_file += 1
    os.chdir(orig_dir)
    doc_df = pd.DataFrame()
    doc_df['file_path'] = file_list
    doc_df['creation_time'] = time_list
    doc_df['file_size'] = size_list

    doc_df = doc_df.sort_values(by='creation_time')

    reader = Reader(cv_file_column='file_path',
                    tesseract_path='/usr/bin/tesseract',
                    image_resolution=150)

    doc_df = reader.read(doc_df)

    doc_df.to_pickle('./tmp/doc_df.reader.pkl', protocol=4)

    doc_df['raw_content'] = doc_df['content']
    doc_df['content'] = doc_df.apply(lambda row: delete_eol(row['raw_content']), axis=1)
    doc_df['file_name'] = doc_df.apply(lambda row: pathlib.PurePosixPath(row['file_path']).stem, axis=1)
    doc_df['file_type'] = doc_df.apply(lambda row: pathlib.PurePosixPath(row['file_path']).suffix.replace('.', ''), axis=1)
    doc_df = doc_df.drop(columns=['file_path'])
    doc_df['content_size'] = doc_df.apply(lambda row: get_length(row['content']), axis=1)
    doc_df['raw_content_size'] = doc_df.apply(lambda row: get_length(row['raw_content']), axis=1)
    doc_df = doc_df[['file_name', 'file_type', 'creation_time', 'file_size', 'n_pages', 'dt', 'error',
                        'content_size', 'content', 'raw_content_size', 'raw_content']]

    doc_df.to_pickle('./tmp/doc_df.transformer.pkl', protocol=4)

    miner = Miner()
    transf_doc_df = miner.mine(doc_df)
    transf_doc_df = transf_doc_df[['file_name', 'file_type', 'creation_time', 'file_size', 'n_pages', 'dt', 'error',
                                    'language', 'without_stop_words']]
    transf_doc_df.to_csv('./tmp/doc_df.miner.csv', sep='|', escapechar='\\')
    transf_doc_df.to_pickle('./tmp/doc_df.miner.pkl', protocol=4)

    np.set_printoptions(precision=3, suppress=True)

    no_error_df = transf_doc_df[transf_doc_df['error'].isnull()]
    # english_df = no_error_df[no_error_df['language'] == 'EN']
    corpus = no_error_df['without_stop_words']

    vectorizer = CountVectorizer(ngram_range=(1, 2), max_df=0.8, min_df=0.01)
    X = vectorizer.fit_transform(corpus)

    doc_topic_prior = 0.085
    topic_word_prior = 0.225
    n_topics = 5

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=0, verbose=1,
                                    doc_topic_prior=doc_topic_prior, topic_word_prior=topic_word_prior,
                                    evaluate_every=10, n_jobs=-1, max_iter=100)
    lda.fit(X)

    perplexity = lda.perplexity(X)
    print("Perplexity", perplexity)

    # Extract topics and their weights
    topic_words = vectorizer.get_feature_names_out()
    topics = []
    for topic_idx, topic in enumerate(lda.components_):
        topic_words_frequencies = [(topic_words[i], X[:, i].sum()) for i in topic.argsort()[:-11:-1]]
        topic_words_frequencies.sort(key=lambda x: x[1], reverse=True) 
        topics.append(topic_words_frequencies)
        print(f"Topic #{topic_idx}:")
        for word, frequency in topic_words_frequencies:
            print(f"  {word}: {frequency}")

    # Extract document-topic distribution
    doc_topic_dist = lda.transform(X)
    doc_topics = []
    for doc_idx, topic_dist in enumerate(doc_topic_dist):
        doc_topics.append((file_list[doc_idx], topic_dist))
        print(f"Document #{doc_idx}: {file_list[doc_idx]}")
        for topic_idx, weight in enumerate(topic_dist):
            print(f"  Topic {topic_idx}: {weight:.4f}")

    return topics, doc_topics

if __name__ == '__main__':
    topics, doc_topics = run()