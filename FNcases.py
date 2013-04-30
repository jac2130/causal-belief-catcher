
def wrap_effect(ptree, effect):                           #This function wraps up causes or effects
                                                          #when we only have a clue about a one-word componant
    assert len(effect.split())==1
    rel=''
    for sub in ptree.subtrees():
 	if sub.height()==2 and effect in sub.leaves():
            if sub.node in posClassLookup:
                effect=sub.parent()
		if effect.node in ("NP", 'PP'):

                    while effect.parent().node in ("NP", 'PP'):
                        effect=effect.parent()
                elif effect.node=="VP":
                    while effect.parent().node=="VP":
                        effect=effect.parent()


    effect= ' '.join(effect.leaves())

    if effect.split()[0] in set(['on', 'to', 'for']):
        effect=' '.join(effect.split()[1:])

    return effect

def trim_cause(ptree, relation, cause):
    #We have to deal with the case where the relation is in a subtree of the cause for cause wrapping
    rel=''
    import nltk
    stemmer=nltk.PorterStemmer()
    if relation in [stemmer.stem(word) for word in cause.split()]:
        index=[stemmer.stem(word) for word in cause.split()].index(relation)
        rel=cause.split()[index]
        for sub in ptree.subtrees():
            if sub.height()==2 and rel in sub.leaves():
                if sub.node in posClassLookup:
                    rel=sub.parent()
                    if rel.node not in ("NP", 'PP'):
                        while rel.parent().node in set(["VP", 'S', 'SBAR']):
                            rel=rel.parent()

    if rel:
        rel=' '.join(rel.leaves())
        cause=cause[:-len(rel)]
        cause_list=cause.split()
        if cause_list[-1] in set(['and']):
            cause=' '.join(cause_list[:-1])
        if cause.rstrip()[-1] in set(['.', ',', ';', '!', '?']):
            cause=cause.rstrip()[:-2]
    if cause.split()[0] in set(['of']):
        cause= ' '.join(cause.split()[1:])
    if cause.split()[-1] in cause.split()[:-1] and cause.split()[-2]==',':
        cause=' '.join(cause.split()[:-2])
    return cause

def receiving(parse_dict, receiver, to_do='', goal='', effect=''):                 #this function ca be called by other functions to get a full effect
    keys=parse_dict['FN-tree']["Target"].keys()
    if 'Receiving' in keys:
        to_do= ' ' + str(parse_dict['FN-tree']["Target"]['Receiving']['word'])
        if 'Recipient' in parse_dict['FN-tree']['Receiving'].keys():
            if str(parse_dict['FN-tree']['Receiving']['Recipient']['word'])==receiver:
                if 'Theme' in parse_dict['FN-tree']['Receiving'].keys():
                    goal= ' ' + str(parse_dict['FN-tree']['Receiving']['Theme']['word'])
                                                #when the effect includes people, or other entities receiving something
    if goal or to_do:
        effect=receiver + to_do + goal
        '''If some cause is affecting people's ability to do or receive something, the effect is:
           people's doing or receiving something
           Else, the effect is people's utility  ...I'm expecting to build up this function quite a bit over time ...I'm sure that as of now
           there are many unhandled cases here! '''

    else:
        if receiver.split()[0] in set(['on', 'for', 'to']):
            effect = 'Utility('+' '.join(receiver.split()[1:]) +')'
        else:
            effect = 'Utility('+ receiver +')'

    return effect


def assistance(parse_dict, cause='', relation='', effect=''):  #nlp_core[5] is dealt with in this function.
    import nltk
    stemmer=nltk.PorterStemmer()

    rel_eff=caus_rel =caus_rel_effects =arcs=[]

    keys=[key for key in parse_dict['FN-tree']['Target'].keys() if key in set(['Assistance'])]

    rel_eff=[(stemmer.stem(parse_dict['FN-tree']['Target'][key]['word']), receiving(parse_dict, parse_dict['FN-tree'][key][out]['word'])) for key in keys for out in parse_dict['FN-tree'][key].keys() if out in set(['Goal'])]

    ptree=nltk.ParentedTree(parse_dict['parsetree'])

    if rel_eff and not caus_rel:
        caus_rel_effects=[(trim_cause(ptree, rel, get_cause(rel, parse_dict)), rel, set([effect])) for rel, effect in rel_eff]

    if caus_rel_effects:
        [arcs.append((cause, rel, list(effect)[i])) for cause, rel, effect in caus_rel_effects for i in range(len(effect)) if (cause, rel, list(effect)[i]) not in arcs]

    return arcs  #if effect is not the same as the basic noun-wrapped effect that would result from passing through the end of the function that captures all rest-causation, then this might result in duplicate causal arcs, with slightly different effect variables!!!


#works_with_new_causation=[len(new_causation(parse_dict)) for parse_dict in nlp_core] #in order to see what is caught only by frame-net
                                                                                      #labels run this. '0' entries are unmatched.

def new_causation(parse_dict):  #When at least two out of three constituents of causation can be found using only semaphore.
    import nltk

    stemmer =nltk.PorterStemmer()
    caus_rel =caus_rel_effects =arcs=[]

    keys=[key for key in parse_dict['FN-tree']['Target'].keys() if key in InfluenceLookup]

    rel_eff=[(stemmer.stem(parse_dict['FN-tree']['Target'][k]['word']), parse_dict['FN-tree'][k][key]['word']) for k in keys for key in parse_dict['FN-tree'][k].keys() if key in set(['Effect', 'Patient', 'Attribute', 'Dependent_entity']) and parse_dict['FN-tree'][k][key]['word'].split()[0]!='by']        #unfortunately, sometimes semaphore confuses causes and effects when the voice is passive, we can correct for that:


    caus_rel =[(parse_dict['FN-tree'][k][key]['word'], stemmer.stem(parse_dict['FN-tree']['Target'][k]['word'])) for k in keys for key in parse_dict['FN-tree'][k].keys() if key in set(['Cause', 'Evaluee', 'Influencing_situation', 'Theme'])]

    if not rel_eff and [node for node in parse_dict['FN-tree'].nodes() if node in set(['Effect'])]:

        caus_rel =[(parse_dict['FN-tree'][k][key]['word'][3:], stemmer.stem(parse_dict['FN-tree']['Target'][k]['word'])) for k in keys for key in parse_dict['FN-tree'][k].keys() if key in set(['Effect']) and parse_dict['FN-tree'][k][key]['word'].split()[0]=='by']


        rel_eff =[(stemmer.stem(parse_dict['FN-tree']['Target'][k]['word']),
                parse_dict['FN-tree'][k][key]['word'])
               for k in keys for key in parse_dict['FN-tree'][k].keys() if key in set(['Cause', 'Evaluee', 'Influencing_situation', 'Theme'])]

    if caus_rel and rel_eff:
        caus_rel_effects=[(cause, rel, set([effect])) for cause, rel in caus_rel for r, effect in rel_eff if r==rel]


    elif not caus_rel:
        caus_rel =[(parse_dict['FN-tree'][k][key]['word'],
                stemmer.stem(parse_dict['FN-tree']['Target'][k]['word']))
               for k in keys for key in parse_dict['FN-tree'][k].keys() if key in set(['Cause', 'Evaluee', 'Influencing_situation', 'Theme'])]

    if rel_eff and not caus_rel:
        caus_rel_effects=[(get_cause(rel, parse_dict), rel, set([effect])) for rel, effect in rel_eff]

    if caus_rel and not caus_rel_effects and not rel_eff:
        caus_rel_effects=[(cause, rel, set(get_effects(rel, parse_dict))) for cause, rel in caus_rel]

    if caus_rel_effects:
        [arcs.append((cause, rel, list(effect)[i])) for cause, rel, effect in caus_rel_effects for i in range(len(effect)) if (cause, rel, list(effect)[i]) not in arcs]

    return arcs


def get_effects(relation, parse_dict):
    import nltk
    result=set(['dobj', 'prep_to', 'prep_for'])
    stemmer=nltk.PorterStemmer()
    eff=''
    next_eff=''
    effects=[]
    for tuple in parse_dict['dependencies']:
        if stemmer.stem(tuple[1])==relation:
            if tuple[0] in result:
                index=parse_dict['dependencies'].index(tuple)
                eff=tuple[2]
                ptree=nltk.ParentedTree(parse_dict['parsetree'])
                eff  =  wrap_effect(ptree, eff)
                if eff.split()[0] in set(['on', 'for', 'to']):
                    eff= ' '.join(eff.split()[1:])
                elif relation in [stemmer.stem(word) for word in eff.split()]:

                        eff= ' '.join(eff.split()[[stemmer.stem(word) for word in eff.split()].index(relation) + 1:])

                effects.append(eff)
                for tup in parse_dict['dependencies'][index:]: #This is where we search for additional effects.
                    if tup[0]=='conj_and' and stemmer.stem(tup[1])==relation:
                        next_eff= wrap_effect(nltk.ParentedTree(parse_dict['parsetree']), tup[2])

                    if 'and' in next_eff.split() and next_eff.split().index(tup[2]) > next_eff.split().index('and'):

                        next_eff= ' '.join(next_eff.split()[next_eff.split().index('and') + 1:])

                        if next_eff:
                            if next_eff not in effects: effects.append(next_eff)

                    elif relation in [stemmer.stem(word) for word in next_eff.split()]:

                        next_eff= ' '.join(next_eff.split()[[stemmer.stem(word) for word in next_eff.split()].index(relation) + 1:])

                        if next_eff:
                            if next_eff not in effects: effects.append(next_eff)

        #Here is the case of a sentence such as: "because of noun1 the noun2 verbed some other noun3"

        elif stemmer.stem(tuple[2])==relation and tuple[0]=='prep_as':
            eff=str(tuple[1])
            for tuple in parse_dict['dependencies']:
                if tuple[1]==eff and tuple[0]=='nsubj':
                    ptree=nltk.ParentedTree(parse_dict['parsetree'])
                    eff1=wrap_effect(ptree, str(tuple[2]))
            eff2 = wrap_effect(ptree, eff)
            eff= eff1 + ' ' + eff2
            if eff.split()[0] in set(['on', 'for', 'to']):
                eff= ' '.join(effect.split()[1:])
            elif relation in [stemmer.stem(word) for word in eff.split()]:

                        eff= ' '.join(eff.split()[[stemmer.stem(word) for word in eff.split()].index(relation) + 1:])
            effects.append(eff)
    return effects

def get_cause(relation, parse_dict):
    import nltk
    from collections import deque
    stemmer=nltk.PorterStemmer()
    relation=[node for node in parse_dict['dependency-tree'].nodes() if stemmer.stem(node)==relation][0]

#While in many functions we need the stem, here we don't want it.

#Get dequeue and do some sort of search algorithm for the relation.
    cause_list=[]
    cause=''
    root=parse_dict['dependency-tree']['ROOT'].keys()[0]

    queue=deque([root])

    while queue:
        v=queue.popleft()

        w=[succ for succ in parse_dict['dependency-tree'].successors(v) if parse_dict['dependency-tree'][v][succ]['label']=='dobj']

 	if v==relation or (w and w[0]==relation) or (relation in parse_dict['dependency-tree'].successors(v) and parse_dict['dependency-tree'][v][relation]['label'] in set(['xcomp'])):

            cause_list=[key for key in parse_dict['dependency-tree'].successors(v) if parse_dict['dependency-tree'][v][key]['label'] in
 			set(['nsubj'])]
            if cause_list:
                ptree=nltk.ParentedTree(parse_dict['parsetree'])
                cause= wrap_effect(ptree, cause_list[0])
                trim_cause(ptree, stemmer.stem(relation), cause)

                return cause

        else:
            queue.extend(parse_dict['dependency-tree'].successors(v))

    return cause


#for relational label evaluation:
def is_zero_effect(relation, parse_dict):
    import nltk
    stemmer=nltk.PorterStemmer()
    for tuple in parse_dict['dependencies']:
        if stemmer.stem(tuple[1])==relation and tuple[2]=='no':
            return True

def non_zero_effect(arc, parse_dict):

    cause, relation, effect =arc
    check1=check2=check3=False
    for tuple in parse_dict['dependencies']:
	if tuple[0]=='conj_or':
            if tuple[1] in positive:
                good=tuple[1]
            elif tuple[1] in negative:
                bad=tuple[1]
            if tuple[2] in positive:
                good=tuple[2]
            elif tuple[2] in negative:
                bad=tuple[2]
 		if tuple[1]!=tuple[2] and (tuple[1]==good or tuple[1]==bad) and (tuple[2]==good or tuple[2]==bad):
                    check1=True
    if check1:
        for tuple in parse_dict['dependencies']:
            if tuple[0]=='nsubj' and tuple[1]==good and (tuple[2]==cause or parse_dict['coref'][tuple[2]]==cause):
                check2=True
            elif tuple[0]=='nsubj' and tuple[1]==bad and (tuple[2]==cause or parse_dict['coref'][tuple[2]]==cause):
                check3=True
    if (check1 and check2 and check3):
        return True
    else: return False





#Lookup Tables for phrases and Dictionaries:

#Lookup Tables:

PhraseLookup = set(["SBAR", "UCP", "ADJP", "ADVP", #Parse Tree phrases "SQ","VP","WHADVP","WHNP","WHPP","INDETERMINATE","FRAG"
"NP", "PP", "S", "SBAR", "SINV","SBARQ",
])

InfluenceLookup=set(['Causation', 'Cause_change_of_strength', 'Objective_influence', 'Cause_change_of_position_on_a_scale', 'Removing', 'Damaging', 'Desirability'])

posClassLookup = set(['BY','BEN','NOT','CC','CD','DT','EX','FW','IN','JJ',  #Part Of Speech Tags.
'JJR','JJS','LS','MD','NN','NNS','NNP','NNPS','PDT','POS','PRP','PRP$',
'RB','RBR','RBS','RP','SYM','TO','UH','VB','VBD','VBG','VBN','VBP','VBZ',
'WDT','WP','WP$','WRB','#','$','.','?','!',',',':',';', '(',')','"', "'"])

#Dictionaries:

positive=set(['good', 'lead to', 'great', 'benefici', 'make', 'help', 'incit', 'convalesc', 'polish', 'reinforc', 'succour', 'uphold', 'fix', 'better', 'add', 'spread', 'mend', 'save', 'invigor', 'snowbal', 'remedi', 'preserv', 'enrich', 'financ', 'intensifi', 'facilit', 'magnifi', 'compound', 'increas', 'aggrand', 'benefit', 'resum', 'back', 'second', 'result', 'further', 'precipit', 'recuper', 'profit', 'defend', 'favour', 'prop', 'underwrit', 'sustain', 'boost', 'induc', 'encourag', 'extend', 'advanc', 'gener', 'promot', 'repair', 'continu', 'dilat', 'recov', 'renew', 'prolifer', 'improv', 'produc', 'endors', 'widen', 'provok', 'commenc', 'bolster', 'prolong', 'proceed', 'support', 'upgrad', 'construct', 'avail', 'start', 'foster', 'advoc', 'wax', 'forward', 'engend', 'champion', 'cultiv', 'heal', 'amplifi', 'fund', 'advantag', 'lift', 'hoist', 'gain', 'deepen', 'heighten', 'serv', 'augment', 'restor', 'mount', 'renov', 'occas', 'aid', 'sponsor', 'enlarg', 'creat', 'strengthen', 'cure', 'motiv', 'aggrav', 'subsid', 'revit', 'hone', 'develop', 'compel', 'build', 'brace', 'espous', 'begin', 'multipli', 'swell', 'assist', 'inflat', 'rais', 'enhanc', 'grow', 'expand', 'escal', 'caus', 'shore', 'maintain', 'elev', 'counten'])

negative=set(['bad', 'harm', 'abas', 'abat', 'abbrevi', 'abridg', 'adulter', 'afflict', 'aggriev', 'allevi', 'anaesthet', 'annihil', 'annoy', 'annul', 'arrest', 'assassin', 'attack', 'avoid', 'bankrupt', 'bar', 'beat', 'beggar', 'belay', 'belittl', 'benumb', 'besmirch', 'blacken', 'blight', 'block', 'blow', 'blunt', 'bodg', 'botch', 'bother', 'break', 'bruis', 'burden', 'butcher', 'cancel', 'ceas', 'chagrin', 'check', 'clobber', 'combat', 'condens', 'condescend', 'conquer', 'contract', 'control', 'crippl', 'croak', 'crush', 'curb', 'curtail', 'cut', 'damag', 'dampen', 'deaden', 'remov','debas', 'debilit', 'decim', 'declin', 'decreas', 'defac', 'defeat', 'deflat', 'degrad', 'deign', 'demean', 'demolish', 'depress', 'desol', 'despoil', 'destroy', 'deter', 'devalu', 'devast', 'devest', 'dilut', 'diminish', 'disabl', 'discompos', 'discourag', 'disempow', 'disfigur', 'disgrac', 'dismantl', 'dispatch', 'distress', 'downgrad', 'downsiz', 'droop', 'drop', 'dull', 'dwindl', 'encumb', 'end', 'enerv', 'enfeebl', 'erad', 'eras', 'eschew', 'execut', 'exhaust', 'extermin', 'extinguish', 'extirp', 'fade', 'fail', 'fight', 'flag', 'floor', 'foil', 'frustrat', 'gash', 'griev', 'gut', 'halt', 'handicap', 'harm', 'hinder', 'hobbl', 'humbl', 'humili', 'hurt', 'hush', 'ill-treat', 'impair', 'imped', 'impoverish', 'incapacit', 'incommod', 'inconveni', 'inhibit', 'injur', 'invalid', 'jeopard', 'kill', 'lessen', 'level', 'liquid', 'lower', 'maim', 'maltreat', 'mangl', 'mar', 'massacr', 'minim', 'mitig', 'moder', 'molest', 'muffl', 'murder', 'mute', 'mutil', 'neutral', 'nonplu', 'nullifi', 'numb', 'obliter', 'obstruct', 'oppos', 'oppress', 'outplay', 'overload', 'overpow', 'overthrow', 'overturn', 'overwhelm', 'pain', 'paralys', 'pauper', 'pillag', 'plunder', 'prevent', 'prune', 'quash', 'quell', 'quieten', 'ravag', 'raze', 'reduc', 'resist', 'revers', 'rout', 'ruin', 'sabotag', 'sack', 'sadden', 'sap', 'scotch', 'shatter', 'shorten', 'shrink', 'sink', 'slash', 'slaughter', 'slay', 'smash', 'smother', 'soften', 'spoil', 'staunch', 'stem', 'stifl', 'still', 'sting', 'stop', 'strain', 'subdu', 'subjug', 'submerg', 'subvert', 'suppress', 'tank', 'tarnish', 'temper', 'termin', 'thin', 'thwart', 'tire', 'total', 'trammel', 'trash', 'trounc', 'truncat', 'undermin', 'undo', 'upset', 'vanquish', 'veto', 'vitiat', 'wast', 'weaken', 'whack', 'withstand', 'wound', 'wreck'])

neutral=set(['affect', 'effect'])

causal_words= set(list(positive) + list(negative) + list(neutral))
