import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

class BOWMachine:

    '''
    This is a bag-of-words (BOW) machine.

    It converts free text into BOW format.

    It has two functions: convert_train_data and convert_online.
    Both of these take a list of strings and convert them into a BOW dataframe.
    The difference between them is that convert_train_data establishes
    the vocabulary, whereas convert_online uses the existing vocabulary.

    There is also a static method for converting BOWs from dataframes to arff files.
    '''

    def __init__(self):

        self.vocab = None

    def convert_train_data(self, strings):

        if self.vocab != None:
            raise ValueError('BOWMachine already has a vocabulary. ' + \
                'Try creating a new BOWMachine or using ' + \
                'convert_test_data instead.')

        vectorizer = CountVectorizer(
            lowercase=True, # convert to lowercase
            stop_words='english', # remove English stopwords
            binary=False, # use counts rather than binary inclusion
            max_df=0.99, # ignore tokens which occur more than 99% of documents
            min_df=0.01, # ignore tokens which occur in fewer than 1% documents
            token_pattern='[A-Za-z]+' # only use pure-alphabetic tokens (no numeric chars)
        )

        bow_obj = vectorizer.fit_transform(strings)
        self.vocab = vocab = vectorizer.get_feature_names()
        bow_df = pd.DataFrame(bow_obj.toarray(), columns=vocab)

        return bow_df

    def convert_online(self, strings):

        vectorizer = CountVectorizer(
            lowercase=True, # convert to lowercase
            binary=False, # use counts rather than binary inclusion
            vocabulary=self.vocab # use the existing vocabulary
        )

        bow_obj = vectorizer.transform(strings)
        self.vocab = vocab = vectorizer.get_feature_names()
        bow_df = pd.DataFrame(bow_obj.toarray(), columns=vocab)

        return bow_df
