'''
    PyElph - Software tool for gel image analysis and phylogenetics
    Copyright (C) 2012  Ana Brandusa Pavel <anabrandusa@gmail.com>,
                        Cristian Ioan Vasile <cristian.ioan.vasile@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

#PyElph
__version__ = '1.4'

#NumPy version
__numpy_version_req__ = (1, 6, 0)
__numpy_version_req_str__ = '>' + '.'.join(map(str, __numpy_version_req__))

#PIL version
__pil_version_req__ = (1, 1, 7)
__pil_version_req_str__ = '>' + '.'.join(map(str, __pil_version_req__))

#wxPython version
__wx_version_req__ = (2, 8, 0)
__wx_version_req_str__ = '>' + '.'.join(map(str, __wx_version_req__))

#matplotlib version
__mpl_version_req__ = (1, 0, 0)
__mpl_version_req_str__ = '>' + '.'.join(map(str, __mpl_version_req__))


import sys
import getopt
import string


def usage(msg=""):
    if msg: print msg
    print 'Usage:', sys.argv[0], '[options]'
    print 'options:'
    print '  -h | --help         - print help message'
    print '  -v | --version      - print version'


def help():
    usage()
    checkDependencies(True)
    sys.exit()


def parseArguments():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "version"])
    except getopt.GetoptError, err:
        usage(str(err))  # print help information and exit
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            help()
        elif o in ("-v", "--version"):
            print 'PyElph version:', __version__
        else:
            assert False, "unhandled option"
    
    return args


# version is a tuple or list of the format: (major, minor, revision)
def checkVersion(currentVersion, minReqVersion, maxReqVersion = None):
    # check major minimum requirement
    if currentVersion[0] < minReqVersion[0]:
        return False
    
    # check minor minimum requirement
    if currentVersion[0] == minReqVersion[0] \
       and currentVersion[1] < minReqVersion[1]:
        return False
    
    # check revision minimum requirement
    if currentVersion[0] == minReqVersion[0] \
       and currentVersion[1] == minReqVersion[1]\
       and currentVersion[2] < minReqVersion[2]:
        return False
    
    if not maxReqVersion:
        return True
    
    # check major maximum requirement
    if currentVersion[0] > maxReqVersion[0]:
        return False
    
    # check minor maximum requirement
    if currentVersion[0] == maxReqVersion[0] \
       and currentVersion[1] > maxReqVersion[1]:
        return False
    
    # check revision maximum requirement
    if currentVersion[0] == maxReqVersion[0] \
       and currentVersion[1] == maxReqVersion[1]\
       and currentVersion[2] > maxReqVersion[2]:
        return False
    
    return True


def checkDependencies(verbose=False):
    error = []
    
    # checking Python version
    if verbose:
        print 'Checking Python version:',
    if sys.version_info[0] == 2 and sys.version_info[1] >= 5:
        if verbose:
            print sys.version, 'OK'
    else:
        print 'Unsupported Python version!'
        print 'Please install Python version 2.5 or 2.6!'
        return True 
    
    # checking NumPy dependency
    if verbose:
        print 'Checking NumPy:',
    try:
        import numpy
    except ImportError:
        if verbose:
            print 'Not installed'
        error.append('NumPy ('+__numpy_version_req_str__+')')
    else:
        numpy_version = numpy.__version__.split('.')
        if not numpy_version[2].isdigit():
            idx = numpy_version[2].find(numpy_version[2].lstrip(string.digits))
            numpy_version[2] = numpy_version[2][:idx] 
        numpy_version = map(int, numpy_version)
        if checkVersion(numpy_version, __numpy_version_req__):
            if verbose:
                print 'OK'
        else:
            print 'Unsupported NumPy version!'
            error.append('NumPy ('+__numpy_version_req_str__+')')
    
    # checking PIL dependency
    if verbose:
        print 'Checking PIL:',
    try:
        import Image
    except ImportError:
        if verbose:
            print 'Not installed'
        error.append('PIL ('+__pil_version_req_str__+')')
    else:
        pil_version = map(int, Image.VERSION.split('.'))
        if checkVersion(pil_version, __pil_version_req__):
            if verbose:
                print 'OK'
        else:
            print 'Unsupported PIL version!'
            error.append('PIL ('+__pil_version_req_str__+')')
    
    # checking matplotlib dependency
    if verbose:
        print 'Checking matplotlib:',
    try:
        import matplotlib
    except ImportError:
        if verbose:
            print 'Not installed'
        error.append('matplotlib ('+__mpl_version_req_str__+')')
    else:
        mpl_version = map(int, matplotlib.__version__.split('.'))
        if checkVersion(mpl_version, __mpl_version_req__):
            if verbose:
                print 'OK'
        else:
            print 'Unsupported matplotlib version!'
            error.append('matplotlib ('+__mpl_version_req_str__+')')
            
    # checking wxPython dependency
    if verbose:
        print 'Checking wxPython:',
    try:
        import wx
    except ImportError:
        if verbose:
            print 'Not installed'
        error.append('wxPython ('+__wx_version_req_str__+')')
    else:
        wx_version = map(int, wx.__version__.split('.'))
        if checkVersion(wx_version, __wx_version_req__):
            if verbose:
                print 'OK'
        else:
            print 'Unsupported wxPython version!'
            error.append('wxPython ('+__wx_version_req_str__+')')
    
    if len(error) > 0:
        print 'Please install/upgrade the following packages for ',
        print 'Python version', sys.version,':', ', '.join(error)
        return False
    
    return True
        

if __name__ == '__main__':
    parseArguments()
    
    if not checkDependencies(True):
        sys.exit(1)
        
    from gui.GelAnalysisGUI import GelAnalysisApp

    app = GelAnalysisApp(redirect=False)
    app.MainLoop()