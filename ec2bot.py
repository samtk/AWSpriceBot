from __future__ import print_function, unicode_literals
import random
import logging
import os


os.environ['NLTK_DATA'] = os.getcwd() + '/nltk_data'

from textblob import TextBlob
from config import FILTER_WORDS

import nltk

import re
import sys

#nltk.download('punkt')

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# start:example-hello.py
# Sentences we'll respond with if the user greeted us
GREETING_KEYWORDS = ("hello", "hi", "greetings", "sup", "what's up",)

GREETING_RESPONSES = ["'sup bro", "hey", "*nods*", "hey you get my snap?"]

LOCATION_KEY = ["us east", "eu west"]
KEY_WORDS = ["price", "ghz", "memory", "gib", "network"]

def check_for_greeting(sentence):
    """If any of the words in the user's input was a greeting, return a greeting response"""
    for word in sentence.words:
        if word.lower() in GREETING_KEYWORDS:
            return random.choice(GREETING_RESPONSES)
# start:example-none.py
# Sentences we'll respond with if we have no idea what the user just said
NONE_RESPONSES = [
    "uh whatever",
    "meet me at the foosball table, bro?",
    "code hard bro",
    "want to bro down and crush code?",
    "I'd like to add you to my professional network on LinkedIn",
    "Have you closed your seed round, dog?",
]
# end

# start:example-self.py
# If the user tries to tell us something about ourselves, use one of these responses
COMMENTS_ABOUT_SELF = [
    "You're just jealous",
    "I worked really hard on that",
    "My Klout score is {}".format(random.randint(100, 500)),
]
# end


class UnacceptableUtteranceException(Exception):
    """Raise this (uncaught) exception if the response was going to trigger our blacklist"""
    pass


def starts_with_vowel(word):
    """Check for pronoun compability -- 'a' vs. 'an'"""
    return True if word[0] in 'aeiou' else False


# start:example-pronoun.py
def find_pronoun(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    pronoun = None

    for word, part_of_speech in sent.pos_tags:
        # Disambiguate pronouns
        if part_of_speech == 'PRP' and word.lower() == 'you':
            pronoun = 'I'
        elif part_of_speech == 'PRP' and word == 'I':
            # If the user mentioned themselves, then they will definitely be the pronoun
            pronoun = 'You'
    return pronoun
# end

def find_verbs(sent):
    """Pick a candidate verb for the sentence."""
    verb = None
    pos = None
    verbs=[]
    for word, part_of_speech in sent.pos_tags:
        if part_of_speech.startswith('VB'):  # This is a verb
            verb = word
            pos = part_of_speech
            verbs.append({"verb":word,"pos":pos})
            break
    return verb, pos


def find_nouns(sent):
    """Given a sentence, find the best candidate noun."""
    noun = None
    nouns = []
    if not noun:
        for w, p in sent.pos_tags:
            if p == 'NN':  # This is a noun
                noun = w
                nouns.append(noun)
    if noun:
        logger.info("Found nouns: %s", nouns)
    return nouns

def find_adjectives(sent):
    """Given a sentence, find the best candidate adjective."""
    adj = None
    adjs = []
    for w, p in sent.pos_tags:
        if p == 'JJ':  # This is an adjective
            adj = w
            adjs.append(w)
    return adj



# start:example-construct-response.py
def construct_response(pronoun, noun, verb):
    """No special cases matched, so we're going to try to construct a full sentence that uses as much
    of the user's input as possible"""
    resp = []

    if pronoun:
        resp.append(pronoun)

    # We always respond in the present tense, and the pronoun will always either be a passthrough
    # from the user, or 'you' or 'I', in which case we might need to change the tense for some
    # irregular verbs.
    if verb:
        verb_word = verb[0]
        if verb_word in ('be', 'am', 'is', "'m"):  # This would be an excellent place to use lemmas!
            if pronoun.lower() == 'you':
                # The bot will always tell the person they aren't whatever they said they were
                resp.append("aren't really")
            else:
                resp.append(verb_word)
    if noun:
        pronoun = "an" if starts_with_vowel(noun) else "a"
        resp.append(pronoun + " " + noun)

    resp.append(random.choice(("tho", "bro", "lol", "bruh", "smh", "")))

    return " ".join(resp)
# end


# start:example-check-for-self.py
def check_for_comment_about_bot(pronoun, noun, adjective):
    """Check if the user's input was about the bot itself, in which case try to fashion a response
    that feels right based on their input. Returns the new best sentence, or None."""
    resp = None
    if pronoun == 'I' and (noun or adjective):
        if noun:
            if random.choice((True, False)):
                resp = random.choice(SELF_VERBS_WITH_NOUN_CAPS_PLURAL).format(**{'noun': noun.pluralize().capitalize()})
            else:
                resp = random.choice(SELF_VERBS_WITH_NOUN_LOWER).format(**{'noun': noun})
        else:
            resp = random.choice(SELF_VERBS_WITH_ADJECTIVE).format(**{'adjective': adjective})
    return resp

# Template for responses that include a direct noun which is indefinite/uncountable
SELF_VERBS_WITH_NOUN_CAPS_PLURAL = [
    "My last startup totally crushed the {noun} vertical",
    "Were you aware I was a serial entrepreneur in the {noun} sector?",
    "My startup is Uber for {noun}",
    "I really consider myself an expert on {noun}",
]

SELF_VERBS_WITH_NOUN_LOWER = [
    "Yeah but I know a lot about {noun}",
    "My bros always ask me about {noun}",
]

SELF_VERBS_WITH_ADJECTIVE = [
    "I'm personally building the {adjective} Economy",
    "I consider myself to be a {adjective}preneur",
]
# end

def preprocess_text(sentence):
    """Handle some weird edge cases in parsing, like 'i' needing to be capitalized
    to be correctly identified as a pronoun"""
    cleaned = []
    words = sentence.split(' ')
    for w in words:
        if w == 'i':
            w = 'I'
        if w == "i'm":
            w = "I'm"
        cleaned.append(w)

    return ' '.join(cleaned)

def get_nouns(parsed):
    nouns = []
    for sent in parsed.sentences:
        sentence = find_nouns(sent)
        nouns += sentence
    return nouns

def get_verbs(parsed):
    verbs = []
    for sent in parsed.sentences:
        sentence = find_verbs(sent)
        verbs += sentence
    return verbs
    
def get_adjectives(parsed):
    adjectives = []
    for sent in parsed.sentences:
        sentence = find_adjectives(sent)
        adjectives += sentence
    return adjectives

def get_best_lines(sentence):
    """
    Takes a list of words and searches a csv file for lines that are similar
    Returns the line/s from csv that have most words in common
    Also returns the number of words in common found
    """
    cleaned = preprocess_text(sentence)
    parsed = TextBlob(cleaned)
    words = parsed.split(" ")
    words = list(set(words))#remove dupe words
    
    bestlines = []
    blcount = 0
    
    priceflag = False
    pricequestion = has_asked_for_price(sentence)
    if pricequestion is not None:
        relationalop = get_relationalop_in_price_question(pricequestion)
        #print("the rel op " + relationalop + "\n")
        price =  get_number_in_price_question(pricequestion)
        priceflag = True
    
    try:
        fp = open('newtrim.csv', 'r')
        line = fp.readline()
        count = 0
        while line:
            split = " ".join(list(set(line.split(","))))
            for word in words:
                if(re.search(word.lower(), split.lower())):
                    count += 1
            if(count > blcount):
                blcount = count
                bestlines = [line]
            elif(count == blcount):
                bestlines.append(line)
            line = fp.readline()
            count = 0
    finally:
        fp.close()
    bl2 = []
    if(priceflag):
        for line in bestlines:
            if (compare_price(get_price_from_sentence(line),price,relationalop)):
                bl2.append(line)
        return bl2,blcount
    return bestlines,blcount

def is_number(s):
    """
    is the string value a digit
    """
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False

def has_asked_for_price(sentence):
    """
    Takes user input as param 
    Check whether user asked for price in input string, if so return that part of string
    """
    pattern = "price(\s)*([><=]|=[><=]|greater(\s)*(than)?|less(\s)*(than)?)(\s)*\$?(\d)+(\.(\d)+)?"
    match = re.search(pattern,sentence)
    if match is not None:
        return match.group(0)
    return (match)

def get_number_in_price_question(pricequestion):
    """
    Reads question and returns the mentioned price
    """
    number = []
    for i in range(len(pricequestion)-1,0,-1):
        if(is_number(pricequestion[i]) or pricequestion[i] == "."):
            number.insert(0,pricequestion[i])
        else:
            break
    return float("".join(number))

def get_relationalop_in_price_question(pricequestion):
    """
    Reads question and returns relational operator as string
    """
    operator = ""
    pattern = "(greater(\s)*(than)?)|(less(\s)*(than)?)"
    match = re.search(pattern, pricequestion.lower())
    if match is not None:
        return match.group(0)
    for i in range(0,len(pricequestion)):
        if(pricequestion[i] == "<" or pricequestion[i] == ">" or pricequestion[i] == "="):
            operator += pricequestion[i]
        
    return operator

def get_price_from_sentence(sentence):
    """
    Reads string and looks for price(number with dollar sign)
    returns price
    """
    pattern = "\$(\d)+(\.(\d)+)?"
    match = re.search(pattern,sentence)
    if match is not None:
        return float(match.group(0)[1:])
    return (match)

def compare_price(price1,price2,operator):
    operator = operator.strip()
    if(price1 is not None and price2 is not None):
        if (operator == "<" or operator == "less" or operator == "less than"):
            return price1 < price2 
        if (operator == ">" or operator == "greater" or operator == "greater than"):
            #print("this should print")
            return price1 > price2 
        if (operator == ">="):
            return price1 >= price2 
        if (operator == "<="):
            return price1 <= price2 
    return False  

def respond(sentence):
    bestlines,blcount = get_best_lines(sentence)
    
    
    
    i = 0
    for line in bestlines:
        print(line + "Number of keywords in common " + str(blcount) + "\n")
        i += 1
        if i > 3:
            print("Only showing top 5 results.")
            break
     
    
"""
def respond(sentence):
    #Parse the user's inbound sentence and find candidate terms that make up a best-fit response
    cleaned = preprocess_text(sentence)
    parsed = TextBlob(cleaned)
    print(parsed.tags)


    # Loop through all the sentences, if more than one. This will help extract the most relevant
    # response text even across multiple sentences (for example if there was no obvious direct noun
    # in one sentence
    pronoun, noun, adjective, verb = find_candidate_parts_of_speech(parsed)

    # If we said something about the bot and used some kind of direct noun, construct the
    # sentence around that, discarding the other candidates
    resp = check_for_comment_about_bot(pronoun, noun, adjective)

    # If we just greeted the bot, we'll use a return greeting
    if not resp:
        resp = check_for_greeting(parsed)

    if not resp:
        # If we didn't override the final sentence, try to construct a new one:
        if not pronoun:
            resp = random.choice(NONE_RESPONSES)
        elif pronoun == 'I' and not verb:
            resp = random.choice(COMMENTS_ABOUT_SELF)
        else:
            resp = construct_response(pronoun, noun, verb)

    # If we got through all that with nothing, use a random response
    if not resp:
        resp = random.choice(NONE_RESPONSES)

    logger.info("Returning phrase '%s'", resp)
    # Check that we're not going to say anything obviously offensive
    filter_response(resp)

    return resp


def find_candidate_parts_of_speech(parsed):
    #Given a parsed input, find the best pronoun, direct noun, adjective, and verb to match their input.
    #Returns a tuple of pronoun, noun, adjective, verb any of which may be None if there was no good match
    pronoun = None
    noun = None
    adjective = None
    verb = None
    for sent in parsed.sentences:
        pronoun = find_pronoun(sent)
        noun = find_noun(sent)
        adjective = find_adjective(sent)
        verb = find_verb(sent)
    logger.info("Pronoun=%s, noun=%s, adjective=%s, verb=%s", pronoun, noun, adjective, verb)
    return pronoun, noun, adjective, verb
    
    """
# end

# start:example-filter.py
def filter_response(resp):
    """Don't allow any words to match our filter list"""
    tokenized = resp.split(' ')
    for word in tokenized:
        if '@' in word or '#' in word or '!' in word:
            raise UnacceptableUtteranceException()
        for s in FILTER_WORDS:
            if word.lower().startswith(s):
                raise UnacceptableUtteranceException()
# end

def search_csv(file,word):
    file = open(file, "r")
    lines = []
    for line in file:
        if(re.search(word.lower(), line.lower())):
            lines.append(line.lower())
            #print(line,)
    return lines
    
def search_list(thelist, word):
    lines = []
    for line in thelist:
        if(re.search(word.lower(), line.lower())):
            lines.append(line.lower())
    return lines
    
if __name__ == '__main__':
    import sys
    # Usage:
    # python broize.py "I am an engineer"
    if (len(sys.argv) > 0):
        saying = sys.argv[1]
    else:
        saying = "How are you, brobot?"
    respond(saying)
     