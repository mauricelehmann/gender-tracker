from backend.models import Article, UserLabel
from django.core.exceptions import ObjectDoesNotExist
from backend.xml_parsing import process_article


##############################################################################################
# Save to Database
##############################################################################################


def paragraph_sentences(article, paragraph_index):
    """
    Finds the index of the first and last sentence, for a paragraph.

    :param article: Article.
        The article that contains the paragraph.
    :param paragraph_index: int.
        The index of the paragraph
    :return: (int, int).
        The indices of the first and last sentence in the paragraph.
    """
    par_ends = article.paragraphs['paragraphs']
    if paragraph_index == 0:
        first_sent = 0
    else:
        first_sent = par_ends[paragraph_index - 1] + 1
    last_sent = par_ends[paragraph_index]
    return first_sent, last_sent


def label_edges(article, paragraph_index, sentence_indices):
    """
    Finds the index of the first and last token and the index of the first and last sentence, for a list of sentences
    or a paragraph.

    :param article: Article.
        The article that contains the paragraph.
    :param paragraph_index: int.
        The index of the paragraph
    :param sentence_indices: list(int).
        The indices of the sentences. Empty list if the task is for an entire paragraph
    :return: dictionary:
        'token': (int, int). The indices of the first and last token in the paragraph.
        'sentence': (int, int). The indices of the first and last sentence in the paragraph.
    """
    sent_ends = article.sentences['sentences']
    if len(sentence_indices) == 0:
        first_sent, last_sent = paragraph_sentences(article, paragraph_index)
    else:
        first_sent = sentence_indices[0]
        last_sent = sentence_indices[-1]

    if first_sent == 0:
        first_token = 0
    else:
        first_token = sent_ends[first_sent - 1] + 1
    last_token = sent_ends[last_sent]
    return {
        'token': (first_token, last_token),
        'sentence': (first_sent, last_sent),
    }


##############################################################################################
# Save to Database
##############################################################################################


def add_article_to_db(path, nlp, admin_article=False):
    """
    Loads an article stored as an XML file, and adds it to the database after having processed it.

    :param path: string.
        The URL of the stored XML file
    :param nlp: spaCy.Language.
        The language model used to tokenize the text.
    :param admin_article: boolean.
        Can this article only be seen by admins.
    :return: Article.
        The article created
    """
    # Loading an xml file as a string
    with open(path, 'r') as file:
        article_text = file.read()
    
    # Process the file
    data = process_article(article_text, nlp)
    label_counts = len(data['s']) * [0]
    label_overlap = len(data['s']) * [0]
    confidence = len(data['s']) * [0]
    return Article.objects.create(
        text=article_text,
        people={'people': data['people']},
        tokens={'tokens': data['tokens']},
        paragraphs={'paragraphs': data['p']},
        sentences={'sentences': data['s']},
        label_counts={
            'label_counts': label_counts,
            'min_label_counts': 0
        },
        label_overlap={'label_overlap': label_overlap},
        in_quotes={'in_quotes': data['in_quotes']},
        confidence={
            'confidence': confidence,
            'min_confidence': 0,
        },
        admin_article=admin_article,
    )


def add_user_labels_to_db(article_id, session_id, labels, sentence_index, author_index, admin=False):
    """
    Adds a new set of user labels to the database for a given user annotation.

    :param article_id: int.
        The key of the article that was annotated
    :param session_id: int.
        The users session id
    :param labels: list(int).
        The labels the user created for the sentence
    :param sentence_index: int.
        The index of the sentence that was labelled in the article
    :param author_index: list(int).
        The indices of the tokens that are authors for this sentence
    :return: UserLabel.
        The UserLabel created
    """
    # Get the article to which these labels belong
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    label_counts = article.label_counts['label_counts']
    # Increase the label count for the given tokens in the Article database
    label_counts[sentence_index] += 1
    article.label_counts = {
            'label_counts': label_counts,
            'min_label_counts': min(label_counts)
        }
    article.save()

    return UserLabel.objects.create(
            article=article,
            session_id=session_id,
            labels={'labels': labels},
            sentence_index=sentence_index,
            author_index={'author_index': author_index},
            admin_label=admin,
    )


##############################################################################################
# Learning
##############################################################################################


def change_confidence(article_id, confidences):
    """
    Edits the Article database to reflect that the trained model has changed his confidence level that each sentence is
    or isn't reported speech.

    :param article_id: int.
        The id of the article to edit
    :param confidences: list(int).
        The confidence (in [0, 100]) the trained model has for each sentence.
    :return: int.
        The minimum confidence this article has in a sentence, or -1 if the article couldn't be added to the database.
    """
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    old_conf = article.confidence['confidence']
    min_conf = min(confidences)
    if len(confidences) == len(old_conf) and min_conf >= 0 and max(confidences) <= 100:
        new_conf = {
            'confidence': confidences,
            'min_confidence': min_conf,
        }
        article.confidence = new_conf
        article.save()
        return min_conf
    return None
