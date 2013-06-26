from gluon import TAG


def V(content, attributes=None):
    """
    Returns a custom web2py html helper representing a <verbal_clause>
    xml tag.
    """
    v = TAG['verb_clause'](content, **attributes)
    return v


def SU(content, attributes=None):
    """
    Returns a custom web2py html helper representing a <subject>
    xml tag.
    """
    s = TAG['subject'](content, **attributes)
    return s


def N(content, attributes=None):
    """
    Returns a custom web2py html helper representing a <noun>
    xml tag.
    """
    n = TAG['noun'](content, **attributes)
    return n


def ADJ(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <adjective>
    xml tag.
    """
    v = TAG['adjective'](content, **attributes)
    return v


def ART(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <article>
    xml tag.
    """
    v = TAG['article'](content, **attributes)
    return v


def G(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <genitive phrase>
    xml tag.
    """
    g = TAG['genitive_phrase'](content, **attributes)
    return g


def D(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <dative_phrase>
    xml tag.
    """
    d = TAG['dative_phrase'](content, **attributes)
    return d


def ADV(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <adverb>
    xml tag.
    """
    v = TAG['article'](content, **attributes)
    return v


def CJ(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <conjunction>
    xml tag.
    """
    cj = TAG['conjunction'](content, **attributes)
    return cj


def PT(content, attributes=None):
    """
    Returns a custom web2py html helper representing an <particle>
    xml tag.
    """
    pt = TAG['conjunction'](content, **attributes)
    return pt
