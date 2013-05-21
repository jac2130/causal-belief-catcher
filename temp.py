import sys, os, inspect
import numpy as np
import nltk, nltk.data

from paths import *
#adding all of the necessary paths
sys.path.append(home)
sys.path.append(core_nlp)
sys.path.append(semaphore)

from corenlp import StanfordCoreNLP
from collections import OrderedDict
from semaphore import clean_raw_text
corenlp_dir = core_nlp + "/stanford-corenlp-full-2013-04-04"

sys.path.append(corenlp_dir)

os.chdir(home)

pronouns=set(['it', 'its', 'he', 'him', 'his', 'she', 'her', 'hers','they', 'theirs','them', 'their'])

poss=set(['its', 'his', 'her', 'theirs', 'hers'])
#Note that 'that' and 'this' are different in that they will not be nested and thus they don't have to be considered separetely.

try:
    if corenlp: pass
    #if we already have everything loaded we should not load a new version of the Stanford tools.
except:                  # corenlp is the python wrapper that wraps the Stanford Core NLP tools.
    from corenlp import StanfordCoreNLP

    corenlp = StanfordCoreNLP(corenlp_dir)  # wait a few minutes...


def clean_text(inputs='files/raw_text/new_sample.txt', outputs='files/clean_text/new_sample_clean.txt', keep_text=False):

    with open(inputs, 'r') as f:
        text=f.read()

        clean_raw_text(text, file_name=outputs)

    if keep_text:
        with open(outputs, 'r') as f:
            text=f.read()

            return text
    else:
        return ''

def load_parses():
    clean_text()
    parses=eval(corenlp.parse())
    return parses

#Add a None tag to every coreference. I will manually add True to those entities that I want to use as replacement for all other mentionings. I will then (once I have a large data set) use feature based machine learning to automate this tagging procedure.


def intersection(set1, set2=pronouns):
    if set1.intersection(set2):
        return True
    else:
        return False

def replace(parse_dict,CoRefGraph,j, pro_nouns=True):
    import nltk

    text='' #this will be populated by this program
    coreffs=CoRefGraph[j]
    root=parse_dict['sentences'][j]['text']

    word_list=nltk.word_tokenize(root)

    #The variable, offset, is used to place a replacement mentioning into the right place in the wordlist.
    #This is also the reason why I import numpy (so that this offset can be added to both coordinates of an entity simultaniously, Matlab style)

    offset=len(word_list)
    import numpy as np

    keys=set([key for key in coreffs])

    while keys:
        key=keys.pop()
        key_sent=parse_dict['sentences'][key]['text']

        for i in range(len(coreffs[key])):
            term1, term2=coreffs[key][i]['coref'].split(' --> ')

            #we are always reducing the length of the entity to one (one string)
                #and thus, the offset will always be calculated as follows:


            coords1, coords2= np.array(coreffs[key][i]['coords'])
            coords1-=offset
            c1, c2 =np.array(coreffs[key][i]['coords'])
            if ' '.join(word_list[coords1[0]:coords1[1]]).strip('[.,!?]')!=term1:
                continue


            #coreferences that include words included in other coreferences are not to change the text (for our purposes they are mistakes):

            if set(term1.lower().split()).intersection(set(term2.lower().split())): continue

            elif pro_nouns and term1.lower() in pronouns:

                word_list[coords1[0]:coords1[1]]=[term2 + " 's"] if term1.lower() in poss else [term2]

            #here is where we use the offset (when we are not changing pronouns, which always have length one)

            elif not pro_nouns:

                word_list[coords1[0]:coords1[1]]=[term2 + " 's"] if term1.lower()[-2:]=="'s" else [term2]

                offset +=offset-len(word_list)




    return ' '.join(word_list) if ' '.join(word_list)[-1] in set(['.', '?', '!']) else ' '.join(word_list) + '.'

def save_data(data):
    data_str=str(data)
    store_data= home + '/coref-data'
    with open(store_data + '/' + 'data.txt', 'w') as f:
        f.write(data_str)

def load_data():
    store_data= home + '/coref-data'
    with open(store_data + '/' + 'data.txt', 'r') as f:
        data=f.read()
        return eval(data) if data else []

def annotator(data, j=57, save=True):
    #first load the data

    import copy
    #making a copy of the coreferences in such a way that I can change the copy without changing the original
    data=copy.deepcopy(data)

    #Adding a "None" tag to every item in the data, to be manually replaces with "True" for those entities that should be representative.
    #This will be used for brute-force mashiene learning of the representative entity (the Stanford tools make a lot of mistakes,
    #and I think that I should be able to fix many of them)
    add_nones = lambda data: [[[element.append(None) for element in relation] for relation in datum] for datum in data]
    #garbage=add_nones(data)

    #not a very elegant solution, I know:
    try: del garbage
    except: print "nothing to delete"
    for i in range(len(data[j])):

        if data[j][i][0][0]== data[j][i][1][0]:
            continue
        answer=raw_input(" Should ITEM:  '%s' get a True value if Item '%s' is on the right side ? \n Answer yes or no or mistake \n If you want to end the session enter 'end': " % (data[j][i][0][0], data[j][i][1][0]))

        if answer=='yes':
            data[j][i][0][-1]=True
            pass
        elif answer=='no':
            data[j][i][0][-1]=None
            pass
        elif answer=='mistake':
            data[j][i][0][-1]='Mistake'
            pass
        elif answer=='end':
            break
        else: pass
    if save:
        save_data(data)


def resolve_corefs(parse_dict):

    coref=parse_dict['coref']

    data=load_data()
    #data must be as long as coref, for now (this could change later, when machine learning will do the work of labeling)
    assert len(data)==len(parse_dict['coref'])
    def find_representative(data=data[1]):
        for item in data:
            if item[0][-1] and item[0][-1]!='Mistake':
                #Something more must be done if there is a mistake label!
                return item[0][0]
            else: pass

    import networkx as nx

    CoRefGraph=nx.MultiDiGraph()

    [[CoRefGraph.add_edges_from([(datum[0][1], datum[1][1], {'coref': datum[0][0] +' --> '+ (find_representative(data[i]) if (datum[1][0]!=find_representative(data[i]) and find_representative(data[i])) else datum[1][0]), 'coords': [(datum[0][-2], datum[0][-1]), (datum[1][-2], datum[1][-1])]}) for datum in coref[i]]) for i in range(len(coref))]]

    keys=CoRefGraph.nodes()

    txt=' '.join([replace(parse_dict,CoRefGraph, j, pro_nouns=True) for j in keys])

    parse_dict=eval(corenlp.parse(txt))

    coref=parse_dict['coref']

    CoRefGraph=nx.MultiDiGraph()

    [[CoRefGraph.add_edges_from([(tup[0][1], tup[1][1], {'coref': tup[0][0] +' --> '+ tup[1][0], 'coords': [(tup[0][-2], tup[0][-1]), (tup[1][-2], tup[1][-1])]}) for tup in coref[i]]) for i in range(len(coref))]]

    keys=CoRefGraph.nodes()

    new_lines= [replace(parse_dict,CoRefGraph, j, pro_nouns=False) for j in keys]

    for line in new_lines:
        print line


def reparse(parse_dict):

    sents=[parse_dict['sentences'][i]['text'] for i in range(len(parse_dict['sentences']))]
    text=' '.join(sents)
    parse_dict=eval(corenlp.parse(text))
    return parse_dict


def default_labels(coref):

    [ent[i].insert(0,None) for entities in coref for ent in entities for i in range(len(ent)) if ent[i][0] not in set([None, True])]


def replace_item(new, ls, item=''):
    if item!='':
        index=ls.index(item)
        ls[index]=new

    else:
        [replace_item(new, ls, member) for member in ls if type(member)==str and new.lower() in member.lower()]

#And here is an example of how to use it to clean up the coreferences (I don't want 'the President or the Attorney General' to be replaced by 'the president', which is what would happen if I naively replaced every coreference with the target reference):

def clean_up_coref(coref, value='the President', j=1):
    [replace_item(value, ent[i]) for ent in coref[j] for i in range(len(ent))]

    [replace_item(True, ent[i], item=None) for ent in coref[j] for i in range(len(ent)) if None in ent[i] and ent[i][1]==value]

    if sum([ent[i][0] for ent in coref[j] for i in range(len(ent))])==len([ent[i] for ent in coref[j] for i in range(len(ent))]):
        del coref[j]


def change_coordinates(parse_dict, coref, j=1):

    #The following is a utility function, useful for replacement of the last two items in a list within list comprehension.

    def replace_last_two(ls, items):
        ls[-2]=items[0]
        ls[-1]=items[1]

    lens=[[len(parse_dict['sentences'][ent[i][2]]['text'].split()) for i in range(len(ent))] for ent in coref[j]]

    coords=[[(-l[i] + ent[i][-2], -l[i] + ent[i][-1]) for i in range(len(ent))] for ent, l in zip(coref[j], lens)]

    [replace_last_two(ent[i],c[i]) for i in range(len(ent)) for c, ent in zip(coords,coref[j])]







# Example for how to use the above function to tag the most informative coreferent:



#sentences=[parse_dict['sentences'][ent[i][2]]['text'].lower() for ent in coref[1] for i in range(len(ent))]


#coordinates=[(ent[i][-2], ent[i][-1]) for ent in coref[1] for i in range(len(ent))]


# I think that I don't need to change coordinates, as I just leave those entries alone that contain the coreferent. [replace_item((sentences[i].split().index(value[0]), sentences[i].split().index(value[-1])+1), coordinates, coordinates[i]) for i in range(len(sentences)) if ' '.join(value).lower() in sentences[i].lower()]


def resolve(text, coords, value='the President'):
    x, y = coords #the indices of where the coreferent is located (word indices)

    temp=text.split()

    temp[x : y]=[value]

    text=' '.join(temp)

    return text


def coref_replace(parse_dict, entities):

    value=set([entities[i][j][1] for i in range(len(entities)) for j in range(len(entities[i])) if entities[i][j][0]]).pop() if set([entities[i][j][1] for i in range(len(entities)) for j in range(len(entities[i])) if entities[i][j][0]]) else ''

#retrieves the most informative mentioning for a set of coreferences (hand selected or machine tagged).

    [parse_dict['sentences'][ent[i][2]].update({'text': resolve(parse_dict['sentences'][ent[i][2]]['text'], (ent[i][-2], ent[i][-1]), value)}) for ent in entities for i in range(len(ent)) if ent[i][0] !=True]


def main():

    default_labels(coref)
    clean_up_coref(coref, value='the President', j=1)

#do this oly once (this is dangerous, as it is right now):

    change_coordinates(parse_dict, coref, j=1)

    coref_replace(parse_dict, coref[1])
