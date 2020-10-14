'''
    PyElph - Utility class for handling processed data
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

from __future__ import with_statement
import hashlib
import os.path

from numpy import loadtxt


class DataStore:

    def __init__(self):
        self.reset()
        
    def reset(self, level=-1, force=False):
        if force or level == -1:
            self.modified = True
        
        if level == -1:
            # Initial
            self.imageName = None
            self.digest = None
            
        if level < 1 and self.modified:
            # Load page
            self.transform = []
            self.data = None #computed, not saved
        
        if level < 2 and self.modified:
            # Detect Lanes Page
            self.lanes = None
            self.laneWidth = -1
            self.maxDev = -1
            self.back = None #computed, not saved
        
        if level < 3 and self.modified:
            # Detect Bands Page
            self.bands = None
            self.filterThreshold = -1
            self.filterWidth = -1
            self.filterPasses = -1
        
        if level < 4 and self.modified:
            # Band Weight Page
            self.weightModel = None
            self.markerLanes = []
            self.marker = -1
            self.standard = None
            self.weights = None #computed, not saved
        
        if level < 5 and self.modified:
            # Match Bands Page
            self.bandMatchings = None
            self.distance = -1
        
        if level < 6 and self.modified:
            # Phylogenetic Tree View Page -- TODO: future
            self.tree = None
            self.dist = None
        
        # TODO: maybe do something else ----------------------------------------
        # aux
        if level == -1: # TODO better conditions
            self.selectedLane = -1
            self.selectedBand = -1
            self.showTreeDistanceLabels = False
            self.showBackgroundSubstraction = False
            
            self.laneLines = []
            self.bandLines = []
            self.bandMatchLines = []
            self.treeLines = []
            self.treeTexts = []
            
            self.laneNames = None
            self.laneLabels = None
            self.treeViewLims = None
        
        self.modified = False
#-------------------------------------------------------------------------------
        
    def isLoaded(self):
        return self.imageName != None
    
    def hasData(self):
        return self.isLoaded() and self.data != None
    
    def hasLanes(self):
        return self.hasData() and self.lanes != None and len(self.lanes) != 0
    
    def hasBands(self):
        return self.hasLanes() and self.bands != None and len(self.bands) != 0
    
    def hasWeights(self):
        return self.hasBands() and self.weights != None
    
    def hasStandard(self):
        return self.standard != None
    
    def hasMatching(self):
        return self.hasBands() and self.bandMatchings != None

    def hasTree(self):
        return self.hasMatching() and self.tree != None
    
    def hasLaneLabels(self):
        return self.laneLabels != None
    
    def generateLaneLabels(self):
        if self.hasLanes():
            self.laneLabels = []
            for i in range(len(self.lanes)):
                if i not in self.markerLanes:
                    self.laneLabels.append('Lane %2d' % (i+1))
    
    def cloneLaneNames(self):
        self.laneNames = self.laneLabels[:]

#-------------------------------------------------------------------------------

    def saveData(self):
        if not self.isLoaded() or not self.modified:
            return
        dataFilename = os.path.splitext(self.imageName)[0] + '.data'
        print 'Saving data to file:', dataFilename
        with open(dataFilename, 'w') as dataFile:
            print>>dataFile, 'Filename : "%s"' % self.imageName
#            print>>dataFile, 'Digest:', \
#                  ' '.join(map(lambda x: '{0:02X}'.format(ord(x)), self.digest))
            
            print>>dataFile, 'Transforms:', self.transform
        
            # Detect Lanes Page
            print>>dataFile, 'Lanes:', self.lanes
            print>>dataFile, 'Lane width:', self.laneWidth
            print>>dataFile, 'Lane width deviation:', self.maxDev

            # Detect Bands Page
            print>>dataFile, 'Bands:', self.bands
            print>>dataFile, 'Filter threshold:', self.filterThreshold
            print>>dataFile, 'Filter width:', self.filterWidth
            print>>dataFile, 'Filter passes:', self.filterPasses
        
            # Band Weight Page
            print>>dataFile, 'Weight model:', self.weightModel
            print>>dataFile, 'Marker lanes:', self.markerLanes
            print>>dataFile, 'Selected marker lane:', self.marker
            print>>dataFile, 'Standard:', self.standard
        
            # Match Bands Page
            print>>dataFile, 'Band match:', self.bandMatchings
            print>>dataFile, 'Band match distance', self.distance
        
            # Phylogenetic Tree Page
            print>>dataFile, 'Lane names:', self.laneNames
    
    def loadData(self): #TODO: to implement and use in future version
        pass
    
    def computeDigest(self, imageFile):
        md5 = hashlib.md5()
        with open(imageFile,'rb') as f: 
            for chunk in iter(lambda: f.read(8192), ''): # TODO: 128*md5.block_size 
                md5.update(chunk)
        self.digest = md5.digest()

#-------------------------------------------------------------------------------

    def getStandards(self):
        stdPath = os.path.join(os.getcwd(), 'standards')
        if not os.path.exists(stdPath):
            os.mkdir(stdPath)
            return []
#        print os.listdir(stdPath)
        standards = []
        for filename in os.listdir(stdPath):
            name, ext = os.path.splitext(filename)
            if ext.lower() == '.marker':
                standards.append(name)
        return standards
    
    def loadWeightStandard(self, filename):
        stdPath = os.path.join(os.getcwd(), 'standards', filename + '.marker')
        if not os.path.exists(stdPath):
            return None
        return loadtxt(stdPath, dtype='uint32')