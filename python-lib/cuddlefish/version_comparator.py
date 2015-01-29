# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''
    This is a really crummy, slow Python implementation of the Mozilla
    platform's nsIVersionComparator interface:

      https://developer.mozilla.org/En/NsIVersionComparator

    For more information, also see:

      http://mxr.mozilla.org/mozilla/source/xpcom/glue/nsVersionComparator.cpp
'''

import re
import sys
PY3 = sys.version[0]=='3'

def _cmp(a,b): #implementing a cmp similar to python2 function to support python 3
    try:
        if a==b:
            r = 0
        elif a>b:
            r = 1
        else:
            r = -1
        return r
    except Exception:
        print("ERROR in comparing : ", a , "and ", b)
        raise

if PY3:
    cmp = _cmp
    MAXINT = sys.maxsize
else:
    MAXINT = sys.maxint

#the below is taken from http://python3porting.com/preparing.html#use-rich-comparison-operators
class ComparableMixin(object):
    '''
    mixin class is used to provide comparison methods.
    '''
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented




class VersionPart():
    '''
    Examples:

      >>> VersionPart('1')
      (1, None, 0, None)

      >>> VersionPart('1pre')
      (1, 'pre', 0, None)

      >>> VersionPart('1pre10')
      (1, 'pre', 10, None)

      >>> VersionPart('1pre10a')
      (1, 'pre', 10, 'a')

      >>> VersionPart('1+')
      (2, 'pre', 0, None)

      >>> VersionPart('*').numA == MAXINT
      True

      >>> VersionPart('1') < VersionPart('2')
      True

      >>> VersionPart('2') > VersionPart('1')
      True

      >>> VersionPart('1') == VersionPart('1')
      True

      >>> VersionPart('1pre') > VersionPart('1')
      False

      >>> VersionPart('1') < VersionPart('1pre')
      False

      >>> VersionPart('1pre1') < VersionPart('1pre2')
      True

      >>> VersionPart('1pre10b') > VersionPart('1pre10a')
      True

      >>> VersionPart('1pre10b') == VersionPart('1pre10b')
      True

      >>> VersionPart('1pre10a') < VersionPart('1pre10b')
      True

      >>> VersionPart('1') > VersionPart('')
      True
    '''

    _int_part = re.compile('[+-]?(\d*)(.*)')
    _num_chars = '0123456789+-'

    def __init__(self, part):
        self.numA = 0
        self.strB = None
        self.numC = 0
        self.extraD = None

        if not part:
            return

        if part == '*':
            self.numA = MAXINT
        else:
            match = self._int_part.match(part)
            self.numA = int(match.group(1))
            self.strB = match.group(2) or None
        if self.strB == '+':
            self.strB = 'pre'
            self.numA += 1
        elif self.strB:
            i = 0
            num_found = -1
            for char in self.strB:
                if char in self._num_chars:
                    num_found = i
                    break
                i += 1
            if num_found != -1:
                match = self._int_part.match(self.strB[num_found:])
                self.numC = int(match.group(1))
                self.extraD = match.group(2) or None
                self.strB = self.strB[:num_found]

    def __lt__(self, other):
        r = self.__cmp(other)
        return True if r<0 else False

    def __le__(self, other):
        r = self.__cmp(other)
        return True if r<=0 else False

    def __eq__(self, other):
        r = self.__cmp(other)
        return True if r==0 else False

    def __ge__(self, other):
        r = self.__cmp(other)
        return True if r>=0 else False

    def __gt__(self, other):
        r = self.__cmp(other)
        return True if r>0 else False

    def __ne__(self, other):
        r = self.__cmp(other)
        return True if r!=0 else False

    def _strcmp(self, str1, str2):
        # Any string is *before* no string.
        if str1 is None:
            if str2 is None:
                return 0
            else:
                return 1

        if str2 is None:
            return -1

        return cmp(str1, str2)

    def __cmp(self, other): # moved the comparison from __cmp__ to rich comparison methods of new style classes
        r = cmp(self.numA, other.numA)
        if r:
            return r

        r = self._strcmp(self.strB, other.strB)
        if r:
            return r

        r = cmp(self.numC, other.numC)
        if r:
            return r

        return self._strcmp(self.extraD, other.extraD)

    def __repr__(self):
        #return ' : '.join( (self.__class__.__name__, repr((self.numA, self.strB, self.numC, self.extraD))) )
        return repr((self.numA, self.strB, self.numC, self.extraD))

def compare(a, b):
    '''
    Examples:

      >>> compare('1', '2')
      -1

      >>> compare('1', '1')
      0

      >>> compare('2', '1')
      1

      >>> compare('1.0pre1', '1.0pre2')
      -1

      >>> compare('1.0pre2', '1.0')
      -1

      >>> compare('1.0', '1.0.0')
      0

      >>> compare('1.0.0', '1.0.0.0')
      0

      >>> compare('1.0.0.0', '1.1pre')
      -1

      >>> compare('1.1pre', '1.1pre0')
      0

      >>> compare('1.1pre0', '1.0+')
      0

      >>> compare('1.0+', '1.1pre1a')
      -1

      >>> compare('1.1pre1a', '1.1pre1')
      -1

      >>> compare('1.1pre1', '1.1pre10a')
      -1

      >>> compare('1.1pre10a', '1.1pre10')
      -1

      >>> compare('1.1pre10a', '1.*')
      -1
    '''

    a_parts = a.split('.')
    b_parts = b.split('.')

    if len(a_parts) < len(b_parts):
        a_parts.extend([''] * (len(b_parts) - len(a_parts)))
    else:
        b_parts.extend([''] * (len(a_parts) - len(b_parts)))

    for a_part, b_part in zip(a_parts, b_parts):
        r = cmp(VersionPart(a_part), VersionPart(b_part))
        if r:
            return r

    return 0

if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True)
