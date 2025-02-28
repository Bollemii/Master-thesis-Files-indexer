import nltk
import pandas as pd
from copy import deepcopy
import langdetect
import unidecode
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from nltk.stem.snowball import FrenchStemmer, DutchStemmer


def detect_language(text):
    try:
        res = langdetect.detect_langs(text)
        for item in res:
            if item.lang == "fr" or item.lang == "en":
                return item.lang.upper()
        return None
    except Exception as exception:
        print('Miner.detect_language:{}'.format(exception.__str__()))
        return None


# def substitute_url(text, substitutedURL='URL'):
    #
    # https://regexr.com/3au3g
    #
    # substituted = re.sub('(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', 'URL', text)
    #
    # https://www.regextester.com/94502
    #
    # return re.sub('(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+', substitutedURL, text)

def normalize(text):
    normalized = ''
    try:
        #normalized = re.sub('(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', ' ', text)
        normalized = substitute_url(text,' ')
        normalized = re.sub('\\W', ' ', normalized)
        normalized = re.sub('\\d', ' ', normalized)
        normalized = re.sub(' +', ' ', normalized)
        normalized = normalized.lower()
    except Exception as exception:
        print('normalize:{}'.format(exception.__str__()))
    if normalized == ' ':
        normalized = ''

    return normalized

def cleanDataTier1(data):  # basic cleaning
    if type(data) == str:
        try:
            data = unidecode.unidecode(data)
            data = data.replace('(', '').replace(')', '').replace('*', '').replace('+', '').replace('[', '').replace(
                ']', '').replace('|', '').replace('∆', '').replace('?', '')  # remove
            data = data.replace('\t', ' ').replace('\n', ' ').replace(':', ' ').replace('-', ' ').replace('_', ' ').replace(';',
                                                                                                          ' ').replace(
                '\\', ' ').replace('.', ' ').replace(',', ' ').replace('\'', ' ').replace('/', ' ').replace('<',
                                                                                                            ' ')  # replace by spaces
            output = data.lower()  # to lower case
            return output
        except:
            return None
    if type(data) == list or pd.core.series.Series:
        try:
            output = []
            for element in data:
                element = unidecode.unidecode(element)
                element = element.replace('(', '').replace(')', '').replace('*', '').replace('+', '').replace('[',
                                                                                                              '').replace(
                    ']', '').replace('|', '').replace('∆', '').replace('?', '')  # remove
                element = element.replace('\t', ' ').replace('\n', ' ').replace(':', ' ').replace('-', ' ').replace('_', ' ').replace(';',
                                                                                                                    ' ').replace(
                    '\\', ' ').replace('.', ' ').replace(',', ' ').replace('\'', ' ').replace('/', ' ').replace('<',
                                                                                                                ' ')  # replace by spaces
                element = element.lower()  # to lower case
                output.append(element)
            return output
        except:
            return None


def cleanDataTier2(data, stopword_df, language, min_len=1, delete_list=[]):  # removing unnecessary words
    stopword_list = []
    try:
        stopword_list = stopword_df[stopword_df['Language'] == language]['Stopword_list'].values[0]
    except:
        return None

    if type(data) == str:
        try:
            words = data.split()  # split text into words
            filtered_words = []  # declare an empty list to hold our filtered words
            for word in words:  # iterate over all words from the text
                if word not in stopword_list and len(
                        word) > min_len:  # only add words that are not in the French stopwords list, and are more than 1 character
                    filtered_words.append(word)  # add word to filter_words list if it meets the above conditions
            output = ' '.join(filtered_words)

            for d in delete_list:
                output = output.replace(d, '')
            return output
        except:
            return None

    if type(data) == list or pd.core.series.Series:
        try:
            output = []
            for element in data:
                words = element.split()  # split text into words
                filtered_words = []  # declare an empty list to hold our filtered words
                for word in words:  # iterate over all words from the text
                    if word not in stopword_list and len(
                            word) > min_len:  # only add words that are not in the French stopwords list, and are more than 1 character
                        filtered_words.append(word)  # add word to filter_words list if it meets the above conditions
                data = ' '.join(filtered_words)
                for d in delete_list:
                    data.replace(d, '')
                output.append(data)
            return output
        except:
            return None


def cleanDataTier3(data, language):  # stem words
    stemmer = None

    try:
        if language == "FR":
            stemmer = FrenchStemmer()
        if language == "NL":
            stemmer = DutchStemmer()
    except:
        return None

    if type(data) == str:
        try:
            words = data.split()  # split text into words
            stemmed_words = []  # declare an empty list to hold our stemmed words
            for word in words:
                stemmed_word = stemmer.stem(stemmer.stem(stemmer.stem(word)))  # stem the word three times to be sure
                stemmed_words.append(stemmed_word)  # add it to our stemmed word list
            output = ' '.join(stemmed_words)
            return output
        except:
            return None

    if type(data) == list or pd.core.series.Series:
        try:
            output = []
            for element in data:
                words = element.split()  # split text into words
                stemmed_words = []  # declare an empty list to hold our stemmed words
                for word in words:
                    stemmed_word = stemmer.stem(
                        stemmer.stem(stemmer.stem(word)))  # stem the word three times to be sure
                    stemmed_words.append(stemmed_word)  # add it to our stemmed word list
                data = ' '.join(stemmed_words)
                output.append(data)
            return output
        except:
            return None


def transform_to_set(df, column, combination_length):
    try:
        output = []
        splitted = df[column].str.split()
        for index, row in df.iterrows():
            l = len(row.text1)
            for i in range(2, combination_length):
                base = splitted[index]
                inter = []
                for j in range(l - i):
                    joined = ' '.join(base[j:j + i])
                    inter += [joined]
                base += inter
            output.append(set(base))
        return output
    except:
        return None


class Miner:
    def __init__(self):
        nltk.download('wordnet')
        nltk.download('stopwords')
        self.lemmatizer = WordNetLemmatizer()
        self.stopWords = {}
        self.stopWords['EN'] = set(stopwords.words('english'))
        self.stopWords['FR'] = set(stopwords.words('french'))

        return

    def lemmatize(self, text):
        lemmatized = ''
        for word in text.split(' '):
            lemmatized += self.lemmatizer.lemmatize(word) + ' '
        return lemmatized

    def delete_stop_words(self, language, text):
        final_text = ''
        for word in text.split(' '):
            if word not in self.stopWords[language]:
                final_text = final_text + ' ' + word
        return final_text

    def mine(self,doc_df,content_column_name='content'):
        # original order index
        doc_df = doc_df.reset_index(drop=True)
        doc_df['original_order'] = doc_df.index

        # strip doc_df already on error
        with_error_df = deepcopy(doc_df[doc_df['error'].notnull()])
        without_error_df = deepcopy(doc_df[doc_df['error'].isnull()])
        if without_error_df.empty:
            return with_error_df

        without_error_df['language'] = without_error_df.apply(lambda row: detect_language(row[content_column_name]), axis=1)
        # strip doc_df['language']== None and set doc_df['error'] to 'Cannot detect language' accordingly
        tmp_without_error_df = deepcopy(without_error_df[without_error_df['language'].notnull()])
        tmp_with_error_df = deepcopy(without_error_df[without_error_df['language'].isnull()])
        tmp_with_error_df['error'] = 'Miner:Cannot detect language'

        with_error_df['language'] = None
        if not tmp_with_error_df.empty:
            with_error_df = pd.concat([with_error_df, tmp_with_error_df], axis=0)
        without_error_df = tmp_without_error_df

        without_error_df['stripped'] = without_error_df.apply(lambda row: normalize(row[content_column_name]), axis=1)
        tmp_without_error_df = deepcopy(without_error_df[without_error_df['stripped'].notnull()])
        tmp_with_error_df = deepcopy(without_error_df[without_error_df['stripped'].isnull()])
        tmp_with_error_df['error'] = 'Miner:Cannot strip'

        with_error_df['stripped'] = None
        if not tmp_with_error_df.empty:
            with_error_df = pd.concat([with_error_df, tmp_with_error_df], axis=0)
        without_error_df = tmp_without_error_df

        without_error_df['lemmatized'] = without_error_df.apply(lambda row: self.lemmatize(row['stripped']), axis=1)
        tmp_without_error_df = deepcopy(without_error_df[without_error_df['lemmatized'].notnull()])
        tmp_with_error_df = deepcopy(without_error_df[without_error_df['lemmatized'].isnull()])
        tmp_with_error_df['error'] = 'Miner:Cannot lemmatize'

        with_error_df['lemmatized'] = None
        if not tmp_with_error_df.empty:
            with_error_df = pd.concat([with_error_df, tmp_with_error_df], axis=0)
        without_error_df = tmp_without_error_df

        without_error_df['without_stop_words'] = without_error_df.apply(lambda row: self.delete_stop_words(row['language'],row['lemmatized']), axis=1)
        tmp_without_error_df = deepcopy(without_error_df[without_error_df['without_stop_words'].notnull()])
        tmp_with_error_df = deepcopy(without_error_df[without_error_df['without_stop_words'].isnull()])
        tmp_with_error_df['error'] = 'Miner:Cannot delete stop word'

        with_error_df['without_stop_words'] = None
        if not tmp_with_error_df.empty:
            with_error_df = pd.concat([with_error_df, tmp_with_error_df], axis=0)
        without_error_df = tmp_without_error_df

        if with_error_df.empty:
            return without_error_df.sort_values('original_order').drop('original_order', axis=1)
        else:
            return pd.concat([with_error_df, without_error_df], axis=0).sort_values('original_order').drop('original_order', axis=1)


# def test_mine():
#     miner = Miner()

# def test_www_domain_regex():
#     text = 'www.figsci.com'
#     #normalized = re.sub('(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', ' ', text)

# if __name__ == '__main__':
#     #test_mine()               ### fonctionne du premier coup... assez bluffant :)
#     test_www_domain_regex()
