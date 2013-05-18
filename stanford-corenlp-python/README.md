# A Python wrapper for the Java Stanford Core NLP tools

This is a fork of [stanford-corenlp-python](https://github.com/dasmith/stanford-corenlp-python), originally written by Dustin Smith and it incorporates the fixes made by Hioroyoshi Komatsu [corenlp-python] (https://bitbucket.org/torotoki/corenlp-python).

## New changes:

The original wrapper only worked for extreemly short texts and it did not accept files.  This new version cleans the raw text files that are placed in the "raw_text" folder, places the cleaned files into the "clean_text" folder, runs the Stanford tools on those cleaned files and creates a large xml file which is placed in the xml folder. The "parse_xml_output()" calls the Stanford tools and parses the xml file to create a python object that is identical to the object that was created in the old version, except that the text length is now unlimited. All changes were mad to one file: "corenlp.py", which can by found in the "corenlp" folder. For more information, please consult the "README" file (by Hioroyoshi Komatsu) in the "corenlp-python" folder!  I am constantly working on this project as these tools help me in my work and I welcome any feedback [jac2130@columbia.edu].

## New Requirements
   * [xmltodict](https://github.com/martinblech/xmltodict)

## To use the new feature:

      import sys

      sys.path.append("[full-path]/corenlp-wrapper/corenlp")

      from collections import OrderedDict

      corenlp_dir = "[full-path]/corenlp-wrapper/stanford-corenlp-full-2013-04-04"

      corenlp = StanfordCoreNLP(corenlp_dir)

      parse_dict=eval(corenlp.parse())

If you instead type:

      parse_dict=eval(corenlp.parse(text))

where "text" is any non-empty string, the behavior is identical to the behavior before the new changes. Thus, if you want to use the new feature, you can just leave the text blank and place your raw files into the "raw_files" folder. The rest is as before.
