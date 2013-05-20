#This is a file of directories that has to be changed in order to make things work:

import sys
import inspect, os

home= os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

core_nlp= home + '/corenlp-python'

semaphore= home + '/Semaphore/semaphore-python'

sys.path.append(home); sys.path.append(semaphore)

from directories import *
