#When expressing a causal relation, speakers and writers must do (at least) three things. They must (a) encode each of the two members of the relation in one form or another, (b) indicate the nature of their relationship in semantic and/or cohesive terms, and (c) present the members in a contextually appropriate sequence. Each of these tasks presents a varying number of options. For example, one or both of the causal members can be encoded as a phrase, as a dependent clause, or as an independent clause or sentence.

import sys

from paths import *
#adding all of the necessary paths
sys.path.append(home)
sys.path.append(core_nlp)
sys.path.append(semaphore)

from directories import *

from FNcases import *
from semaphore import run_semaphore, import_semaphore, semaphore

import matplotlib.pyplot as plt #for drawing graphs

try:
    if corenlp: pass
    #if we already have everything loaded we should not load a new version of the Stanford tools.
except:                  # corenlp is the python wrapper that wraps the Stanford Core NLP tools.
    from corenlp import StanfordCoreNLP

    corenlp_dir = "/home/johannes/Documents/causal-belief-catcher/corenlp-python/stanford-corenlp-full-2013-04-04"

    corenlp = StanfordCoreNLP(corenlp_dir)  # wait a few minutes...

#this runs the java program, semaphore and prints out a xml file of frame-net tags ...it puts all sentences together in one big and very ugly file:


def append_dependency_trees(nlp_core):
    import networkx as nx
    DG=[nx.DiGraph() for i in range(len(nlp_core))]

    [DG[i].add_edges_from([(tuple[1], tuple[2], {'label':tuple[0]}) for tuple in nlp_core[i]['dependencies']]) for i in range(len(nlp_core))]

    [nlp_core[i].update({"dependency-tree":DG[i]}) for i in range(len(nlp_core))]

def append_FN_graphs(nlp_core):
    import networkx as nx
    DG=[nx.DiGraph() for i in range(len(nlp_core))]

    [DG[i].add_edges_from([(tuple[1], tuple[0], {'word':tuple[2]}) for tuple in nlp_core[i]['fn_labels'] if (type(tuple[1])!=list and str(tuple[1])=='Target')]) for i in range(len(nlp_core))]

    [DG[i].add_edges_from([(tuple[0], tuple[1], {'word':tuple[2]}) for tuple in nlp_core[i]['fn_labels'] if (type(tuple[1])!=list and str(tuple[1])!='Target')]) for i in range(len(nlp_core))]

    [DG[i].add_edges_from([(tuple[0], tuple[j][0], {'word':tuple[j][1]}) for j in [1, 2] for tuple in nlp_core[i]['fn_labels'] if type(tuple[1])==list]) for i in range(len(nlp_core))]

    [nlp_core[i].update({"FN-tree":DG[i]}) for i in range(len(nlp_core))]

#before importing the semaphore data from the xml file, we should have a corenlp parser ready, because we will output a combined package of dependencies + syntactic parse + fn_labels:



def new_causal_arcs(parse_dict):
    cause=''; relation=''; effect=''
    arcs=relations=causes=cause_rel=caus_rel_effects=[]

    arcs += assistance(parse_dict, cause='', relation='', effect='')

    arcs += new_causation(parse_dict)

#All of the kinds of causation that could not be caught by the frame-net semantic role labels might not be lost, we might be able to catch them simply by using the Stanford dependencies and finding relations that are in some causal vocabulary.

    relations= (not arcs or []) and [word for word in parse_dict['text'].split() if word in set(['by'])]
    causes=get_cause('', parse_dict) if relations else []
        #
    cause_rel= ([(causes.pop(), rel) for rel in relations if causes] if relations else []) if causes and type(causes)==set else ([(causes, relations[0])] if relations and causes else [])

    caus_rel_effects=[(cause, rel, new_effects(rel, parse_dict)) for cause, rel in cause_rel] if cause_rel else []

    if caus_rel_effects:
        [arcs.append((cause, rel, list(effect)[i])) for cause, rel, effect in caus_rel_effects for i in range(len(effect)) if (cause, rel, list(effect)[i]) not in arcs]
    return arcs


def append_cause_relation_effects(nlp_core): #This is the function that does all of the work of causal parsing,
                                             #it is the heart of the program.
    import nltk
    stemmer = nltk.PorterStemmer()
    cause=''; relation=''; effect=''
    arcs=relations=causes=cause_rel=caus_rel_effects=[]

    for i in range(len(nlp_core)):
        tuples=[tuple for tuple in nlp_core[i]['fn_labels']]

        arcs=new_causal_arcs(nlp_core[i])
        if not arcs:
            import nltk
            exists_cause=False
            stemmer=nltk.PorterStemmer()
            for tuple in nlp_core[i]['dependencies']:
                if tuple[0]=='nsubj' and stemmer.stem(tuple[1]) in causal_words:
                    relation=stemmer.stem(tuple[1])
                    ptree=nltk.ParentedTree(nlp_core[i]['parsetree'])
                    for tup in nlp_core[i]['dependencies']:
                        if tup[0]=='conj_and' and stemmer.stem(tup[2])==relation:
                            cause  = wrap_effect(ptree, tup[1])
                            cause =  trim_cause(ptree, relation, cause)
                            exists_cause=True
                    if not exists_cause:
                        cause  = wrap_effect(ptree, tuple[2])
                        cause =  trim_cause(ptree, relation, cause)
                elif tuple[0]=='nsubj':
                    relation_finder=tuple[1]
                    for tup in nlp_core[i]['dependencies']:
                        if (tup[0]=='xcomp' and tup[1]==relation_finder and stemmer.stem(tup[2]) in causal_words):
                            relation= stemmer.stem(tup[2])
                            ptree=nltk.ParentedTree(nlp_core[i]['parsetree'])
                            cause   = wrap_effect(ptree, tuple[2])
                            cause =  trim_cause(ptree, relation, cause)
                if (cause and relation):
                    effects = get_effects(relation, parse_dict=nlp_core[i])
                    if effects:
                        number_effects=len(effects)
                        [arcs.append((c, r, e)) for c, r, e in zip([cause]*number_effects, [relation]*number_effects, effects) if (c, r, e) not in arcs]

                    elif (cause and relation and effect) and (cause, relation, effect) not in arcs:
                        arcs.append((cause, relation, effect))

        nlp_core[i]['Causal-Arcs']=arcs


def print_causal_arcs(nlp_core):                    #This function prints out all causal assertions in convenient form.
    for i in range(len(nlp_core)):
        arcs=nlp_core[i]['Causal-Arcs']
        str_arcs=[str(arc[0]) + '  ' + '/' + ' ' + eval_relation(arc, nlp_core[i]) + ' ' + '/' + '  ' + str(arc[2]) for arc in arcs]
        out_print= '  / AND /  '.join(str_arcs)
        print out_print


def try_to_negate(symb, relation, parse_dict):
    import nltk
    stemmer=nltk.PorterStemmer()
    for tup in parse_dict['dependencies']:
            if tup[0]=='neg' and stemmer.stem(tup[1])==relation:
                relation = 'ominus' if symb=='+' else 'oplus'

    if not relation in set(['ominus', 'oplus']):
        relation = symb

    return relation

def eval_relation(arc, parse_dict):                           #This function will probably be broken up
    import nltk                                                    #into cases, as was the add_causal_arcs function.
    stemmer=nltk.PorterStemmer()
    relation=arc[1]
    if relation in positive:
        symb = '+'
        relation=try_to_negate(symb, relation, parse_dict)

    elif relation in negative:
        symb = '-'
        relation=try_to_negate(symb, relation, parse_dict)

    elif non_zero_effect(arc, parse_dict):
        return 'm'

    elif is_zero_effect(relation, parse_dict):
        return '0'

    else:
        import nltk
        stemmer=nltk.PorterStemmer()
        for tup in parse_dict['dependencies']:
            if tup[0]=='prep_in' and stemmer.stem(tup[1])==relation:
                temp_var1=tup[2]
            elif tup[0]=='neg':
                temp_var2=tup[1]

            check1=check2=False

        for tup in parse_dict['fn_labels']:
            if str(tup[0])=='Expectation' and str(tup[1])=='Target' and str(tup[2])==temp_var2:
                check1=True
            elif str(tup[0])=='Expectation' and str(tup[1])=='Phenomenon' and str(tup[2])==temp_var1:
                check2=True

            if (check1 and check2):
                relation='a'

    return relation



#Below are some functions that would do great preprocessing work, before semaphore operates (right now, I'm not using these)
def make_coref_dict(parse_dict):
    coref_dict={}
    for item in parse_dict['coref']:
        for j, item2 in enumerate(item):
            coref_dict[str(item[j][0][0])] = str(item[j][1][0])
    return coref_dict

def substitute_coref(tree, parse_dict): #This function is concerned with cohesion. For multiple sentences the idea will be to recursively look in previous and downstream sentences to see whether 'he', 'she' or 'it' was coreferenced with a name there and then we can make a better guess as to what the name in the current phrase should be. Often people will say things such as "Bob went to the market and then he picked up the children from school. Next, he went to bring his children to their grand-parents. They are 97 and 84 years old and their names are Hary and Mary." What we want, for the sake of a consistent causal graph is to remold the sentences into "Bob went to the market and then Bob picked up Bob's children from school. Next, Bob went to bring Bob's children to Hary and Mary (keeping a record that Hary and Mary are Bob's children's grandparents as well as their ages)", we are still waiting to find the names of the children and if it is recorded somewhere where that connection is made, then "Bob's children" can be substituted with their names (keeping a record of their relationships to Bob).
    import re                                      #for a more complicated, later version.

    subst_dict=make_coref_dict(parse_dict)

    i=0
    while i <2: #Do it two times, because sometimes a substitution (such as 'his employees' necessitates a new substitution)
        for position in tree.treepositions():
            if tree[position] in subst_dict.keys():
 		new_parse_dict=eval(corenlp.parse(subst_dict[tree[position]]))
 		new_tree=new_parse_dict['sentences'][0]['parsetree']
 		t_new=nltk.Tree(new_tree)
 		tree[position]=t_new[0]

        i+=1


    return tree

def named_entity_tags(tree, word_dict):
    for t in tree.subtrees():
 	if ' '.join(t.leaves()) in word_dict.keys():
            if word_dict[' '.join(t.leaves())]['NamedEntityTag']!='O':
                t.node=word_dict[' '.join(t.leaves())]['NamedEntityTag']
    return tree
