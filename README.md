causal-belief-catcher
=====================

Please contact me (Johannes Castner) if you have any questions or problems! My e-mail is "jac2130@columbia.edu"

This repository combines a few open source computational linguistics tools in order to distill causal assertions from large texts.

**Dependencies:

1) xmltodict, 2) nltk, 3) pexpect 4) networkx (This should do it, but please let me know if something is missing!)

1) xmltodict:

install by typing the following into your shell:

But first, install Pip:

sudo easy_install pip

then

sudo pip install xmltodict

or, if you are on Fedora or RHEL, type:

sudo yum install python-xmltodict

2) nltk:

First install Numpy:

sudo pip install -U numpy

Then install PyYAML and NLTK:

sudo pip install -U pyyaml nltk

to test, open python and then type:

import nltk

3) pexpect:

wget http://pexpect.sourceforge.net/pexpect-2.3.tar.gz

tar xzf pexpect-2.3.tar.gz

cd pexpect-2.3

sudo python ./setup.py install

4) The full instalation instructions can be found here:

http://networkx.github.io/documentation/latest/install.html

Get NetworkX from the Python Package Index at http://pypi.python.org/pypi/networkx

or install it with:

easy_install networkx


next, in order to make this program work for you, there are exactly three places where you need to change the directory paths:
1) Edit the first few lines in "causal_parser.py" (which is in the main directory)
2) Edit the first few lines in "/stanford-corenlp-python/corenlp.py"
3) Edit the relevant paths in "Semaphore-master/semafor-semantic-parser/release/config"

Please also read the README files in the "Semaphore-master" and "stanford-corenlp-python" folders for more details!

Now, you are ready to work (or play) with all of these wonderful computational linguistic tools:

To test that everything works, open a python shell and type:

from causal_parser import *

#if you want to try out the Stanford corenlp tools, type:

parse_dict= eval(corenlp.parse("Hi there!"))                    #which will return a dictionary that contains the Stanford dependencies,
	    			   				#coreferences, syntactic parsetree etc.
#If you also want to get a feel for frame-net semantic labels, type:

run_semaphore()                                                 #This takes a file of sentences (one for each line) and produces an xml file
								#containing frame-net semantic labels and relations.
								#The file that is used for this demonstration is the following:
								# "Semaphore-master/semafor-semantic-parser/samples/sample.txt"
								#You can, of course, change the file!

#next, to get both the Stanford core tools and the semaphore output together into one convenient python dictionary, run:

nlp_core=import_semaphore()	     	       	   	     	#Now, you have a dictionary for each sentence, containing a host of useful
								#information that can be made useful for machine understanding of natural
								#languag.

nlp_core[0].keys()         #These are the dictionary keys for sentence 0.

#if, like me, you are interested in causal assertions, type:

append_cause_relation_effects(nlp_core)

#and then:

print_causal_arcs(nlp_core)
