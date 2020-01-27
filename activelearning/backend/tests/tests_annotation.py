from django.test import TestCase
from django.test import Client

from backend.models import Article, UserLabel
from backend.db_management import add_article_to_db
from backend.helpers import label_consensus
from backend.xml_parsing.postgre_to_xml import database_to_xml

import spacy
import json


""" The language model. """
nlp = spacy.load('fr_core_news_md')


""" The content and annotation of the first article. """
TEST_1 = {
    'input_xml': '<?xml version="1.0"?>\n'
                '<article>\n'
                '\t<titre>Le football</titre>\n'
                '\t<p>Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi. Du moins, c\'est ce '
                'que pense Serge Aurier. Il l\'affirme dans un interview avec L\'Equipe. Il pense que sa victoire en '
                'coupe du monde est plus importante que les victoires individuelles de lutin du FC Barcelone.</p>\n'
                '\t<p>Il ne pense pas que Messi pourra un jour gagner une coupe du monde. Mais Platini nous informe '
                'qu\'en fait c\'est lui "le meilleur joueur du monde". Et que "ça n\'a rien à voir avec son ego".</p>\n'
                '\t<p>Mais au final, c\'est vraiement Wayne Rooney, le meilleur joueur de tous les temps. C\'est '
                'indiscutable. Même Zlatan le dit: "Personne n\'est meilleur que Wayne".</p>\n'
                '</article>',
    'output_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Le football</titre>\n'
                  '\t<p><RS a="0">Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi</RS>. Du '
                  'moins, c\'est ce que pense <author a="0">Serge Aurier</author>. Il l\'affirme dans un interview '
                  'avec L\'Equipe. Il pense que <RS a="0">sa victoire en coupe du monde est plus importante que les '
                  'victoires individuelles de lutin du FC Barcelone</RS>.</p>\n'
                  '\t<p>Il ne pense pas que Messi pourra un jour gagner une coupe du monde. Mais <author a="1">Platini '
                  '</author>nous informe qu\'en fait <RS a="1">c\'est lui "le meilleur joueur du monde"</RS>. Et que '
                  '"<RS a="1">ça n\'a rien à voir avec son ego</RS>".</p>\n'
                  '\t<p>Mais au final, c\'est vraiement Wayne Rooney, le meilleur joueur de tous les temps. C\'est '
                  'indiscutable. Même <author a="2">Zlatan </author>le dit: "<RS a="2">Personne n\'est meilleur que '
                  'Wayne</RS>".</p>\n'
                  '</article>',
    'text': 'Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi. Du moins, c\'est ce que pense '
            'Serge Aurier. Il l\'affirme dans un interview avec L\'Equipe. Il pense que sa victoire en coupe du monde '
            'est plus importante que les victoires individuelles de lutin du FC Barcelone. Il ne pense pas que Messi '
            'pourra un jour gagner une coupe du monde. Mais Platini nous informe qu\'en fait c\'est lui "le meilleur '
            'joueur du monde". Et que "ça n\'a rien à voir avec son ego". Mais au final, c\'est vraiement Wayne Rooney,'
            ' le meilleur joueur de tous les temps. C\'est indiscutable. Même Zlatan le dit: "Personne n\'est meilleur'
            'que Wayne".',
    'tokens': [
        ['Le ', 'fameux ', 'joueur ', 'de ', 'football ', 'Diego ', 'Maradona ', 'est ', 'meilleur ', 'que ', 'Lionel ',
         'Messi', '. '],
        ['Du ', 'moins', ', ', "c'", 'est ', 'ce ', 'que ', 'pense ', 'Serge ', 'Aurier', '. '],
        ['Il ', "l'", 'affirme ', 'dans ', 'un ', 'interview ', 'avec ', "L'", 'Equipe', '. '],
        ['Il ', 'pense ', 'que ', 'sa ', 'victoire ', 'en ', 'coupe ', 'du ', 'monde ', 'est ', 'plus ', 'importante ',
         'que ', 'les ', 'victoires ', 'individuelles ', 'de ', 'lutin ', 'du ', 'FC ', 'Barcelone', '.'],
        ['Il ', 'ne ', 'pense ', 'pas ', 'que ', 'Messi ', 'pourra ', 'un ', 'jour ', 'gagner ', 'une ', 'coupe ',
         'du ', 'monde', '. '],
        ['Mais ', 'Platini ', 'nous ', 'informe ', "qu'", 'en ', 'fait ', "c'", 'est ', 'lui ', '"', 'le ', 'meilleur ',
         'joueur ', 'du ', 'monde', '"', '. '],
        ['Et ', 'que ', '"', 'ça ', "n'", 'a ', 'rien ', 'à ', 'voir ', 'avec ', 'son ', 'ego', '"', '.'],
        ['Mais ', 'au ', 'final', ', ', "c'", 'est ', 'vraiement ', 'Wayne ', 'Rooney', ', ', 'le ', 'meilleur ',
         'joueur ', 'de ', 'tous ', 'les ', 'temps', '. '],
        ["C'", 'est ', 'indiscutable', '. '],
        ['Même ', 'Zlatan ', 'le ', 'dit', ': ', '"', 'Personne ', "n'", 'est ', 'meilleur ', 'que ', 'Wayne', '"', '.']
    ],
    'in_quotes': [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    ],
    'labels': [
        # 0 - 12
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 13 - 23
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 24 - 33
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 34 - 55
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 56 - 70
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 71 - 88
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 89 - 102
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 103 - 120
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 121 - 124
        [0, 0, 0, 0],
        # 125 - 138
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    ],
    'authors': [
        [21, 22],
        [],
        [],
        [21, 22],
        [],
        [72],
        [72],
        [],
        [],
        [126],
    ],
    'sentence_ends': [12, 23, 33, 55, 70, 88, 102, 120, 124, 138],
    'paragraph_ends': [3, 6, 9],
}


""" The content and annotation of the second article. """
TEST_2 = {
    'input_xml': '<?xml version="1.0"?>\n'
                '<article>\n'
                '\t<titre>Article sans sens.</titre>\n'
                '\t<p>Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "est bien '
                'plus importante que la véracité des dires", répond Pierre. Michel Schmid ne dit rien. Il criait '
                'pourtant plus tôt que "rien n\'est mieux qu\'un code bien commenté".</p>\n'
                '\t<p>Alain est d\'un avis différent. Pour lui, les tests sont la partie la plus importante du code. Il'
                ' pense que c\'est plus important que le reste.</p>\n'
                '</article>',
    'output_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Article sans sens.</titre>\n'
                  '\t<p>Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "est bien '
                'plus importante que la véracité des dires", répond Pierre. Michel Schmid ne dit rien. Il criait '
                'pourtant plus tôt que "rien n\'est mieux qu\'un code bien commenté".</p>\n'
                '\t<p>Alain est d\'un avis différent. Pour lui, les tests sont la partie la plus importante du code. Il'
                ' pense que c\'est plus important que le reste.</p>\n'
                '</article>',
    'text': 'Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "est bien plus '
            'importante que la véracité des dires", répond Pierre. Michel Schmid ne dit rien. Il criait pourtant plus '
            'tôt que "rien n\'est mieux qu\'un code bien commenté". Alain est d\'un avis différent. Pour lui, les tests'
            ' sont la partie la plus importante du code. Il pense que c\'est plus important que le reste.',
    'tokens': [
        ['Cet ', 'article ', 'est ', 'utilisé ', 'pour ', 'tester ', "l'", 'implémentation ', 'du ', 'gender ',
         'tracker', '. '],
        ['Une ', 'citation ', '"', 'est ', 'bien ', 'plus ', 'importante ', 'que ', 'la ', 'véracité ', 'des ', 'dires',
         '"', ', ', 'répond ', 'Pierre', '. '],
        ['Michel ', 'Schmid ', 'ne ', 'dit ', 'rien', '. '],
        ['Il ', 'criait ', 'pourtant ', 'plus ', 'tôt ', 'que ', '"', 'rien ', "n'", 'est ', 'mieux ', "qu'", 'un ',
         'code ', 'bien ', 'commenté', '"', '.'],
        ['Alain ', 'est ', "d'", 'un ', 'avis ', 'différent', '. '],
        ['Pour ', 'lui', ', ', 'les ', 'tests ', 'sont ', 'la ', 'partie ', 'la ', 'plus ', 'importante ', 'du ',
         'code', '. '],
        ['Il ', 'pense ', 'que ', "c'", 'est ', 'plus ', 'important ', 'que ', 'le ', 'reste', '.']
    ],
    'in_quotes': [
        # 0 - 11
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 12 - 28
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        # 29 - 34
        [0, 0, 0, 0, 0, 0],
        # 35 - 52
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 53 - 59
        [0, 0, 0, 0, 0, 0, 0],
        # 60 - 73
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 74 - 84
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'labels': [
        # 0 - 11
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 12 - 28
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        # 29 - 34
        [0, 0, 0, 0, 0, 0],
        # 35 - 52
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 53 - 59
        [0, 0, 0, 0, 0, 0, 0],
        # 60 - 73
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 74 - 84
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0],
    ],
    'authors': [
        [],
        [27],
        [],
        [29, 30],
        [],
        [53],
        [53]
    ],
    'sentence_ends': [11, 28, 34, 52, 59, 73, 84],
    'paragraph_ends': [3, 6],

}


def load_new_task(test_class, client):
    """
    Loads a new sentence from the database.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :return: int, int, list(int), list(string), string.
        * The unique session id of the user
        * The id of the article from which the task is loaded.
        * The list of sentences to annotate.
        * The list of tokens in these sentences.
        * One of {sentence, paragraph, None, error}. The task to perform
    """
    response = client.get('/api/loadContent/')
    user_id = client.session['id']
    data = json.loads(response.content)
    keys = list(data)
    test_class.assertEquals(len(keys), 4)
    test_class.assertTrue('article_id' in keys)
    test_class.assertTrue('sentence_id' in keys)
    test_class.assertTrue('data' in keys)
    test_class.assertTrue('task' in keys)
    article_id = data['article_id']
    sentence_ids = data['sentence_id']
    text = data['data']
    task = data['task']
    return user_id, article_id, sentence_ids, text, task


def submit_task(test_class, client, article_id, sentence_ids, first_sentence, last_sentence, tags, authors):
    """
    Submits the user labels with the given parameters and checks that they are correctly saved to the database.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param sentence_ids: list(int)
        The ids of the sentences for which the annotation was the task.
    :param first_sentence: int
        The smallest id of a sentence loaded by the user. Equal to sentence_id[0] if and only if the user didn't load
        any text above, otherwise smaller than sentence_id[0].
    :param last_sentence: int
        The largest id of a sentence loaded by the user. Equal to sentence_id[-1] if and only if the user didn't load
        any text below, otherwise larger than sentence_id[-1].
    :param tags: list(int)
        The labels the user gave to each token.
    :param authors: list(int)
        The indices of tokens that are the author of the quote, if there was one.
    """
    data = {
        'article_id': article_id,
        'sentence_id': sentence_ids,
        'first_sentence': first_sentence,
        'last_sentence': last_sentence,
        'tags': tags,
        'authors': authors,
    }
    response = client.post('/api/submitTags/', data, content_type='application/json')
    data = json.loads(response.content)
    keys = list(data)
    test_class.assertEquals(len(keys), 1)
    test_class.assertTrue('success' in keys)
    test_class.assertTrue(data['success'])


def parse_extra_load(test_class, response):
    """
    Checks that the response from a load of extra text is in the correct format and extracts information from it.

    :param test_class: django.test.TestCase
        The test class.
    :param response: django.http.JsonResponse
        The response from the backend.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = json.loads(response.content)
    keys = list(data)
    test_class.assertEquals(len(keys), 3)
    test_class.assertTrue('data' in keys)
    test_class.assertTrue('first_sentence' in keys)
    test_class.assertTrue('last_sentence' in keys)
    text = data['data']
    first_sentence = data['first_sentence']
    last_sentence = data['last_sentence']
    return text, first_sentence, last_sentence


def load_above(test_class, client, article_id, first_sentence):
    """
    Loads the paragraph above the sentence with index first_sentence. If first_sentence is the first sentence in a
    paragraph, loads all the sentences in the paragraph above it. If it isn't, loads the remaining sentences in that
    paragraph.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param first_sentence: int.
        The index of the sentence above which we want the content.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = {
        'article_id': article_id,
        'first_sentence': first_sentence,
    }
    response = client.get('/api/loadAbove/', data, content_type='application/json')
    return parse_extra_load(test_class, response)


def load_below(test_class, client, article_id, last_sentence):
    """
    Loads the paragraph below the sentence with index last_sentence. If last_sentence is the last sentence in a
    paragraph, loads all the sentences in the paragraph below it. If it isn't, loads the remaining sentences in that
    paragraph.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param last_sentence: int.
        The index of the sentence below which we want the content.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = {
        'article_id': article_id,
        'last_sentence': last_sentence,
    }
    response = client.get('/api/loadBelow/', data, content_type='application/json')
    return parse_extra_load(test_class, response)


def relative_author_positions(authors, first_sentence_id, sentence_ends):
    """
    Computes the relative index of authors when given their index in the full document.

    :param authors: list(int)
        The indices of the authors in the full document.
    :param first_sentence_id: int
        The index of the first sentence loaded by the user.
    :param sentence_ends: list(int)
        The index of the last token of each sentence.
    :return: list(int)
        The index of the author tokens with respect to the first token in the loaded text.
    """
    first_token_index = 0
    if first_sentence_id > 0:
        first_token_index = sentence_ends[first_sentence_id - 1] + 1
    relative_authors = []
    for a in authors:
        relative_authors.append(a - first_token_index)
    return relative_authors


class SingleUserTestCase(TestCase):
    """ Case where a single user is annotating sentences """

    def setUp(self):
        # Add an article to the database
        self.a1 = add_article_to_db('../data/test_article_1.xml', nlp)
        self.a2 = add_article_to_db('../data/test_article_2.xml', nlp)

    def test_0_loading(self):
        """
        Test that the XML files are correctly loaded and stored in the database.
        """
        def check_article(article, name, data):
            self.assertEquals(article.name, name)
            self.assertEquals(article.text, data['input_xml'])
            self.assertEquals(article.tokens['tokens'], [token for sentence_tokens in data['tokens']
                                                         for token in sentence_tokens])
            self.assertEquals(article.sentences['sentences'], data['sentence_ends'])
            self.assertEquals(article.paragraphs['paragraphs'], data['paragraph_ends'])
            self.assertEquals(article.label_counts['label_counts'], len(data['sentence_ends']) * [0])
            self.assertEquals(article.label_counts['min_label_counts'], 0)
            self.assertEquals(article.label_overlap['label_overlap'], len(data['sentence_ends']) * [0])
            self.assertEquals(article.in_quotes['in_quotes'], [in_quote for sentence_in_quote in data['in_quotes']
                                                               for in_quote in sentence_in_quote])
            self.assertEquals(article.confidence['confidence'], len(data['sentence_ends']) * [0])
            self.assertEquals(article.confidence['min_confidence'], 0)
            self.assertEquals(article.admin_article, False)

        check_article(self.a1, 'Le football', TEST_1)
        check_article(self.a2, 'Article sans sens.', TEST_2)

    def test_1_trivial(self):
        """
        Test where the user simply annotates all sentences as text that isn't reported, without ever loading extra text.
        """
        # Define a new client
        c = Client()
        test_1_sentences = 10
        test_2_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id

        def annotate_simple(sentence_index_range, true_values):
            for s_id in sentence_index_range:
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, [s_id])
                self.assertEquals(text, true_values['tokens'][s_id])
                self.assertEquals(task, 'sentence')
                submit_task(self, c, article_id, sentence_ids, s_id, s_id, len(text) * [0], [])

        # The first article should be loaded first as it has a smaller index
        annotate_simple(range(test_1_sentences), TEST_1)
        annotate_simple(range(test_2_sentences), TEST_2)

        # Check that no more sentences are left to annotate.
        user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
        self.assertEquals(article_id, -1)
        self.assertEquals(sentence_ids, [])
        self.assertEquals(text, [])
        self.assertEquals(task, 'None')

    def test_2_real_annotations(self):
        """
        Test where a single user annotates all sentences correctly, looking up in the text when needed.
        """
        # Define a new client
        c = Client()
        test_1_sentences = 10
        test_2_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_1['look_above_index'] = [3, 6]
        TEST_1['look_below_index'] = [0]
        TEST_2['id'] = self.a2.id
        TEST_2['look_above_index'] = [3, 5, 6]
        TEST_2['look_below_index'] = []

        def annotate_true(sentence_index_range, true_values):
            for s_id in sentence_index_range:
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, [s_id])
                self.assertEquals(text, true_values['tokens'][s_id])
                self.assertEquals(task, 'sentence')

                labels = true_values['labels'][s_id]

                first_sentence = sentence_ids[0]
                last_sentence = sentence_ids[0]

                if s_id in true_values['look_above_index']:
                    extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                    extra_labels = []
                    for id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][id]) * [0]
                    first_sentence = min(first_sentence, first_extra)
                    labels = extra_labels + labels

                if s_id in true_values['look_below_index']:
                    extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                    extra_labels = []
                    for id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][id]) * [0]
                    labels = labels + extra_labels
                    last_sentence = max(last_sentence, last_extra)

                authors = true_values['authors'][s_id]
                authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'])
                submit_task(self, c, article_id, sentence_ids, first_sentence, last_sentence, labels, authors)

        # The first article should be loaded first as it has a smaller index
        annotate_true(range(test_1_sentences), TEST_1)
        annotate_true(range(test_2_sentences), TEST_2)

        # Check that no more sentences are left to annotate.
        user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
        self.assertEquals(article_id, -1)
        self.assertEquals(sentence_ids, [])
        self.assertEquals(text, [])
        self.assertEquals(task, 'None')

        # Check that the output file is the expected output file

        # Don't need this yet as their is single author
        # labels, authors, consensus = label_consensus(labels, authors)

        labels = []
        authors = []

        for s_id in range(10):
            sentence_labels = UserLabel.objects.filter(article=self.a1, sentence_index=s_id)
            labels.append([label.labels['labels'] for label in sentence_labels][0])
            authors.append([label.author_index['author_index'] for label in sentence_labels][0])

        xml_string_1 = database_to_xml(self.a1, labels, authors)
        self.assertEquals(xml_string_1, TEST_1['output_xml'])
