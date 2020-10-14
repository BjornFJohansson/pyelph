'''
    PyElph - Utility procedures for handling resources (icons, etc.) 
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

import sys, imp, os

def getResourcesDirectory():
    if (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") or # old py2exe
        imp.is_frozen("__main__")): # tools/freeze
        return os.path.join(os.path.dirname(sys.executable), 'resources')
    else:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')