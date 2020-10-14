'''
    PyElph - setup script for generating the Windows executable via py2exe
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

from distutils.core import setup
from distutils.filelist import findall
import os
import py2exe
import matplotlib


def dataFiles():
    resourcesdata_files = []
    
    resourcesdir = os.path.join(os.path.join(os.path.dirname(
                                os.path.realpath(__file__)),
                                'gui'), 'resources')
    resourcesdata = findall(resourcesdir)
    for f in resourcesdata:
        dirname = os.path.join('resources', f[len(resourcesdir)+1:])
        resourcesdata_files.append((os.path.split(dirname)[0], [f]))
    
    resourcesdir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'standards')
    resourcesdata = findall(resourcesdir)
    for f in resourcesdata:
        dirname = os.path.join('standards', f[len(resourcesdir)+1:])
        resourcesdata_files.append((os.path.split(dirname)[0], [f]))
    
    return matplotlib.get_py2exe_datafiles() + resourcesdata_files


setup(
      console    = ['src/PyElph.py'],
      data_files = dataFiles(),
      options = {'py2exe': {
                          'excludes': ['_gtkagg', '_tkagg'],
                }}
      )
