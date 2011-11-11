#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The script has been taken on Python's Cookbook
# and modified a little bit to suit my needs.
# In particualr, it now handles accented chars correctly using unicode.

import cStringIO,operator

def indent(rows, hasHeader=False, headerChar='-', delim=' | ', justify='left',
           separateRows=False, prefix='', postfix='', wrapfunc=lambda x:x):
    """Indents a table by column.
       - rows: A sequence of sequences of items, one sequence per row.
       - hasHeader: True if the first row consists of the columns' names.
       - headerChar: Character to be used for the row separator line
         (if hasHeader==True or separateRows==True).
       - delim: The column delimiter.
       - justify: Determines how are data justified in their column.
         Valid values are 'left','right' and 'center'.
       - separateRows: True if rows are to be separated by a line
         of 'headerChar's.
       - prefix: A string prepended to each printed row.
       - postfix: A string appended to each printed row.
       - wrapfunc: A function f(text) for wrapping text; each element in
         the table is first wrapped by this function."""
    # closure for breaking logical rows to physical, using wrapfunc
    def rowWrapper(row):
        newRows = [wrapfunc(item).split('\n') for item in row]
        return [[substr or '' for substr in item] for item in map(None,*newRows)]
    # break each logical row into one or more physical ones
    logicalRows = [rowWrapper(row) for row in rows]
    # columns of physical rows
    columns = map(None,*reduce(operator.add,logicalRows))
    # get the maximum of each column by the string length of its items
    maxWidths = [max([len(str(item)) for item in column]) for column in columns]
    rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) + \
                                 len(delim)*(len(maxWidths)-1))
    # select the appropriate justify method
    justify = {'center':str.center, 'right':str.rjust, 'left':str.ljust}[justify.lower()]
    output=cStringIO.StringIO()
    if separateRows: print >> output, rowSeparator
    for physicalRows in logicalRows:
        for row in physicalRows:
            print >> output, \
                prefix \
                + delim.join([justify(str(item),width) for (item,width) in zip(row,maxWidths)]) \
                + postfix
        if separateRows or hasHeader: print >> output, rowSeparator; hasHeader=False
    return output.getvalue()

# written by Mike Brown
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
def wrap_onspace(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line[line.rfind('\n')+1:])
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )

import re
def wrap_onspace_strict(text, width):
    """Similar to wrap_onspace, but enforces the width constraint:
       words longer than width are split."""
    wordRegex = re.compile(r'\S{'+str(width)+r',}')
    return wrap_onspace(wordRegex.sub(lambda m: wrap_always(m.group(),width),text),width)

import math
def wrap_always(text, width):
    """A simple word-wrap function that wraps text on exactly width characters.
       It doesn't split the text in words."""
    return '\n'.join([ text[width*i:width*(i+1)] \
                       for i in xrange(int(math.ceil(1.*len(text)/width))) ])

import string
def toRSTtable(rows, header=True, vdelim="  ", padding=2, justify='center'):
    """ Outputs a list of lists as a Restructured Text Table

    - rows - list of lists
    - header - if True the first row is treated as a table header
    - vdelim - vertical delimiter betwee columns
    - padding - padding nr. of spaces are left around the longest element in the
      column
    - justify - may be left,center,right
    """
    border="=" # character for drawing the border
    justify = {'left':string.ljust,'center':string.center, 'right':string.rjust}[justify.lower()]

    # calculate column widhts (longest item in each col
    # plus "padding" nr of spaces on both sides)
    cols = zip(*rows)
    colWidths = [max([len(unicode(item))+2*padding for item in col]) for col in cols]

    # the horizontal border needed by rst
    borderline = vdelim.join([w*border for w in colWidths])

    # outputs table in rst format
    result = []
    result.append(borderline)
    for row in rows:
        #print vdelim.join([justify(str(item),width) for (item,width) in zip(row,colWidths)])
        result.append(vdelim.join([justify(unicode(item),width) for (item,width) in zip(row,colWidths)]))
        if header: result.append(borderline); header=False
    result.append(borderline)
    return "\n".join(result)

if __name__ == '__main__':
    labels = ('IOMode','Peut écrire ?','Peut lire ?','Position de départ', 'Notes')
    data = \
    '''ReadMode,Oui,Non,Début de fichier,Le fichier doit déjà exister
WriteMode,Non,Oui,Début de fichier,Le fichier est effacé s'il existe déjà
ReadWriteMode,Oui,Oui,Début de fichier,Le fichier est créé s'il n'existe pas. Sinon son contenu est gardé intact'''
    rows = [row.strip().split(',')  for row in data.splitlines()]

    print toRSTtable([labels]+rows)
