'''
    PyElph - Custom options panel and associated dialogs
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
import os
from copy import deepcopy

import wx
import wx.grid as wxgrid
from wx.lib.agw.floatspin import FloatSpin

from numpy import array, savetxt, loadtxt, transpose
from numpy.core.defchararray import replace

from analysis.BackgroundSubstraction import backgroundSubstraction
from analysis.Lane import extractLanes
from analysis.Bands import extractBands, bandMatching, computeMatchMatrix,\
    extractWeightsModel, computeWeights
from analysis.PhylTree import distanceMatrix, similarityMatrix, \
        computePhylogeneticTree, singleLinkage, completeLinkage, upgma, wpgma, \
        neighbourJoining#, centroid, median, ward

from gui.resources import getResourcesDirectory

resources = getResourcesDirectory()

def SetChoice(width, w, mode=None): #TODO: try to delete in future version
    if mode == None:
        mode = width.GetValue().rstrip(' :0123456789')
        width.SetValue(mode + ' : %d' % w)
    else:
        width.SetValue(width.choices[mode] + ' : %d' % w)

class EditLaneNamesDialog(wx.Dialog):
    
    def __init__(self, parent, id, lanes, labels=None, size=(240, 200), **kwargs):
        wx.Dialog.__init__(self, parent, id, size=size, title='Edit Lane Labels',
                           **kwargs)
        self.Centre()
        
        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(os.path.join(
                        resources, 'edit_lane_labels.png'))))
        
        if labels == None:
            self.labels = lanes[:]
        else:
            self.labels = labels
#        print self.labels
        
        mainBox = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, 'Lane Labels', size=(180, -1)),
                wx.HORIZONTAL)
        
        scrollPanel = wx.ScrolledWindow(self, wx.ID_ANY)
        scrollPanel.SetScrollRate(1, 1)
        
        panel = wx.Panel(scrollPanel, wx.ID_ANY)
        scrollVBox = wx.BoxSizer(wx.VERTICAL)

        for k, label in enumerate(self.labels):
#            print label
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            field = wx.StaticText(panel, wx.ID_ANY, lanes[k],
                             size=(40, -1), style=wx.ST_NO_AUTORESIZE | wx.LEFT)
            hbox.Add(field, 0, wx.ALIGN_CENTER | wx.ALL, 5)
            self.labels[k] = wx.TextCtrl(panel, wx.ID_ANY, label, size=(120, -1))
            hbox.Add(self.labels[k], 1, wx.ALIGN_CENTER | wx.ALL, 5)
            scrollVBox.Add(hbox, 0, wx.ALIGN_CENTER)

        panel.SetSizer(scrollVBox)
        
        abox = wx.BoxSizer(wx.VERTICAL)
        abox.Add(panel, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        scrollPanel.SetSizer(abox)

        hbox = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        
        box.Add(scrollPanel, 5, wx.ALIGN_CENTER | wx.EXPAND)
        mainBox.Add(box, 5, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        mainBox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(mainBox)
    
    def GetLaneNames(self):
        return map(lambda x: x.GetValue(), self.labels)

class CreateStandardDialog(wx.Dialog):
    
    def __init__(self, parent, id, stdPath=None, size=(240, 200), **kwargs):
        wx.Dialog.__init__(self, parent, id, size=size, title='Create Marker Standard',
                           **kwargs)
        self.Centre()
        
#        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(os.path.join(
#                        resources, 'edit_lane_labels.png'))))
        
        if stdPath == None or not os.path.exists(stdPath):
            dlg = wx.NumberEntryDialog(self.Parent,
                                       'Enter the number of bands',
                                       'Number', 'Define standard', 10, 1, 200)
            if dlg.ShowModal() == wx.ID_OK:
                nrWeights = dlg.GetValue()
            else:
                nrWeights = 0
            dlg.Destroy()
            self.weights = [1] * nrWeights
        else:
            self.weigths = loadtxt(stdPath, '%d')
        
#        print self.weights
        
        mainBox = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, 'Standard', size=(180, -1)),
                wx.HORIZONTAL)
        
        scrollPanel = wx.ScrolledWindow(self, wx.ID_ANY)
        scrollPanel.SetScrollRate(1, 1)
        
        panel = wx.Panel(scrollPanel, wx.ID_ANY)
        scrollVBox = wx.BoxSizer(wx.VERTICAL)

        for k, weight in enumerate(self.weights):
#            print weight
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            field = wx.StaticText(panel, wx.ID_ANY, 'Weight %d' % (k+1),
                             size=(60, -1), style=wx.ST_NO_AUTORESIZE | wx.LEFT)
            hbox.Add(field, 0, wx.ALIGN_CENTER | wx.ALL, 5)
#            self.weights[k] = wx.TextCtrl(panel, wx.ID_ANY, str(weight), size=(75, -1))
            self.weights[k] = wx.SpinCtrl(panel, wx.ID_ANY, min=1, max=10**6, initial=weight, size=(75, -1))
            hbox.Add(self.weights[k], 1, wx.ALIGN_CENTER | wx.ALL, 5)
            field = wx.StaticText(panel, wx.ID_ANY, 'bp',
                             size=(15, -1), style=wx.ST_NO_AUTORESIZE | wx.LEFT)
            hbox.Add(field, 0, wx.ALIGN_CENTER | wx.ALL, 5)
            scrollVBox.Add(hbox, 0, wx.ALIGN_CENTER)

        panel.SetSizer(scrollVBox)
        
        abox = wx.BoxSizer(wx.VERTICAL)
        abox.Add(panel, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        scrollPanel.SetSizer(abox)

        hbox = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        
        box.Add(scrollPanel, 5, wx.ALIGN_CENTER | wx.EXPAND)
        mainBox.Add(box, 5, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        mainBox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(mainBox)
    
    def ExistsStandard(self):
        return len(self.weights) != 0
    
    def CheckStandard(self):
        if len(self.weights) < 2:
            return True
        return all(map(lambda x, y: x.GetValue() > y.GetValue(), self.weights[:-1], self.weights[1:]))
    
    def GetWeights(self):
        return map(lambda x: long(x.GetValue()), self.weights)

class ViewWeightsDialog(wx.Dialog):
    
    def __init__(self, parent, id, weights, size=(512, 400), **kwargs):
        wx.Dialog.__init__(self, parent, id, size=size, title='View Molecular Weights',
                           **kwargs)
        self.Centre()
        
#        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(os.path.join(
#                        resources, 'edit_lane_labels.png'))))
        self.weights = weights
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
        gridBox = wx.BoxSizer(wx.HORIZONTAL)
        
        staticBox = wx.StaticBoxSizer(
              wx.StaticBox(self, wx.ID_ANY, 'Molecular Weights', size=(180, -1)),
              wx.HORIZONTAL)
        gridBox.Add(staticBox, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        self.grid = wxgrid.Grid(self, wx.ID_ANY)
        staticBox.Add(self.grid, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        # init heads and cells
        self.grid.CreateGrid(max(map(lambda w: len(w), weights)), len(weights))
        self.ResetMatchMatrix()
        
        hbox = self.CreateButtonSizer(wx.OK)
        
        self.Sizer.Add(gridBox, 5, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        self.Sizer.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
    
    def ResetMatchMatrix(self):
        self.grid.EnableDragGridSize(False)
        self.grid.EnableDragColSize(False)
        self.grid.EnableDragRowSize(False)
        self.grid.EnableEditing(False)
        
        self.grid.SetRowLabelSize(0)
        
#        for k in range(self.matchMatrix.shape[0]):
#            self.grid.SetRowLabelValue(k, 'Cluster %d' % (k+1))
        
        for k in range(len(self.weights)):
            self.grid.SetColLabelValue(k, 'Lane %d' % (k+1))
        
        for j, w in enumerate(self.weights):
            for i, val in enumerate(w):
                self.grid.SetCellValue(i, j, '%d' % val)
                self.grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)


class EditMatchMatrixDialog(wx.Dialog):
    
    def __init__(self, parent, id, matchMatrix, lanes, size=(512, 400), **kwargs):
        wx.Dialog.__init__(self, parent, id, size=size, title='Edit Match Matrix',
                           **kwargs)
        self.Centre()
        
#        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(os.path.join(
#                        resources, 'edit_lane_labels.png'))))
        self.matchMatrix = matchMatrix
        self.lanes = lanes
        self.selected = [0, 0, False]
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
        gridBox = wx.BoxSizer(wx.HORIZONTAL)
        
        staticBox = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, 'Match Matrix', size=(180, -1)),
                wx.HORIZONTAL)
        gridBox.Add(staticBox, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        self.grid = wxgrid.Grid(self, wx.ID_ANY)
        staticBox.Add(self.grid, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        self.Bind(wxgrid.EVT_GRID_CELL_LEFT_CLICK, self.OnClick, self.grid)
        
        # init heads and cells
        self.grid.CreateGrid(*self.matchMatrix.shape)
        self.ResetMatchMatrix()
        
        # buttons
        buttonsBox =wx.BoxSizer(wx.VERTICAL)
        gridBox.Add(buttonsBox, 0, wx.ALIGN_CENTER | wx.EXPAND)
        
        up = wx.BitmapButton(self, wx.ID_ANY,
                             wx.Bitmap(os.path.join(resources, 'up.png')))
        self.Bind(wx.EVT_BUTTON, self.OnUp, up)
        buttonsBox.Add(up, 0, wx.ALL, 5)
        
        down = wx.BitmapButton(self, wx.ID_ANY,
                               wx.Bitmap(os.path.join(resources, 'down.png')))
        self.Bind(wx.EVT_BUTTON, self.OnDown, down)
        buttonsBox.Add(down, 0, wx.ALL, 5)
        
        addAbove = wx.BitmapButton(self, wx.ID_ANY,
                            wx.Bitmap(os.path.join(resources, 'add_above.png')))
        self.Bind(wx.EVT_BUTTON, self.OnAddAbove, addAbove)
        buttonsBox.Add(addAbove, 0, wx.ALL, 5)
        
        addBelow = wx.BitmapButton(self, wx.ID_ANY,
                            wx.Bitmap(os.path.join(resources, 'add_below.png')))
        self.Bind(wx.EVT_BUTTON, self.OnAddBelow, addBelow)
        buttonsBox.Add(addBelow, 0, wx.ALL, 5)
        
        remove = wx.BitmapButton(self, wx.ID_ANY,
                            wx.Bitmap(os.path.join(resources, 'remove.png')))
        self.Bind(wx.EVT_BUTTON, self.OnRemove, remove)
        buttonsBox.Add(remove, 0, wx.ALL, 5)
        
        restart = wx.BitmapButton(self, wx.ID_ANY,
                            wx.Bitmap(os.path.join(resources, 'restart.png')))
        self.Bind(wx.EVT_BUTTON, self.OnRestart, restart)
        buttonsBox.Add(restart, 0, wx.ALL, 5)
        
        
        hbox = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        
        self.Sizer.Add(gridBox, 5, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        self.Sizer.Add(hbox, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
    
    def ResetMatchMatrix(self):
        self.grid.EnableDragGridSize(False)
        self.grid.EnableDragColSize(False)
        self.grid.EnableDragRowSize(False)
        self.grid.EnableEditing(False)
        
        for k in range(self.matchMatrix.shape[0]):
            self.grid.SetRowLabelValue(k, 'Cluster %d' % (k+1))
        
        for k, lane in enumerate(self.lanes):
            self.grid.SetColLabelValue(k, lane)
        
        for j in range(self.matchMatrix.shape[1]):
            k = 1
            for i in range(self.matchMatrix.shape[0]):
                if self.matchMatrix[i, j] == 1:
                    self.grid.SetCellValue(i, j, 'Band %d' % k)
                    k += 1
#                self.grid.SetReadOnly(i, j, True)
                self.grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
    
    def UpdateBands(self, bands):
        clusters = [[] for i in range(self.grid.NumberRows)]
        for j in range(self.grid.NumberCols):
            k = 0
            for i in range(self.grid.NumberRows):
                if len(self.grid.GetCellValue(i, j)) > 0:
                    bands[j][k][2] = i
                    clusters[i].append(bands[j][k])
                    k += 1
        return map(lambda cl: sorted(cl, lambda x, y: cmp(x[0], y[0])), clusters)
    
    def Deselect(self):
        if self.selected[2]:
            row, col = self.selected[:2]
            self.grid.SetCellBackgroundColour(row, col, wx.WHITE)
            self.selected = [0, 0, False]
            self.grid.Refresh()
    
    def OnClick(self, event):
#        print '!!!!!!!!!!!!!!!! On click', event
#        print 'pos:', (event.Col, event.Row)
#        for i in range(self.matchMatrix.shape[0]):
#            for j in range(self.matchMatrix.shape[1]):
#        print '-----------------------------------'
#        print 'Selected before:', self.selected
        if self.selected[2]:
#            print 'Set white bkgk', self.selected
            self.grid.SetCellBackgroundColour(self.selected[0],
                                              self.selected[1], wx.WHITE)
                
        if len(self.grid.GetCellValue(event.Row, event.Col)) > 0:
            self.selected = event.Row, event.Col, True
#            print 'Set red bkgk', self.selected
            self.grid.SetCellBackgroundColour(event.Row, event.Col, wx.RED)
        else:
            self.selected = event.Row, event.Col, False
        
#        print 'Selected after:', self.selected
        
        self.grid.Refresh()
        event.Skip()
    
    def OnUp(self, event):
        if self.selected[2]:
            row, col = self.selected[:2]
            if row != 0:
                if len(self.grid.GetCellValue(row-1, col)) == 0:
                    band = self.grid.GetCellValue(row, col)
                    self.grid.SetCellValue(row-1, col, band)
                    self.grid.SetCellValue(row, col, '')
                    
                    self.grid.SetCellBackgroundColour(row, col, wx.WHITE)
                    self.grid.SetCellBackgroundColour(row-1, col, wx.RED)
                    
                    self.selected = row-1, col, True
            
    def OnDown(self, event):
        if self.selected[2]:
            row, col = self.selected[:2]
            if row != self.grid.GetNumberRows()-1:
                if len(self.grid.GetCellValue(row+1, col)) == 0:
                    band = self.grid.GetCellValue(row, col)
                    self.grid.SetCellValue(row+1, col, band)
                    self.grid.SetCellValue(row, col, '')
                    
                    self.grid.SetCellBackgroundColour(row, col, wx.WHITE)
                    self.grid.SetCellBackgroundColour(row+1, col, wx.RED)
                    
                    self.selected = row+1, col, True
        
    def OnAddAbove(self, event):
#        print 'add above'
        row = self.selected[0]
        self.Deselect()
        self.grid.InsertRows(row)
        
        for j in range(self.grid.NumberCols):
            self.grid.SetCellAlignment(row, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        
        for k in range(row, self.grid.NumberRows):
            self.grid.SetRowLabelValue(k, 'Cluster %d' % (k+1))

    def OnAddBelow(self, event):
#        print 'add below'
        row = self.selected[0] + 1
        self.Deselect()
        self.grid.InsertRows(row)
        
        for j in range(self.grid.NumberCols):
            self.grid.SetCellAlignment(row, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        
        for k in range(row, self.grid.NumberRows):
            self.grid.SetRowLabelValue(k, 'Cluster %d' % (k+1))
    
    def OnRemove(self, event):
#        print 'add remove'
        row = self.selected[0]
        if any([len(self.grid.GetCellValue(row, i)) != 0 for i in range(self.grid.NumberCols)]):
            msgDialog = wx.MessageDialog(self.Parent,
                                         'The cluster is not empty!', 'Warning',
                                         style=wx.OK | wx.ICON_WARNING)
            msgDialog.ShowModal()
            msgDialog.Destroy()
        else:
            self.grid.DeleteRows(row)
            for k in range(row, self.grid.NumberRows):
                self.grid.SetRowLabelValue(k, 'Cluster %d' % (k+1))
    
    def OnRestart(self, event):
        self.grid.ClearGrid()
        self.Deselect()
        err = self.grid.GetNumberRows() - self.matchMatrix.shape[0]
        if err > 0:
            self.grid.DeleteRows(numRows=err)
        elif err < 0:
            self.grid.InsertRows(numRows=-err)
        
        self.ResetMatchMatrix()


class OptionWindow(wx.Panel):
    
    steps = [
        {'title' : 'Load Image',
         'description': 
'1. Load image \r\n2. Zoom \r\n3. Edit the image if it is necessary: rotate, crop \r\n 4. Save current view',
         'init' : lambda x, y: x.LoadPage(y)
        },
        {'title' : 'Lane Detection',
         'description':
'1. "Detect" button is for automatic lane detection \r\n2. If automatic lane detection does not work properly, you can: \r\n  a. manually select or remove lanes \r\n  b. manually define the lane width using the yellow button and then try the "Detect" button again \r\n  c. the "width deviation" parameter is the percentage that the detected lanes can vary from the medium lane width (found automatically) or from the manually defined width (for the manually defined width, the parameter should have a small value like 10% for a good accuracy) \r\n3. After the lanes are detected you can apply the background substraction filter in order to filter the noise and highlight the bands',
         'init' : lambda x, y: x.LaneDetectionPage(y)
        },
        {'title' : 'Band Detection',
         'description':
'1. "Detect" button is for automatic band detection \r\n2. If automatic band detection does not work properly, you can: \r\n  a. manually select or remove bands \r\n  b. the intensity "threshold" - the smaller value it gets, the more bands are detected \r\n  c. The moving average filter eliminates the noise caused by the false intensity peaks. The filter width determines how many values are used to compute the average for the current position as follows:\r\n xF[i] = (x[i-width] + ... + x[i-1] + x[i] + x[i+1] + ... + x[i+width])/ (2*width+1).\n\r The passes filter parameter represents the number of times the filter is applied on the data. For small images the recommended filter width is 1 and the number of "filter passes" can be between 0-3, for larger images like: \r\n aprox. 600x400, recommended filter width: 2 and "filter passes": 5; \r\n aprox. 4000x3000, recommended "filter width": 3 and "filter passes": 10 ',
         'init' : lambda x, y: x.BandDetectionPage(y)
        },
        {'title' : 'Molecular Weight',
         'description':
'1. You must select the lanes which are weight markers in the gel image \r\n2. Select an existing standard or define a new one (when a new standard is defined, the bands must be introduced in a decreasing order of the weight). The new defined standard is saved in a .marker file in the directory "standards" and it is available in the interface for future use.\r\n3. "Compute" button computes the weight for all the fragments in the gel\r\n4. "Export" button saves the results in a file \r\n5. "View" button displays the results',
         'init' : lambda x, y: x.BandWeightPage(y)
        },
        {'title' : 'Band Matching',
         'description':
'1. "Match" button computes the clusters of matched bands \r\n2. You can adjust band matching by changing the "distance" parameter which represents the distance that two bands are considered to be in the same cluster \r\n3. "Edit" buttons allows the modification of the clustering method: move a band from a cluster to a neighbor cluster, add or remove a cluster \r\n4. "Export" button saves the matrix in a file in 1/0 format or +/- format',
         'init' : lambda x, y: x.BandsMatchingPage(y)
        },
        {'title' : 'Phylogenetic Tree',
         'description':
'1. Select the method for tree computation \r\n 2. "View" button displays the tree \r\n3. Check the "Distance labels" if you want to display the genetic distance on the branches \r\n4. "Edit Lane Labels" button allows to rename the labels for the analyzed population (after changing a the labels press "View" button to see the change)',
         'init' : lambda x, y: x.PhylogeneticTreePage(y),
         'methods' : {'Neighbour Joining' : neighbourJoining,
                      'Single Linkage' : singleLinkage,
                      'Complete Linkage' : completeLinkage,
                      'UPGMA' : upgma,
                      'WPGMA' : wpgma,
#                      'Centroid' : centroid, #TODO: negative branch distance
#                      'Median' : median, #TODO: negative branch distance
#                      'Ward' : ward #TODO: negative branch distance
                     }, 
         'defaultMethod' : 'Neighbour Joining'
        }
    ]
    
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.step = 0
        
        # add title
        self.stepTitle = wx.StaticText(self, wx.ID_ANY, '', size=(200, -1),
                                    style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
        self.stepTitle.SetFont(wx.Font(14, family=wx.FONTFAMILY_ROMAN,
                                       weight=wx.FONTWEIGHT_BOLD,
                                       style=wx.FONTSTYLE_NORMAL))
        self.Sizer.Add(self.stepTitle, 0, wx.ALL, 5)
        
        box = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, 'Description', size=(200, -1)),
                wx.HORIZONTAL)
        self.Sizer.Add(box, 1, wx.ALL, 5)
        
        self.description = wx.TextCtrl(self, wx.ID_ANY, size=(180, 100),
                        style=wx.TE_READONLY | wx.TE_BESTWRAP | wx.TE_MULTILINE)
        self.description.SetFont(wx.Font(12, family=wx.FONTFAMILY_ROMAN,
                                       weight=wx.FONTWEIGHT_NORMAL,
                                       style=wx.FONTSTYLE_NORMAL))
        box.Add(self.description, 1, wx.ALL | wx.EXPAND | wx.CENTER, 5)
        
        # add parameters page
        self.parametersBox = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, 'Parameters', size=(200, -1)),
                wx.VERTICAL)
        self.Sizer.Add(self.parametersBox, 1, wx.ALL | wx.EXPAND | wx.CENTER, 5)
        
        for step in self.steps:
            scrollPanel = wx.ScrolledWindow(self, wx.ID_ANY)
            scrollPanel.SetScrollRate(1, 1)
            scrollPanel.Sizer = wx.BoxSizer(wx.VERTICAL)
            
            step['parameters'] = scrollPanel
            step['init'](self, scrollPanel)
            
            self.parametersBox.Add(scrollPanel, 1, wx.EXPAND)
        
        # add next and previous page buttons
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.prev = wx.BitmapButton(self, wx.ID_ANY,
                                 wx.Bitmap(os.path.join(resources, 'prev.png')))
        sizer.Add(self.prev, 0, wx.ALL, 5)
        self.prev.Show(False)
        
        self.next = wx.BitmapButton(self, wx.ID_ANY,
                                 wx.Bitmap(os.path.join(resources, 'next.png')))
        self.next.SetDefault()
        sizer.Add(self.next, 0, wx.ALL, 5)
        
        self.Sizer.Add(sizer, 0, wx.CENTER)
        
        self.ShowPage()
        
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prev)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.next)
    
    def OnPrev(self, event): #TODO:
        if self.step == 1: # bands page
            dlg = wx.MessageDialog(self.Parent,
                                   'Do you really want to reset lane data?',
                                   'Reset data')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
        elif self.step == 2: # bands page
            dlg = wx.MessageDialog(self.Parent,
                                   'Do you really want to reset band data?',
                                   'Reset data')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
        
        wx.BeginBusyCursor()
        self.Parent.imagePanel.toolbar.deactivate()
        if self.step == 1:
            self.Parent.imagePanel.toolbar.ShowTools(('open', 'crop', 'rotate'))
            self.Parent.imagePanel.toolbar.ShowTools(('addLane', 'removeLane',
                                                     'defineLaneWidth'), False)
        elif self.step == 2:
            self.Parent.imagePanel.toolbar.ShowTools(('addLane', 'removeLane',
                                                     'defineLaneWidth'))
            self.Parent.imagePanel.toolbar.ShowTools(('addBand', 'removeBand'),
                                                     False)
        elif self.step == 3:
            self.Parent.imagePanel.toolbar.ShowTools(('addBand', 'removeBand'))
        
        if self.step == 1:
#            print 'restore image with background'
            self.Parent.imagePanel.RestoreBackground(all=False)
#            print 'clear lane spectrum'
            self.Parent.imagePanel.SetLaneSpectrum(clear=True)
#            print 'clear lane lines, if any'
            self.Parent.imagePanel.SetLaneLines([])
#            print 'reset controls' # TODO: init properly in future version
            self.steps[1]['laneWidth'].SetChoice(0, 'auto')
            self.steps[1]['maxDev'].SetValue(25)
            self.steps[1]['background'].SetValue(False)
        elif self.step == 2:
#            print 'clear band points, if any'
#            print self.Parent.dataStore.hasLanes(), self.Parent.dataStore.lanes
            self.Parent.imagePanel.SetBands([])
#            print self.Parent.dataStore.hasLanes(), self.Parent.dataStore.lanes
#            print 'reset controls' # TODO: init properly in future version
            self.steps[2]['filterThreshold'].SetValue(20)
            self.steps[2]['filterWidth'].SetValue(3)
            self.steps[2]['filterPasses'].SetValue(10)
        elif self.step == 3:
#            print 'reset controls' # TODO: init properly in future version
            self.steps[3]['model'].SetSelection(0)
        elif self.step == 4:
#            print 'clear band match lines, if any'
            self.Parent.imagePanel.SetBandClusters([])
#            print 'reset controls' # TODO: init properly in future version
            self.steps[4]['distance'].SetValue(2.0)
        elif self.step == 5:
#            print 'clear tree, if any and restore everything else'
            self.Parent.imagePanel.SetImage()
            self.Parent.imagePanel.SetLaneSpectrum()
            self.Parent.imagePanel.SetLaneLines(self.Parent.dataStore.lanes)
            self.Parent.imagePanel.SetBands(self.Parent.dataStore.bands)
            self.Parent.imagePanel.SetBandClusters(self.Parent.dataStore.clusters)
            self.Parent.dataStore.treeLines = []
            self.Parent.dataStore.treeTexts = []
            self.Parent.dataStore.showTreeDistanceLabels = False
#            print 'reset controls' # TODO: init properly in future version
            self.steps[5]['distanceLabels'].SetValue(False)
            self.steps[5]['method'].SetSelection(self.steps[5]['method']\
                                    .FindString(self.steps[5]['defaultMethod']))
        
        self.Parent.dataStore.modified = True #TODO: remove in future version
        self.Parent.dataStore.reset(self.step)
        self.step = max(0, self.step-1)
        self.ShowPage()
        wx.EndBusyCursor()
    
    def OnNext(self, event): #TODO:
        wx.BeginBusyCursor()
        self.Parent.imagePanel.toolbar.deactivate()
        
        if self.step == 0 and self.Parent.imagePanel.ShowNoImageWarning():
            wx.EndBusyCursor()
            return
        elif self.step == 1 and self.Parent.imagePanel.ShowNoLanesWarning():
            wx.EndBusyCursor()
            return
        elif self.step == 2:
            if self.Parent.imagePanel.ShowNoBandsWarning() \
               or self.Parent.imagePanel.ShowEmptyLanesWarning():
                    wx.EndBusyCursor()
                    return
        elif self.step == 4 and self.Parent.imagePanel.ShowNoMatchingWarning():
            wx.EndBusyCursor()
            return
        
        if self.step == 0:
            self.Parent.imagePanel.toolbar.ShowTools(('open', 'crop', 'rotate'),
                                                     False)
            self.Parent.imagePanel.toolbar.ShowTools(('addLane', 'removeLane',
                                                     'defineLaneWidth'))
        elif self.step == 1:
            self.Parent.imagePanel.toolbar.ShowTools(('addLane', 'removeLane',
                                                      'defineLaneWidth'), False)
            self.Parent.imagePanel.toolbar.ShowTools(('addBand', 'removeBand'))
        elif self.step == 2:
            self.Parent.imagePanel.toolbar.ShowTools(('addBand', 'removeBand'),
                                                    False)
        
        if self.step == 0:
            self.Parent.imagePanel.SaveImageWithBackground()
            self.Parent.imagePanel.SetLaneSpectrum()
        
        if self.step == 1:
            back = self.Parent.dataStore.back
            if self.Parent.dataStore.modified or back.size == 0:
                data = self.Parent.dataStore.data
                back = backgroundSubstraction(data, self.Parent.dataStore.lanes)
                self.Parent.dataStore.back = back

        if self.step == 2:
            self.steps[3]['marker'].SetItems(['Lane %d' % (k+1)
                              for k in range(len(self.Parent.dataStore.lanes))])
        
        if self.step == 3:
            markerWidget = self.steps[3]['marker']
            self.Parent.dataStore.markerLanes = markerWidget.GetChecked() 

        if self.step == 4:
            self.Parent.dataStore.cloneLaneNames()
            self.Parent.dataStore.laneLines = []
            self.Parent.dataStore.bandLines = []
            self.Parent.dataStore.bandMatchLines = []
        if self.step == 5:
            dlg = wx.MessageDialog(self.Parent,
                                   'Do you really want to reset all data?',
                                   'Reset data')
            if dlg.ShowModal() == wx.ID_OK:
                self.Parent.dataStore.reset()
                
                #TODO: reset method
                self.Parent.imagePanel.originalImage = None
                self.Parent.imagePanel.image = None
                self.Parent.imagePanel.imageWithBackg = None
                self.Parent.imagePanel.data = None
                self.Parent.imagePanel.imagePort.clear()
                self.Parent.imagePanel.laneSpectrum.clear()
                self.Parent.imagePanel.laneLevels.clear()
                self.Parent.imagePanel.OnPaint(None)
                
                self.Parent.imagePanel.toolbar.ShowTools(('open', 'crop', 'rotate'))
                
                # TODO: init properly in future version
                self.steps[1]['background'].SetValue(False)
                self.steps[1]['laneWidth'].SetChoice(0, 'auto')
                self.steps[1]['maxDev'].SetValue(25)
                
                self.steps[2]['filterThreshold'].SetValue(20)
                self.steps[2]['filterWidth'].SetValue(3)
                self.steps[2]['filterPasses'].SetValue(10)
                
                self.steps[5]['distanceLabels'].SetValue(False)
                method = self.steps[5]['method']
                method.SetSelection(method.FindString(self.steps[5]['defaultMethod']))
                
                self.Parent.statusBar.SetStatusText('No image specified', 0)
                
                self.step = -1
            dlg.Destroy()
                
        
        self.step = min(len(self.steps)-1, (self.step+1))
#        self.Parent.dataStore.reset(self.step) #TODO: for future use
#        self.Parent.dataStore.saveData()
        self.ShowPage()
        wx.EndBusyCursor()
    
    def ShowPage(self):
        self.stepTitle.SetLabel(self.steps[self.step]['title'])
        self.description.SetLabel(self.steps[self.step]['description'])
        
        for step in self.steps:
            step['parameters'].Show(False)
        self.steps[self.step]['parameters'].Show(True)
        
        if self.step == 0:
            self.prev.Show(False)
            self.next.Show()
#        elif self.step == len(self.steps)-1:
#            self.prev.Show()
#            self.next.Show(False)
        else:
            self.prev.Show()
            self.next.Show()
        self.Sizer.Layout()
    
    #---------------------------------------------------------------------------
    
    def LoadPage(self, scrollPanel): pass
    
    def LaneDetectionPage(self, scrollPanel):
        # lane width
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Lane width',
                              size=(80, -1), style=wx.ST_NO_AUTORESIZE)
        field.Wrap(80)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        width = wx.TextCtrl(scrollPanel, wx.ID_ANY, size=(90, -1))
        width.choices = {'auto' : 'Auto', 'manual' : 'Manual'}
        width.choice = 'auto'
        width.SetChoice = lambda w, mode=None: SetChoice(width, w, mode) #TODO: not good
        width.SetChoice(0, 'auto')
        width.Enable(False)
        self.steps[1]['laneWidth'] = width
        box.Add(width, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # max deviation
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Width deviation',
                              size=(80, -1), style=wx.ST_NO_AUTORESIZE)
        field.Wrap(80)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        maxDev = wx.SpinCtrl(scrollPanel, wx.ID_ANY, min=1, max=100,
                             initial=25, size=(60, -1)) 
        self.steps[1]['maxDev'] = maxDev
        box.Add(maxDev, 0, wx.ALL | wx.CENTER)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, '%',
                              size=(15, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # background
        bkgr = wx.CheckBox(scrollPanel, wx.ID_ANY, 'Background substraction', size=(160, -1))
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBackground, bkgr) 
        self.steps[1]['background'] = bkgr
        scrollPanel.Sizer.Add(bkgr, 0, wx.ALL | wx.CENTER, 5)
        
        # detect lane button
        detect = wx.Button(scrollPanel, wx.ID_ANY, 'Detect', size=(60, 30))
        self.Bind(wx.EVT_BUTTON, self.OnDetectLanes, detect)
        self.steps[1]['detect'] = detect
        scrollPanel.Sizer.Add(detect, 0, wx.ALL | wx.CENTER, 5)
            
    def BandDetectionPage(self, scrollPanel):
        # filter threshold
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Threshold',
                              size=(65, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        threshold = wx.SpinCtrl(scrollPanel, wx.ID_ANY, min=0, max=255,
                            initial=20, size=(60, -1))
        self.steps[2]['filterThreshold'] = threshold
        box.Add(threshold, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # filter width
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Filter width',
                              size=(65, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        width = wx.SpinCtrl(scrollPanel, wx.ID_ANY, min=1, max=15,
                            initial=3, size=(60, -1))
        self.steps[2]['filterWidth'] = width
        box.Add(width, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # filter passes
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Filter passes',
                              size=(65, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        passes = wx.SpinCtrl(scrollPanel, wx.ID_ANY, min=0, max=50,
                            initial=10, size=(60, -1))
        self.steps[2]['filterPasses'] = passes
        box.Add(passes, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # detect band button
        detect = wx.Button(scrollPanel, wx.ID_ANY, 'Detect', size=(60, 30))
        self.Bind(wx.EVT_BUTTON, self.OnDetectBands, detect)
        self.steps[2]['detect'] = detect
        scrollPanel.Sizer.Add(detect, 0, wx.ALL | wx.CENTER, 5)
    
    def BandWeightPage(self, scrollPanel):
        # select marker lane
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Markers',
                              size=(60, -1), style=wx.ST_NO_AUTORESIZE)
        field.Wrap(60)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        marker = wx.CheckListBox(scrollPanel, wx.ID_ANY, size=(100, 60)) 
        self.steps[3]['marker'] = marker
        box.Add(marker, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # select model / add new model
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Standard', size=(60, -1),
                              style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        model = wx.Choice(scrollPanel, wx.ID_ANY, size=(100, -1),
                          choices=self.Parent.dataStore.getStandards() + ['Add New Standard'])
        model.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChooseStandard, model)
        self.steps[3]['model'] = model
        box.Add(model, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        # compute band weight
        compute = wx.Button(scrollPanel, wx.ID_ANY, 'Compute', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnComputeBandWeights, compute)
        self.steps[3]['computeWeights'] = compute
        box.Add(compute, 0, wx.ALL | wx.CENTER, 3)
        
        # edit bands match button
        view = wx.Button(scrollPanel, wx.ID_ANY, 'View', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnViewBandWeights, view)
        self.steps[3]['viewWeights'] = view
        box.Add(view, 0, wx.ALL | wx.CENTER, 3)
        
        # export bands match button
        export = wx.Button(scrollPanel, wx.ID_ANY, 'Export', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnExportBandWeights, export)
        self.steps[3]['exportWeights'] = export
        box.Add(export, 0, wx.ALL | wx.CENTER, 3)
        
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 0)
    
    def BandsMatchingPage(self, scrollPanel):
        # band distance
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Distance',
                              size=(95, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        dist = FloatSpin(scrollPanel, wx.ID_ANY, min_val=0.1, max_val=10,
                         value=2, increment=0.1, digits=1, size=(60, -1))
        self.steps[4]['distance'] = dist
        box.Add(dist, 0, wx.ALL | wx.CENTER)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, '%',
                              size=(15, -1), style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        # match bands button
        match = wx.Button(scrollPanel, wx.ID_ANY, 'Match', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnMatchBands, match)
        self.steps[4]['match'] = match
        box.Add(match, 0, wx.ALL | wx.CENTER, 3)
        
        # edit bands match button
        edit = wx.Button(scrollPanel, wx.ID_ANY, 'Edit', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnEditBandMatch, edit)
        self.steps[4]['editMatch'] = edit
        box.Add(edit, 0, wx.ALL | wx.CENTER, 3)
        
        # export bands match button
        export = wx.Button(scrollPanel, wx.ID_ANY, 'Export', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnExportBandMatch, export)
        self.steps[4]['exportMatch'] = export
        box.Add(export, 0, wx.ALL | wx.CENTER, 3)
        
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 0)
    
    def PhylogeneticTreePage(self, scrollPanel):
        # tree distances labels
        distLabels = wx.CheckBox(scrollPanel, wx.ID_ANY, 'Distance Labels',
                                 size=(160, -1))
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckTreeDistanceLabels, distLabels) 
        self.steps[5]['distanceLabels'] = distLabels
        scrollPanel.Sizer.Add(distLabels, 0, wx.ALL | wx.CENTER, 5)
        
        # tree generation method
        box = wx.BoxSizer(wx.HORIZONTAL)
        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Method', size=(40, -1),
                              style=wx.ST_NO_AUTORESIZE)
        box.Add(field, 0, wx.ALL | wx.CENTER)
        method = wx.Choice(scrollPanel, wx.ID_ANY, size=(120, -1),
                          choices=sorted(self.steps[5]['methods'].keys()))
        method.SetSelection(method.FindString(self.steps[5]['defaultMethod']))
        self.steps[5]['method'] = method
        box.Add(method, 0, wx.ALL | wx.CENTER)
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
#        # tree display method # TODO: future version
#        box = wx.BoxSizer(wx.HORIZONTAL)
#        field = wx.StaticText(scrollPanel, wx.ID_ANY, 'Display', size=(40, -1),
#                              style=wx.ST_NO_AUTORESIZE)
#        box.Add(field, 0, wx.ALL | wx.CENTER)
#        display = wx.Choice(scrollPanel, wx.ID_ANY, size=(120, -1),
#                          choices=('Model 1', 'Model 2', 'Model 3')) #TODO: add choices
#        display.SetSelection(0)
#        self.steps[5]['display'] = display
#        box.Add(display, 0, wx.ALL | wx.CENTER)
#        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 5)
        
        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        # view phylogenetic tree
        viewButton = wx.Button(scrollPanel, wx.ID_ANY, 'View', size=(50, 30))
        self.Bind(wx.EVT_BUTTON, self.OnViewPhylTree, viewButton)
        self.steps[5]['view'] = viewButton
        box.Add(viewButton, 0, wx.ALL | wx.CENTER, 5)

        # Edit Tree Lane Labels
        editLaneLabels = wx.Button(scrollPanel, wx.ID_ANY, 'Edit Lane Labels',
                               size=(100, 30))
        self.Bind(wx.EVT_BUTTON, self.OnEditTreeLaneLabels, editLaneLabels)
        self.steps[5]['editLaneLabels'] = editLaneLabels
        box.Add(editLaneLabels, 0, wx.ALL | wx.CENTER, 5)
        
        scrollPanel.Sizer.Add(box, 0, wx.ALL | wx.LEFT, 0)
        
#        # export tree #TODO: future version
#        export = wx.Button(scrollPanel, wx.ID_ANY, 'Export', size=(60, 30))
#        self.Bind(wx.EVT_BUTTON, self.OnExportPhylTree, export)
#        self.steps[5]['export'] = export
#        scrollPanel.Sizer.Add(export, 0, wx.ALL | wx.CENTER, 5)
    
#-------------------------------------------------------------------------------
    
    def OnDetectLanes(self, event):
        if self.Parent.dataStore.hasLanes():
            dlg = wx.MessageDialog(self.Parent,
                                  'This operation will reset all lane data.\r\n'
                                  + 'Are you sure you want to continue?',
                                  'Reset data')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
        
        wx.BeginBusyCursor()
        
        data = self.Parent.dataStore.data
        
        maxDev = self.steps[1]['maxDev'].GetValue() / 100.0
        meanLW = None
        if self.Parent.dataStore.laneWidth > 0:
            meanLW = self.Parent.dataStore.laneWidth
        
#        print 'Saved lane width:', self.Parent.dataStore.laneWidth
#        print maxDev, meanLW

        # reset background substraction
        self.steps[1]['background'].SetValue(False)
        self.Parent.imagePanel.RestoreBackground(False)
        self.Parent.dataStore.showBackgroundSubstraction = False
        
        lanes, meanLW = extractLanes(data, maxDev, meanLaneWidth=meanLW)
#        print lanes

        if len(lanes) == 0:
            self.Parent.imagePanel.ShowWarning('No lanes were detected!')
            wx.EndBusyCursor()
            return
        
        self.steps[1]['laneWidth'].SetChoice(meanLW)
        
#        print 'Computed lane width:', meanLW 
        
        self.Parent.dataStore.lanes = lanes
        self.Parent.dataStore.laneWidth = meanLW
        self.Parent.dataStore.maxDev = maxDev
        
        # save image without background
        self.Parent.dataStore.back = backgroundSubstraction(data, lanes)
        
        self.Parent.dataStore.modified = True

        self.Parent.imagePanel.SetLaneLines(lanes)
        self.Parent.imagePanel.SetLaneSpectrum()
        
        wx.EndBusyCursor()

    def OnCheckBackground(self, event):
        show = self.steps[1]['background'].GetValue()
        
        if not self.Parent.imagePanel.ShowNoLanesWarning():
            wx.BeginBusyCursor()
            if show: 
                self.Parent.imagePanel.RemoveBackground(backgroundSubstraction)
            else:
                self.Parent.imagePanel.RestoreBackground()
            self.Parent.dataStore.showBackgroundSubstraction = show
            wx.EndBusyCursor()
        else:
            self.steps[1]['background'].SetValue(False)

#-------------------------------------------------------------------------------

    def OnDetectBands(self, event):
        if self.Parent.dataStore.hasBands():
            dlg = wx.MessageDialog(self.Parent,
                                 'This operation will reset all band data. \r\n'
                                 + 'Are you sure you want to continue?',
                                 'Reset data')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
        wx.BeginBusyCursor()
        
        lanes = self.Parent.dataStore.lanes
        back = self.Parent.dataStore.back
        
        filterTh = self.steps[2]['filterThreshold'].GetValue()
        filterW = self.steps[2]['filterWidth'].GetValue()
        filterP = self.steps[2]['filterPasses'].GetValue()
        
#        print filterTh, filterW, filterP
        
        bands = extractBands(back, lanes, filterTh, filterW, filterP)
#        print bands
        
        self.Parent.dataStore.bands = bands
        self.Parent.dataStore.filterThreshold = filterTh
        self.Parent.dataStore.filterWidth = filterW
        self.Parent.dataStore.filterPasses = filterP
        
        self.Parent.dataStore.modified = True
        
        self.Parent.imagePanel.SetBands(bands)
        
        wx.EndBusyCursor()

#-------------------------------------------------------------------------------
    def OnChooseStandard(self, event): #TODO: redo this in future version - needs clean up
        model = self.steps[3]['model']
        if model.CurrentSelection == model.GetCount() - 1: # choose add new
            dlg = CreateStandardDialog(self, wx.ID_ANY)
            if dlg.ExistsStandard():
#                print 'Ok standard', dlg.ExistsStandard()
                if dlg.ShowModal() == wx.ID_OK:
#                    print 'Print check:', not dlg.CheckStandard()
                    while not dlg.CheckStandard():
                        dlgWarn = wx.MessageDialog(self.Parent,
                            'The mass data is not well defined!', 'Warning',
                            wx.OK | wx.ICON_WARNING)
                        dlgWarn.ShowModal()
                        dlgWarn.Destroy()
                        if dlg.ShowModal() != wx.ID_OK:
                            model.SetSelection(0)
                            dlg.Destroy()
                            return
#                        print 'Print int check:', not dlg.CheckStandard()

                    textDlg = wx.TextEntryDialog(self, 'Enter standard name',
                                       'Save standard', defaultValue='standard')
                    if textDlg.ShowModal() == wx.ID_OK:
                        filename = os.path.join(os.getcwd(), 'standards', textDlg.GetValue() + '.marker')
                        savetxt(filename, array(dlg.GetWeights()), '%d')
                        
                        model.Insert(textDlg.GetValue(), model.GetCount() - 1)
                        model.SetSelection(model.GetCount() - 2)
                    else:
                        model.SetSelection(0)
                    textDlg.Destroy()
                else:
                    model.SetSelection(0)
            else:
                model.SetSelection(0)
            dlg.Destroy()
        
    def OnComputeBandWeights(self, event):
#        print 'here compute band weights'
        
        stdWidget = self.steps[3]['model']
        if stdWidget.GetCount() == 1:
            self.Parent.imagePanel.ShowWarning('Create a standard first!')
            return
        std = self.Parent.dataStore.loadWeightStandard(
                                               stdWidget.GetStringSelection())
        if std == None:
            self.Parent.imagePanel.ShowError('Error loading standard!')
            return
        
        markerWidget = self.steps[3]['marker']
        self.Parent.dataStore.markerLanes = markerWidget.GetChecked()
        if len(self.Parent.dataStore.markerLanes) > 0:
#            print 'Choices:', markerWidget.GetCheckedStrings()
            dlg = wx.SingleChoiceDialog(self.Parent, 'Select marker lane',
                          'Marker lane', list(markerWidget.GetCheckedStrings()))
            if dlg.ShowModal() == wx.ID_OK:
#                print 'Ok sel:', dlg.GetStringSelection(), 'Idx:', dlg.GetSelection()
                marker = self.Parent.dataStore.markerLanes[dlg.GetSelection()]
                bands = self.Parent.dataStore.bands
                if len(bands[marker]) == len(std):
                    wx.BeginBusyCursor()
                    
                    model = extractWeightsModel(bands, std, marker)
                    self.Parent.dataStore.weights = computeWeights(bands, model)
                    self.Parent.dataStore.weightModel = model
                    self.Parent.dataStore.marker = marker
                    self.Parent.dataStore.standard = stdWidget.GetStringSelection()
                    
#                    print 'Model:', model
#                    print 'Marker:', marker
#                    print 'Markers:', self.Parent.dataStore.markerLanes
#                    print 'Standard:', stdWidget.GetStringSelection()
#                    print 'Weights:', self.Parent.dataStore.weights
                    
                    wx.EndBusyCursor()
                else:
                    self.Parent.imagePanel.ShowWarning(
                         'Standard is can not be applied to marker (dim diff)!')
            dlg.Destroy()
        else:
            self.Parent.imagePanel.ShowWarning('Select marker lane(s)!')
    
    def OnViewBandWeights(self, event):
#        print 'here view band weights'
        if not self.Parent.imagePanel.ShowNoWeightsWarning():
            dlg = ViewWeightsDialog(self.Parent, wx.ID_ANY,
                                    self.Parent.dataStore.weights)
            dlg.ShowModal()
            dlg.Destroy()
    
    def OnExportBandWeights(self, event):
#        print 'here export band weights'
        
        if not self.Parent.imagePanel.ShowNoWeightsWarning():
            # fetch the required filename and file type
            defaultFile = 'weights.txt'
            filters = 'Text files (*.txt)|*.txt'
            dlg = wx.FileDialog(self.Parent, "Save to file", "", defaultFile,
                                filters, style=wx.SAVE|wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
#                print 'Weights:', self.Parent.dataStore.weights
                with open(dlg.GetPath(), 'w') as f:
                    for line in self.Parent.dataStore.weights:
                        print>>f, str(line)[1:-1]
            dlg.Destroy()

#-------------------------------------------------------------------------------
    def OnMatchBands(self, event):
        wx.BeginBusyCursor()
        
        bands = deepcopy(self.Parent.dataStore.bands)
        
        for k in sorted(self.Parent.dataStore.markerLanes, reverse=True):
            del bands[k]
        
        self.Parent.dataStore.generateLaneLabels()
        
        distance = self.steps[4]['distance'].GetValue()
        self.Parent.dataStore.distance = distance
#        print
#        print 'Percent:', distance, self.Parent.imagePanel.image.size
#        print 'Distance:', int(distance*self.Parent.imagePanel.image.size[1]/100)
#        print
        distance = int(distance*self.Parent.imagePanel.image.size[1]/100)
        
        self.Parent.dataStore.clusters = bandMatching(bands, distance)
        self.Parent.dataStore.bandMatchings  = bands
        
        self.Parent.dataStore.modified = True
        
#        print self.Parent.dataStore.bands
#        print bands
#        print self.Parent.dataStore.bandMatchings
#        print self.Parent.dataStore.clusters
        
        self.Parent.imagePanel.SetBandClusters(self.Parent.dataStore.clusters)
        
        wx.EndBusyCursor()
    
    def OnEditBandMatch(self, event):
#        print 'Edit bands match'
        if not self.Parent.imagePanel.ShowNoMatchingWarning():
            bands = self.Parent.dataStore.bandMatchings
            noClusters = len(self.Parent.dataStore.clusters)
            matrix = computeMatchMatrix(bands, noClusters)
#            print 'match matrix:'
#            print matrix
        
#            matrix = array([[1, 0, 0, 1, 1, 1],
#                            [0, 1, 1, 0, 1, 0],
#                            [1, 1, 0, 1, 0, 1],
#                            [1, 0, 1, 1, 1, 0],
#                            [1, 1, 1, 0, 0, 1]])
            
            dlg = EditMatchMatrixDialog(self, wx.ID_ANY, matrix,
                                        self.Parent.dataStore.laneLabels)
            if dlg.ShowModal() == wx.ID_OK:
#                print 'Ok pressed!'
                self.Parent.dataStore.clusters = \
                               dlg.UpdateBands(self.Parent.dataStore.bandMatchings)
                self.Parent.imagePanel.SetBandClusters(self.Parent.dataStore.clusters)
                self.Parent.dataStore.modified = True
            dlg.Destroy()
    
    def OnExportBandMatch(self, event):
        if not self.Parent.imagePanel.ShowNoMatchingWarning():
            wx.BeginBusyCursor()
            bands = self.Parent.dataStore.bandMatchings
            noClusters = len(self.Parent.dataStore.clusters)
            matrix = computeMatchMatrix(bands, noClusters)
#            print 'match matrix:'
#            print matrix
            wx.EndBusyCursor()
            
            # fetch the required filename and file type
            # TODO: move somewhere else
            defaultFile = 'matrix.txt'
            filters = \
                'Zero one text files (*.txt)|*.txt' + '|'+ \
                'Zero one (transposed) text files (*.txt)|*.txt' + '|'+ \
                'Plus minus text files (*.txt)|*.txt' + '|' + \
                'Plus minus (transposed) text files (*.txt)|*.txt' + '|' + \
                'Similarity matrix text files (*.txt)|*.txt' + '|' + \
                'Distance matrix text files (*.txt)|*.txt'
            dlg = wx.FileDialog(self.Parent, "Save to file", "", defaultFile,
                                filters, style=wx.SAVE|wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                wx.BeginBusyCursor()
                if dlg.GetFilterIndex() == 0:
                    savetxt(dlg.GetPath(), matrix, '%d')
                elif dlg.GetFilterIndex() == 1:
                    savetxt(dlg.GetPath(), transpose(matrix), '%d')
                elif dlg.GetFilterIndex() == 2:
                    matrixStr = array(matrix, dtype='a1')
                    matrixStr = replace(matrixStr, '1', '+')
                    matrixStr = replace(matrixStr, '0', '-')
                    savetxt(dlg.GetPath(), matrixStr, '%c', ' ')
                elif dlg.GetFilterIndex() == 3:
                    matrixStr = array(transpose(matrix), dtype='a1')
                    matrixStr = replace(matrixStr, '1', '+')
                    matrixStr = replace(matrixStr, '0', '-')
                    savetxt(dlg.GetPath(), matrixStr, '%c', ' ')
                elif dlg.GetFilterIndex() == 4:
                    simMatrix = similarityMatrix(matrix)
                    savetxt(dlg.GetPath(), simMatrix, '%.2f')
                elif dlg.GetFilterIndex() == 5:
                    distMatrix = distanceMatrix(similarityMatrix(matrix))
                    savetxt(dlg.GetPath(), distMatrix, '%.2f')
                wx.EndBusyCursor()
            dlg.Destroy()
    
#-------------------------------------------------------------------------------
    def OnViewPhylTree(self, event):
        wx.BeginBusyCursor()
        
        bands = self.Parent.dataStore.bandMatchings
        noClusters = len(self.Parent.dataStore.clusters)
        matrix = computeMatchMatrix(bands, noClusters)
#        print 'match matrix:'
#        print matrix
    
        simMatrix = similarityMatrix(matrix)
#        print 'similarity matrix:'
#        print simMatrix
        distMatrix = distanceMatrix(simMatrix)
#        print 'distance matrix:'
#        print distMatrix
#        print 'method:', self.steps[5]['method'].GetStringSelection()
        method = self.steps[5]['methods'][self.steps[5]['method'].GetStringSelection()]
        tree, dist = computePhylogeneticTree(distMatrix, method)
#        print 'tree:', tree
#        print 'dist:', dist

        self.Parent.dataStore.tree = tree
        self.Parent.dataStore.dist = dist
        self.Parent.imagePanel.SetTree(tree, dist)
        
        wx.EndBusyCursor()
    
    def OnCheckTreeDistanceLabels(self, event):
        self.Parent.dataStore.showTreeDistanceLabels = \
                                      self.steps[5]['distanceLabels'].GetValue()
        if self.Parent.dataStore.hasTree():
            wx.BeginBusyCursor()
            self.Parent.imagePanel.SetTree(self.Parent.dataStore.tree,
                                           self.Parent.dataStore.dist)
            wx.EndBusyCursor()
    
    def OnEditTreeLaneLabels(self, event):
#        print 'edit lane names'
        dlg = EditLaneNamesDialog(self, wx.ID_ANY,
           self.Parent.dataStore.laneLabels, self.Parent.dataStore.laneNames[:])
        if dlg.ShowModal() == wx.ID_OK:
            self.Parent.dataStore.laneNames = dlg.GetLaneNames()
            self.Parent.dataStore.modified = True
        dlg.Destroy()
    
#    def OnExportPhylTree(self, event):#TODO: future version
#        print 'here export phyl tree'