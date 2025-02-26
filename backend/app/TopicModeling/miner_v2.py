import nltk
import pandas as pd
from functools import lru_cache
import langdetect
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
# from nltk.stem.snowball import FrenchStemmer, DutchStemmer
from typing import Optional

URL_PATTERN = re.compile(r'(?:http(?:s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+')
NORMALIZE_PATTERNS = [
    (re.compile(r'\W'), ' '),
    (re.compile(r'\d'), ' '),
    (re.compile(r' +'), ' ')
]

@lru_cache(maxsize=1000)
def detect_language(text: str) -> Optional[str]:
    """Cache language detection results for performance"""
    try:
        res = langdetect.detect_langs(text)
        return next((item.lang.upper() for item in res if item.lang in ("fr", "en")), None)
    except Exception as e:
        print(f'Miner.detect_language: {str(e)}')
        return None

@lru_cache(maxsize=1000)
def substitute_url(text: str, substituted_url: str = 'URL') -> str:
    """Cache URL substitution results"""
    return URL_PATTERN.sub(substituted_url, text)

def normalize(text: str) -> str:
    """Optimize text normalization with pre-compiled patterns"""
    try:
        normalized = substitute_url(text, ' ')
        for pattern, replacement in NORMALIZE_PATTERNS:
            normalized = pattern.sub(replacement, normalized)
        return normalized.lower().strip()
    except Exception as e:
        print(f'normalize: {str(e)}')
        return ''

class Miner:
    def __init__(self):
        for resource in ['wordnet', 'stopwords']:
            try:
                nltk.data.find(f'corpora/{resource}')
            except LookupError:
                nltk.download(resource, quiet=True)

        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = {
            'EN': set(stopwords.words('english')),
            'FR': set(stopwords.words('french'))
        }
        
        self.word_split = re.compile(r'\s+')

    @lru_cache(maxsize=1000)
    def lemmatize(self, text: str) -> str:
        """Cache lemmatisation results"""
        return ' '.join(self.lemmatizer.lemmatize(word) for word in self.word_split.split(text))

    def delete_stop_words(self, language: str, text: str) -> str:
        """Optimize stop words removal with sets"""
        if language not in self.stopwords:
            return text
        words = set(self.word_split.split(text)) - self.stopwords[language]
        return ' '.join(words)

    def mine(self, doc_df: pd.DataFrame, content_column_name: str = 'content') -> pd.DataFrame:
        """Optimize mining process with vectorized operations"""
        result_df = doc_df.copy()
        
        mask = result_df['error'].isnull()
        valid_docs = result_df[mask]
        
        if valid_docs.empty:
            return result_df
        
        new_columns = ['language', 'stripped', 'lemmatized', 'without_stop_words']
        for col in new_columns:
            if col not in result_df.columns:
                result_df[col] = None

        result_df.loc[mask, 'language'] = valid_docs[content_column_name].apply(detect_language)
        lang_mask = result_df['language'].notnull()
        
        result_df.loc[mask & lang_mask, 'stripped'] = (
            valid_docs[content_column_name][lang_mask].apply(normalize)
        )
        strip_mask = result_df['stripped'].notnull()
        
        result_df.loc[mask & lang_mask & strip_mask, 'lemmatized'] = (
            result_df['stripped'][mask & lang_mask & strip_mask].apply(self.lemmatize)
        )
        lem_mask = result_df['lemmatized'].notnull()
        
        result_df.loc[mask & lang_mask & strip_mask & lem_mask, 'without_stop_words'] = (
            result_df[mask & lang_mask & strip_mask & lem_mask].apply(
                lambda row: self.delete_stop_words(row['language'], row['lemmatized']),
                axis=1
            )
        )

        result_df.loc[mask & ~lang_mask, 'error'] = 'Miner:Cannot detect language'
        result_df.loc[mask & lang_mask & ~strip_mask, 'error'] = 'Miner:Cannot strip'
        result_df.loc[mask & lang_mask & strip_mask & ~lem_mask, 'error'] = 'Miner:Cannot lemmatize'

        print(result_df.columns)
        
        return result_df