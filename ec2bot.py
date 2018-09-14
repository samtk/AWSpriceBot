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

LOCATION_KEY = ["us east", "eu west"]
KEY_WORDS = ["price", "ghz", "memory", "gib", "network"]

def get_best_lines(sentence):
    """
    Takes a list of words and searches a csv file for lines that are similar
    Returns the line/s from csv that have most words in common
    Also returns the number of words in common found
    """
    
    bestlines = []
    blcount = 0
    
    priceflag = False
    pricequestion = has_asked_for_subject("price",sentence)
    if pricequestion is not None:
        relationalop = get_relationalop_in_question(pricequestion)
        price =  get_number_in_question(pricequestion)
        priceflag = True
    
    cpuflag = False
    cpuquestion = has_asked_for_subject("cpu",sentence)
    if cpuquestion is not None:
        cpuop = get_relationalop_in_question(cpuquestion)
        numcpu = get_number_in_question(cpuquestion)
        cpuflag = True
    
    parsed = TextBlob(sentence)
    words = parsed.split(" ")
    words = list(set(words))#remove dupe words
    if(priceflag):
        for w in pricequestion.split():
            words.remove(w)
    
    if(cpuflag):
        for w in cpuquestion.split():
            words.remove(w)
    
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
    if(cpuflag):
        for line in bestlines:
            if (compare_price(get_price_from_sentence(line),numcpu, cpuop)):
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

def has_asked_for_subject(subject, sentence):
    """
    Takes user input as param 
    Check whether user asked for price in input string, 
    if so return price compare part of string and string without price compare
    """
    pattern = subject + "(\s)*([><=]|=[><=]|greater(\s)*(than)?|less(\s)*(than)?)(\s)*\$?(\d)+(\.(\d)+)?"
    match = re.search(pattern,sentence)
    if match is not None:
        return match.group(0)
    return (match)

def get_number_in_question(question):
    """
    Reads question and returns the mentioned price
    """
    number = []
    for i in range(len(question)-1,0,-1):
        if(is_number(question[i]) or question[i] == "."):
            number.insert(0,question[i])
        else:
            break
    return float("".join(number))

def get_relationalop_in_question(question):
    """
    Reads question and returns relational operator as string
    """
    operator = ""
    pattern = "(greater(\s)*(than)?)|(less(\s)*(than)?)"
    match = re.search(pattern, question.lower())
    if match is not None:
        return match.group(0)
    for i in range(0,len(question)):
        if(question[i] == "<" or question[i] == ">" or question[i] == "="):
            operator += question[i]
        
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
    
def get_cpu_from_sentence(sentence):
    pass

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
        if (operator == "="):
            return price1 == price2 
    return False  

def respond(sentence):
    bestlines,blcount = get_best_lines(sentence)
    i = 0
    for line in bestlines:
        print(line + "Number of keywords in common " + str(blcount) + "\n")
        i += 1
        if i > 3:
            print("Only showing top 4 results.")
            break

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
     