#! /usr/bin/python
# -*- coding:utf-8 -*-

import re
from collections import OrderedDict
#from pprint import pprint
from paideia_utils import clr
import traceback

wordforms = {'ἀνηρ': {'gender': 'masc',
                      'part_of_speech': 'noun',
                      'number': 'sing',
                      'case': 'nominative'},
             'ἀρτον': {'gender': 'masc',
                       'part_of_speech': 'noun',
                       'number': 'sing',
                       'case': 'accusative'},
             'ὁ': {'part_of_speech': 'def_art',
                   'gender': 'masc',
                   'number': 'sing',
                   'case': 'nominative'},
             'τον': {'part_of_speech': 'def_art',
                     'gender': 'masc',
                     'number': 'sing',
                     'case': 'accusative'}
             }


def tokenize(str):
    """
    Divide a string into clauses and each clause into word tokens.

    Returns a list of OrderedDicts, each of which represents one clause
    (or fragment). The keys in each dict are the tokens which make up the
    clause, ordered according to their appearance in the string.
    """
    clauses = re.split(r'[\.\?;:,]', str)
    tokenized = []
    for c in clauses:
       token_dict = OrderedDict((t.decode('utf-8').lower().encode('utf-8'), None) for t in c.split(' '))
       tokenized.append(token_dict)
    return tokenized


class Parser(object):
    """
    Abstract class defining basic recursive parsing behaviour.
    """
    myc = 'white'

    def __init__(self, *args):
        """
        Initialize a Parser object.

        restring
        : Test string to be used in regex comparisons for evaluating this
        construction

        structures
        : A list of Parser sub-class objects representing the grammatical
        constructions expected as constituents of this parent construction.
        """
        self.restring = args[0]
        if self.restring:
            self.restring = args[0].strip()
        self.structures = list(args[1:])

    def validate(self, validleaves, failedleaves=[]):
        """
        compare list of word tokens to definition of valid natural language expressions.

        clause should be Clause() object
        """
        # TODO: to see eliminated parsing leaves, move them to a second list
        # instead of simply removing
        print clr('validating {}'.format(type(self).__name__), self.myc)
        print clr('starting with {} valid leaves in parsing tree'.format(len(validleaves)), self.myc)

        # validate constituent structures first, recursively
        try:
            for s in self.structures:
                validleaves, failedleaves = s.validate(validleaves, failedleaves)
                if len(validleaves) < 1:
                    print clr('sub-structures didn\'t match', self.myc)
                    return validleaves, failedleaves
        except AttributeError:  # if structure is at bottom level
            pass

        # test sub-structure order for any viable parsing leaves returned
        for idx, leaf in enumerate(validleaves):
            leaf, match = self.test_order(leaf)
            if not match:
                failedleaves.append(validleaves.pop(idx))
            if len(validleaves) < 1:
                print clr(['order didn\'t match in', type(self).__name__], self.myc)
                return validleaves, failedleaves

        # find matching string in remaining viable leaves
        if self.restring:
            validleaves, failedleaves = self.match_string(validleaves, failedleaves)
            if len(validleaves) < 1:
                print clr(['didn\'t find matching string for', type(self).__name__],
                          self.myc)
                return validleaves, failedleaves

        # find any untagged words in remaining leaves and remove those leaves
        # only if top level
        if isinstance(self, Clause):
            # TODO: handle top-level detection for non-Clause objects
            # add optional 'top' argument/property to Parser abstract class
            for idx, leaf in enumerate(validleaves):
                if [t for t, v in leaf.iteritems() if not v]:
                    failedleaves.append(validleaves.pop(idx))
            if len(validleaves < 1):
                print clr(['some extra words left over'], self.myc)
                return validleaves, failedleaves

        print clr('finished with {} valid leaves in parsing tree'.format(len(validleaves)), self.myc)
        if len(validleaves):
            print clr('{} is valid'.format(type(self).__name__), self.myc)
        return validleaves, failedleaves

    def match_string(self, tokens, restring=None, classname=None):
        '''
        Identify token strings that match the current construction.

        tokens
        : The ordered list of strings conaining the actual utterance.
        '''

        restring = self.restring if not restring else restring
        classname = type(self).__name__ if not classname else classname
        for t, k in tokens.iteritems(): print '{}:'.format(t), '{};'.format(k),
        test = re.compile(restring, re.U|re.I)
        print clr('looking for {}'.format(restring), self.myc)
        result = True
        mymatch = test.findall(' '.join(tokens[0]))
        # TODO: split into leaves if (b) match already tagged
        # TODO: handle list of leaves elsewhere for tokens
        print clr('found {} matching strings in tokens'.format(len(mymatch)), self.myc)
        def tag_token(matchstring, leaftokens):
            for word in matchstring.split(' '):  # allows for multi-word match strings
                print 'match:', clr(word, self.myc),
                try:
                    leaftokens[word].append(classname)
                except AttributeError:
                    leaftokens[word] = [classname]
        if mymatch:
            tokens = [leaf.tag_token(m, leaf)
                      for leaf in tokens for m in mymatch]
            print clr('now working with {} leaves in parsing '
                      'tree'.format(len(tokens)), self.myc)
        else:
            result = False
        return (tokens, result)

    def test_order(self, tokens):
        """ """
        match = True
        return tokens, match

    def get_struct_order(self, tokens):
        """
        Returns a dictionary of Parser subclass names and their index in tokens.

        This method also sets the self.structs class instance variable to the
        return value.
        """
        try:
            structs = {}
            for i, v in enumerate(tokens.values()):
                try:
                    structs[v] = i
                except TypeError:  # if the value is a list
                    for l in v:
                        structs[l] = i
            self.structs = structs
            return structs
        except Exception:
            print traceback.format_exc(5)

    def before(self, struct1, struct2, proximity=0, allow=[], exclude=[], require=[]):
        """
        Test whether struct1 appears before struct2 in the parsed tokens.

        Returns a boolean (True if struct1 comes before).

        proximity (int)
        :keyword argument, gives the maximum index places the two structures
        may stand apart in the token dictionary. The default value (0)
        indicates that proximity will not be considered.

        allow (list of strings)
        :keyword argument, lists the structures (type names) that may appear
        between struct1 and struct2.

        exclude (list of strings)
        :keyword argument, lists the structures (type names) that may not appear
        between struct1 and struct2.
        """
        structs = self.structs
        p1 = structs[struct1]
        p2 = structs[struct2]
        fit = True if p1 < p2 else False
        if fit and proximity > 0:
            fit = True if p2 - p1 <= proximity else False
        if fit and (allow or exclude or require):
            fit = self.between(p1, p2, allow, exclude, require)
        return fit

    def after(self, struct1, struct2, proximity=0,
              allow=[], exclude=[], require=[]):
        """
        Test whether struct1 appears before struct2 in the parsed tokens.

        Returns a boolean (True if struct1 comes before).

        proximity (int)
        :keyword argument, gives the maximum index places the two structures
        may stand apart in the token dictionary. The default value (0)
        indicates that proximity will not be considered.

        allow (list of strings)
        :keyword argument, lists the structures (type names) that may appear
        between struct1 and struct2.

        exclude (list of strings)
        :keyword argument, lists the structures (type names) that may not appear
        between struct1 and struct2.
        """
        structs = self.structs
        p1 = structs[struct1]
        p2 = structs[struct2]
        fit = True if p2 < p1 else False
        if fit and proximity > 0:
            fit = True if p1 - p2 <= proximity else False
        if fit and (allow or exclude or require):
            fit = self.between(p2, p1, allow, exclude, require)
        return fit

    def between(self, p1, p2, allow=[], exclude=[], require=[]):
        """
        Test whether any intervening structures are appropriate.
        """
        between = [s for s, v in self.structs.iteritems()
                   if v in range(p1 + 1, p2 - 1)]
        disallowed = [s for s in between
                      if (s not in allow) or (s in exclude)]
        missing = [s for s in require if s not in between]
        fit = False if (disallowed or missing) else True

        return fit

    def parseform(self, token):
        """
        Return a dictionary holding the grammatical information for the token.
        """
        return wordforms[token]

    def getform(self, **kwargs):
        """
        Return a list of possible declined forms for the supplied parsing.
        """
        myform = list(set([w for w, p in wordforms.iteritems()
                           if not [k for k, v in kwargs.iteritems()
                                   if p[k] != v]
                           ]))
        return myform


class Clause(Parser):
    """ """
    reqs = ['Verb']
    pass


class VerblessClause(Parser):
    """ """
    reqs = ['Subject', 'Complement']

    def test_order(self, tokens):
        """
        Is there any necessary?
        """
        pass


class Verb(Parser):
    myc = 'orange'
    """
    """
    reqs = []
    pass

class NounPhrase(Parser):
    myc = 'lightcyan'

    def __init__(self, *args):
        """
        """
        super(NounPhrase, self).__init__(*args)
        self.definite = False
        if 'def' in self.structures:
            self.definite = True
            self.structures.remove('def')

    def find_article(self, nominal, tokens):
        """
        Add the appropriate def article to the substructures of a noun phrase.
        """
        gram = self.parseform(nominal)
        kwargs = {'gender': gram['gender'],
                  'case': gram['case'],
                  'number': gram['number'],
                  'part_of_speech': 'def_art'
                  }
        myart = self.getform(**kwargs)[0]  # What about multiple matches?
        tokens, match = self.match_string(tokens, restring=myart, classname='Art')
        return tokens

    def test_order(self, tokens):
        """
        """
        print 'testing order for', clr(type(self).__name__, self.myc)
        match = False

        if self.definite:  # look for article(s) in valid configuration
            nominals = [t for t, v in tokens.iteritems() if v and 'Noun' in v]
            for n in nominals:
                tokens = self.find_article(n, tokens)
            structs = self.get_struct_order(tokens)
            for k, v in structs.iteritems(): print clr([k, v, ';'], self.myc),

            # TODO: check agreement of art and noun
            #- have before return index of both
            #- use index to test agreement
            matches = [self.before('Art', 'Noun', allow='Adj'),
                       self.before('Art', 'Noun', proximity=1)]
            match = [m for m in matches if m]
        else:
            match = True

        return tokens, match


class DirObject(NounPhrase):
    myc = 'lightred'
    """
    """
    pass


class IndirObject(NounPhrase):
    """
    """
    pass


class Subject(NounPhrase):
    """
    """
    pass


class DatPhrase(NounPhrase):
    """
    """

class Noun(Parser):
    """
    Defniteness ambiguous.
    """
    myc = 'blue'
    pass


class Art(Parser):
    """
    """
    pass


class Adjective(Parser):
    pass


if __name__ == "__main__":
    print clr('\n\nSTARTING VALIDATION', 'white')
    strings = ['Τον ἀρτον ὁ ἀνηρ πωλει.',
               'Ὁ ἀνηρ πωλει τον ἀρτον.',
               'Πωλει τον ἀρτον ὁ ἀνηρ.',
               'τον πωλει ὁ ἀρτον ἀνηρ.'  # fails
               'ὁ ἀρτον πωλει τον ἀνηρ.'  # fails
               ]
    for s in strings:
        tokenset = [token for token in tokenize(s) if token.keys()[0] not in ['', ' ', None]]
        #print len(tokens), 'clauses to validate'
        for tokens in tokenset:
            c = Clause(None,
                       Subject(None, Noun(r'ἀνηρ'), 'def'),
                       Verb(r'πωλει|ἀγοραζει'),
                       DirObject(None, Noun(r'ἀρτον'), 'def')
                       )
            # put tokens in list to prepare for parsing tree forking
            validleaves, failedleaves = c.validate([tokens])
            myc = 'green' if validleaves else 'red'
            resp = 'Success!' if validleaves else 'Failed'
            print clr([resp, '\n'], myc)
