#!/usr/bin/env python

'''
UMLS Metathesaurus Dictionary Builder

+ Build dictionaries of UMLS semantic types
+ Expand dictionary using

(See umls/docs for list of UMLS Semantic Types)
'''
from __future__ import print_function

import re
import umls
import argparse
from sklearn.neighbors import *
from gensim.models.word2vec import Word2Vec

def term_expansion(fpath, terms, knn):
    '''Expand term list by creating list of nearest neighbors in provided embeddings
    representation. This is usually very noisy and there is a fuzzy distinction between
    semantic similarity and "relatedness". Bacteria names, for example, often neighbor
    diseases caused by those organisms.
    '''
    model = Word2Vec.load(fpath)
    model.init_sims()
    nbrs = NearestNeighbors(n_neighbors=knn+1, algorithm='ball_tree', metric='l2')
    nbrs.fit(model.syn0norm)
    
    expansion = []
    for phrase in terms:
        # space replaced with underscore in PMC/PubMed embeddings
        phrase = phrase.replace(" ","_")
        if phrase not in model.vocab:
            continue
        idx = model.vocab[phrase].index
        vec = model.syn0norm[idx]
        _,indices = nbrs.kneighbors(vec)
        neighbors = [model.index2word[j] for j in indices.flatten()]
        neighbors.remove(phrase)
        expansion += neighbors
    
    # transform words back to whitespace separators 
    return map(lambda x:x.replace("_"," "), expansion)
    

def main(args):
    
    meta = umls.Metathesaurus()
    norm = umls.MetaNorm(function=lambda x:x.lower())
    
    # Build dictionaries for a given a set of semantic types (i.e., entities)
    dictionary = []
    for sty in args.target:
        d = meta.dictionary(sty)
        dictionary += map(norm.normalize,d)
        
    dictionary = {t:1 for t in dictionary}

    # Use expanded 
    if args.embeddings:
        terms = term_expansion(args.embeddings, dictionary, args.knn)
        dictionary = {t:1 for t in terms if t not in dictionary and t.lower() not in dictionary}.keys()
    
    # remove terms that are just digits
    dictionary = [term for term in dictionary if not re.match("^\d+[.]*\d*$",term)]
    
    for term in sorted(dictionary,key=lambda x:len(x.split()),reverse=1):
        print(term.encode("utf-8"))
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--target", type=str, help="target(s) entity (REQUIRED) delitted by |", default=None)
    #parser.add_argument("-n","--ngram", type=int, help="max ngram length (default: any length)", default=None)
    parser.add_argument("-e","--embeddings", type=str, help="word embeddings (default: none)", default=None)
    parser.add_argument("-k","--knn", type=int, help="expand dictionary with k nearest neighbors (default: none)", default=None)   
    args = parser.parse_args()
    
    if not args.target:
        parser.print_help()
    else:
        args.target = args.target.split("|")
        main(args)