
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

def receiving(tuples, receiver, to_do='', goal='', effect=''):                 #this function ca be called by other functions to get a full effect
    for tup in tuples:                                               #when the effect includes people, or other entities receiving something
        if str(tup[0])=='Receiving' and str(tup[1])=='Target':
            to_do= ' ' + str(tup[2])
            for tp in tuples:
                if type(tp[1])==type(tp[2])==list:
                    if str(tp[2][0])=='Recipient' and str(tp[2][1])==receiver:
                        goal= ' ' + str(tp[1][1])
        if goal:
            effect=receiver + to_do + goal
    return effect

def removing(parse_dict, cause='', relation='', effect=''):
    import nltk
    stemmer=nltk.PorterStemmer()
    arcs=[]
    for tuple in parse_dict['fn_labels']:
        if str(tuple[0])=='Removing' and str(tuple[1])=='Target':
            relation=stemmer.stem(str(tuple[2]))
        elif str(tuple[0])=='Removing' and str(tuple[1])=='Theme':
            cause=str(tuple[2])
    if (cause and relation):
        effects=get_effects(relation, parse_dict) #This function (get_effects) makes structural use of the dependencies in the Stanford dependencies graph. Soon, I want to make more use of the structures in both frame-net (currently, I am using the labels without taking advantage of nearby-ness) and the dependencies (I'm already making use of the syntactic trees, in wrap_effect, mostly)
        if effects:
            number_effects=len(effects)
            [arcs.append((c, r, e)) for c, r, e in zip([cause]*number_effects, [relation]*number_effects, effects) if (c, r, e) not in arcs]
    elif (cause and relation and effect) and (cause, relation, effect) not in arcs:
        arcs.append((cause, relation, effect))

    return arcs

def assistance(tuples, parse_dict, cause='', relation='', effect=''):
    import nltk
    stemmer=nltk.PorterStemmer()
    arcs=[]
    for tuple in tuples:
       #getting the relation
        if str(tuple[0])=='Assistance' and str(tuple[1])=='Target':
            relation=stemmer.stem(str(tuple[2]))
            for tup in tuples:                                                  #and now the effect
                if str(tup[0])=='Assistance' and str(tup[1])=='Goal':
                    effect=receiving(tuples, receiver=str(tup[2]), to_do='', goal='', effect='')
                    '''If some cause is affecting people's receiving something, the effect is:
                    people receiving something
                    Else, the effect is people's utility'''


                    if not effect:
                        if tup[2].split()[0] in set(['on', 'for', 'to']):
                            effect = 'Utility('+' '.join(tup[2].split()[1:]) +')'
                        else:
                            effect = 'Utility('+tup[2]+')'
                        ptree=nltk.ParentedTree(parse_dict['parsetree'])
                        cause=get_cause(relation, parse_dict)
                        cause=trim_cause(ptree, relation, cause)
                        if (cause and relation and effect) and (cause, relation, effect) not in arcs:
                            arcs.append((cause, relation, effect))
                    else:
                        ptree=nltk.ParentedTree(parse_dict['parsetree'])
                        cause=get_cause(relation, parse_dict)
                        cause=trim_cause(ptree, relation, cause)
                        if (cause and relation and effect) and (cause, relation, effect) not in arcs:
                            arcs.append((cause, relation, effect))

    return arcs  #if effect is not the same as the basic noun-wrapped effect that would result from passing through the end of the function that captures all rest-causation, then this might result in duplicate causal arcs, with slightly different effect variables!!!

def desirability(tuples, parse_dict, cause='', relation='', effect=''):
    arcs=[]
    import nltk
    stemmer=nltk.PorterStemmer()
    for tuple in tuples:
        if str(tuple[0])=='Desirability' and str(tuple[1])=='Target':
            relation = stemmer.stem(str(tuple[2]))

            for tup in parse_dict['dependencies']:
                if tup[0]=='prep_for' and stemmer.stem(tup[1])==relation:
                    ptree=nltk.ParentedTree(parse_dict['parsetree'])
                    effect=wrap_effect(ptree, tup[2])
                    if effect.split()[0] in set(['on', 'for', 'to']):
                        effect= ' '.join(effect.split()[1:])

        elif str(tuple[0])=='Desirability' and str(tuple[1])=='Evaluee':
            cause=str(tuple[2])

    if (cause and relation and effect) and (cause, relation, effect) not in arcs:
        arcs.append((cause, relation, effect))
    return arcs

def obj_influence(parse_dict, cause='', relation='', effect=''):
    arcs=[]
    import nltk
    stemmer=nltk.PorterStemmer()

    for tuple in parse_dict['fn_labels']:
        if str(tuple[0])=='Objective_influence' and str(tuple[1])=='Target':
            relation=stemmer.stem(str(tuple[2]))

        elif str(tuple[0])=='Objective_influence' and str(tuple[1])=='Influencing_situation':
            cause =str(tuple[2])

        elif str(tuple[0])=='Objective_influence' and str(tuple[1])=='Dependent_entity':
            effect =str(tuple[2])

            if effect.split()[0] in set(['on', 'for', 'to']):
                effect= ' '.join(effect.split()[1:])

    if (cause and relation and effect) and (cause, relation, effect) not in arcs:
        arcs.append((cause, relation, effect))

    elif (cause and relation):
        effects=get_effects(relation, parse_dict) #get effects again
        if effects:
            number_effects=len(effects)
            [arcs.append((c, r, e)) for c, r, e in zip([cause]*number_effects, [relation]*number_effects, effects) if (c, r, e) not in arcs]
        elif (cause and relation and effect) and (cause, relation, effect) not in arcs:
            arcs.append((cause, relation, effect))

    elif (relation and effect):
        cause=get_cause(relation, parse_dict)
        if (cause and relation and effect) and (cause, relation, effect) not in arcs:
            arcs.append((cause, relation, effect))


    return arcs

def cause_change(tuples, parse_dict, cause='', relation='', effect=''):
    arcs=[]
    cause_change=set(['Cause_change_of_strength', 'Cause_change_of_position_on_a_scale'])  #Framenet is more subtle than needed
    result = set(['Patient', 'Attribute'])
    import nltk
    stemmer=nltk.PorterStemmer()
    for tuple in tuples:
        if str(tuple[0]) in cause_change and str(tuple[1])=='Target':
            relation=stemmer.stem(str(tuple[2]))
            for tup in tuples:
                if str(tuple[0]) in cause_change and str(tup[1]) in result:
                    effect=str(tup[2])
                    if (relation and effect):
                        cause=get_cause(relation, parse_dict)
                        if (cause and relation and effect) and (cause, relation, effect) not in arcs:
                            arcs.append((cause, relation, effect))
    return arcs

def causation(tuples, parse_dict, cause='', relation='', effect=''):
    arcs=[]
    import nltk
    stemmer=nltk.PorterStemmer()
    for tuple in tuples:

        if str(tuple[1])=='Cause':
                cause = str(tuple[2]); label= str(tuple[0])
                if cause.split()[0] in set(['of']):
                    cause= ' '.join(cause.split()[1:])
                relation=get_relation_from_label(tuples, label)
                effects = get_effects(relation, parse_dict)  #get_effects again
                if effects:
                    number_effects=len(effects)
                    [arcs.append((c, r, e)) for c, r, e in zip([cause]*number_effects, [relation]*number_effects, effects) if (c, r, e) not in arcs]
                if (cause and relation and effect):
                    if (cause, relation, effect) not in arcs:
                        arcs.append((cause, relation, effect))

        elif str(tuple[0])=='Causation' and str(tuple[1])=='Target':
            relation=stemmer.stem(str(tuple[2]))
        elif str(tuple[0])=='Causation' and type(tuple[1])==type(tuple[2])==list:
            if str(tuple[1][0])=='Effect':
                if str(tuple[1][1])[:2]!='by':                           #This line exists because semaphore often makes this mistake
                                                                     #it doesn't correct for passive voice.
                    effect= str(tuple[1][1])

                    cause= str(tuple[2][1])
                    if (cause and relation and effect):
                        if (cause, relation, effect) not in arcs:
                            arcs.append((cause, relation, effect))
                else:
                    cause= str(tuple[1][1])[3:]
                    effect=str(tuple[2][1])
                    if (cause and relation and effect) and (cause, relation, effect) not in arcs:
                        arcs.append((cause, relation, effect))
            elif str(tuple[1][0])=='Cause':
                cause=str(tuple[1][1])
                effect=str(tuple[2][1])
                if effect.split()[0] in set(['on', 'for', 'to']):
                    effect= ' '.join(effect.split()[1:])
                if (cause and relation and effect):
                    if (cause, relation, effect) not in arcs:
                        arcs.append((cause, relation, effect))
    return arcs

def get_relation_from_label(tuples, label):
    import nltk
    stemmer=nltk.PorterStemmer()
    for tuple in tuples:
        if str(tuple[0])==label and str(tuple[1])=='Target':
            relation = stemmer.stem(str(tuple[2]))
    return relation

def get_effects(relation, parse_dict):
    import nltk
    result=set(['dobj', 'prep_to'])
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
    stemmer=nltk.PorterStemmer()
    cause=''
    for tup in parse_dict['dependencies']:
        if tup[0]=='nsubj' and stemmer.stem(tup[1])==relation:
            ptree=nltk.ParentedTree(parse_dict['parsetree'])
            cause=wrap_effect(ptree, tup[2])
            trim_cause(ptree, relation, cause)
        elif tup[0]=='dobj' and stemmer.stem(tup[2])==relation:
            temp_var=stemmer.stem(tup[1])
            cause=get_cause(temp_var, parse_dict)
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

posClassLookup = set(['BY','BEN','NOT','CC','CD','DT','EX','FW','IN','JJ',  #Part Of Speech Tags.
'JJR','JJS','LS','MD','NN','NNS','NNP','NNPS','PDT','POS','PRP','PRP$',
'RB','RBR','RBS','RP','SYM','TO','UH','VB','VBD','VBG','VBN','VBP','VBZ',
'WDT','WP','WP$','WRB','#','$','.','?','!',',',':',';', '(',')','"', "'"])

#Dictionaries:

positive=set(['good', 'great', 'benefici', 'make', 'help', 'incit', 'convalesc', 'polish', 'reinforc', 'succour', 'uphold', 'fix', 'better', 'add', 'spread', 'mend', 'save', 'invigor', 'snowbal', 'remedi', 'preserv', 'enrich', 'financ', 'intensifi', 'facilit', 'magnifi', 'compound', 'increas', 'aggrand', 'benefit', 'resum', 'back', 'second', 'result', 'further', 'precipit', 'recuper', 'profit', 'defend', 'favour', 'prop', 'underwrit', 'sustain', 'boost', 'induc', 'encourag', 'extend', 'advanc', 'gener', 'promot', 'repair', 'continu', 'dilat', 'recov', 'renew', 'prolifer', 'improv', 'produc', 'endors', 'widen', 'provok', 'commenc', 'bolster', 'prolong', 'proceed', 'support', 'upgrad', 'construct', 'avail', 'start', 'foster', 'advoc', 'wax', 'forward', 'engend', 'champion', 'cultiv', 'heal', 'amplifi', 'fund', 'advantag', 'lift', 'hoist', 'gain', 'deepen', 'heighten', 'serv', 'augment', 'restor', 'mount', 'renov', 'occas', 'aid', 'sponsor', 'enlarg', 'creat', 'strengthen', 'cure', 'motiv', 'aggrav', 'subsid', 'revit', 'hone', 'develop', 'compel', 'build', 'brace', 'espous', 'begin', 'multipli', 'swell', 'assist', 'inflat', 'rais', 'enhanc', 'grow', 'expand', 'escal', 'caus', 'shore', 'maintain', 'elev', 'counten'])

negative=set(['bad', 'harm', 'abas', 'abat', 'abbrevi', 'abridg', 'adulter', 'afflict', 'aggriev', 'allevi', 'anaesthet', 'annihil', 'annoy', 'annul', 'arrest', 'assassin', 'attack', 'avoid', 'bankrupt', 'bar', 'beat', 'beggar', 'belay', 'belittl', 'benumb', 'besmirch', 'blacken', 'blight', 'block', 'blow', 'blunt', 'bodg', 'botch', 'bother', 'break', 'bruis', 'burden', 'butcher', 'cancel', 'ceas', 'chagrin', 'check', 'clobber', 'combat', 'condens', 'condescend', 'conquer', 'contract', 'control', 'crippl', 'croak', 'crush', 'curb', 'curtail', 'cut', 'damag', 'dampen', 'deaden', 'remov','debas', 'debilit', 'decim', 'declin', 'decreas', 'defac', 'defeat', 'deflat', 'degrad', 'deign', 'demean', 'demolish', 'depress', 'desol', 'despoil', 'destroy', 'deter', 'devalu', 'devast', 'devest', 'dilut', 'diminish', 'disabl', 'discompos', 'discourag', 'disempow', 'disfigur', 'disgrac', 'dismantl', 'dispatch', 'distress', 'downgrad', 'downsiz', 'droop', 'drop', 'dull', 'dwindl', 'encumb', 'end', 'enerv', 'enfeebl', 'erad', 'eras', 'eschew', 'execut', 'exhaust', 'extermin', 'extinguish', 'extirp', 'fade', 'fail', 'fight', 'flag', 'floor', 'foil', 'frustrat', 'gash', 'griev', 'gut', 'halt', 'handicap', 'harm', 'hinder', 'hobbl', 'humbl', 'humili', 'hurt', 'hush', 'ill-treat', 'impair', 'imped', 'impoverish', 'incapacit', 'incommod', 'inconveni', 'inhibit', 'injur', 'invalid', 'jeopard', 'kill', 'lessen', 'level', 'liquid', 'lower', 'maim', 'maltreat', 'mangl', 'mar', 'massacr', 'minim', 'mitig', 'moder', 'molest', 'muffl', 'murder', 'mute', 'mutil', 'neutral', 'nonplu', 'nullifi', 'numb', 'obliter', 'obstruct', 'oppos', 'oppress', 'outplay', 'overload', 'overpow', 'overthrow', 'overturn', 'overwhelm', 'pain', 'paralys', 'pauper', 'pillag', 'plunder', 'prevent', 'prune', 'quash', 'quell', 'quieten', 'ravag', 'raze', 'reduc', 'resist', 'revers', 'rout', 'ruin', 'sabotag', 'sack', 'sadden', 'sap', 'scotch', 'shatter', 'shorten', 'shrink', 'sink', 'slash', 'slaughter', 'slay', 'smash', 'smother', 'soften', 'spoil', 'staunch', 'stem', 'stifl', 'still', 'sting', 'stop', 'strain', 'subdu', 'subjug', 'submerg', 'subvert', 'suppress', 'tank', 'tarnish', 'temper', 'termin', 'thin', 'thwart', 'tire', 'total', 'trammel', 'trash', 'trounc', 'truncat', 'undermin', 'undo', 'upset', 'vanquish', 'veto', 'vitiat', 'wast', 'weaken', 'whack', 'withstand', 'wound', 'wreck'])

neutral=set(['affect', 'effect'])

causal_words= set(list(positive) + list(negative) + list(neutral))
