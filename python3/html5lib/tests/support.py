from __future__ import absolute_import, division, unicode_literals

import os
import sys
import codecs
import glob

base_path = os.path.split(__file__)[0]

if os.path.exists(os.path.join(base_path, 'testdata')):
    #release
    test_dir = os.path.join(base_path, 'testdata')
else:
    #development
    test_dir = os.path.abspath(
        os.path.join(base_path,
                     os.path.pardir, os.path.pardir,
                     os.path.pardir, 'testdata'))
    assert os.path.exists(test_dir), "Test data not found"
    #import the development html5lib
    sys.path.insert(0, os.path.abspath(os.path.join(base_path, 
                                                    os.path.pardir,
                                                    os.path.pardir)))

import html5lib
from html5lib import html5parser, treebuilders
del base_path

#Build a dict of avaliable trees
treeTypes = {"simpletree":treebuilders.getTreeBuilder("simpletree"),
             "DOM":treebuilders.getTreeBuilder("dom")}

#Try whatever etree implementations are avaliable from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes['lxml'] = treebuilders.getTreeBuilder("lxml")
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treebuilders.getTreeBuilder("beautifulsoup", fullTree=True)
except ImportError:
    pass

def get_data_files(subdirectory, files='*.dat'):
    return glob.glob(os.path.join(test_dir,subdirectory,files))

class DefaultDict(dict):
    def __init__(self, default, *args, **kwargs):
        self.default = default
        dict.__init__(self, *args, **kwargs)
    
    def __getitem__(self, key):
        return dict.get(self, key, self.default)

class TestData(object):
    def __init__(self, filename, newTestHeading="data", encoding="utf8"):
        if encoding == None:
            self.f = open(filename, mode="rb")
        else:
            self.f = codecs.open(filename, encoding=encoding)
        self.encoding = encoding
        self.newTestHeading = newTestHeading

    def __del__(self):
        self.f.close()
    
    def __iter__(self):
        data = DefaultDict(None)
        key=None
        for line in self.f:
            heading = self.isSectionHeading(line)
            if heading:
                if data and heading == self.newTestHeading:
                    #Remove trailing newline
                    data[key] = data[key][:-1]
                    yield self.normaliseOutput(data)
                    data = DefaultDict(None)
                key = heading
                data[key]="" if self.encoding else b""
            elif key is not None:
                data[key] += line
        if data:
            yield self.normaliseOutput(data)
        
    def isSectionHeading(self, line):
        """If the current heading is a test section heading return the heading,
        otherwise return False"""
        #print(line)
        if line.startswith("#" if self.encoding else b"#"):
            return line[1:].strip()
        else:
            return False
    
    def normaliseOutput(self, data):
        #Remove trailing newlines
        for key,value in data.items():
            if value.endswith("\n" if self.encoding else b"\n"):
                data[key] = value[:-1]
        return data

def convert(stripChars):
    def convertData(data):
        """convert the output of str(document) to the format used in the testcases"""
        data = data.split("\n")
        rv = []
        for line in data:
            if line.startswith("|"):
                rv.append(line[stripChars:])
            else:
                rv.append(line)
        return "\n".join(rv)
    return convertData

convertExpected = convert(2)

def errorMessage(input, expected, actual):
    msg = ("Input:\n%s\nExpected:\n%s\nRecieved\n%s\n" %
           (repr(input), repr(expected), repr(actual)))
    if sys.version_info.major == 2:
        msg = msg.encode("ascii", "backslashreplace")
    return msg
