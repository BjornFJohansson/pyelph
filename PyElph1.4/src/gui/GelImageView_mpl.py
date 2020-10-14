'''
    PyElph - Matplotlib image view panel
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

#wxPython
import wx

#PIL
import Image

#numpy
from numpy import array, argwhere

#matplotlib
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.cm as cm

#Gel Analysis
from GelToolbar import GelToolbar


class GelDataWindow(wx.Panel):
    
    def __init__(self, parent, id, maxRes=(600, 400)):
        wx.Panel.__init__(self, parent, id)
        
        self.maxRes = maxRes
        self.originalImage = None #save original image for undo and stuff
        self.image = None
        self.imageWithBackg = None #used to restore background
        self.data = None # data from transformed image, but with background
        
        self.SetBackgroundColour(wx.WHITE)
        self.SetForegroundColour(wx.WHITE)

        self.figure = Figure()
        self.figure.set_frameon(True)
        
        self.laneColors = ('b', 'g', 'b')
        self.laneSelectColors = ('r', 'w', 'r')

        # l, b, w, h
        self.bounds = [0.075, 0.05, 0.85, 0.95]
        # h, v
        self.cut = [0.8, 0.2]

        #-----------------------------------------------------------------------
        rect = [self.bounds[0],
                self.bounds[1] + self.cut[1] * self.bounds[3],
                self.cut[0] * self.bounds[2] - 0.025,
                (1-self.cut[1]) * self.bounds[3] - 0.025]
        self.imagePort = self.figure.add_axes(rect, frameon=True, axisbg='w')
        
        self.imagePort.tick_params('both', which='both', labelleft=False, 
                                   labelbottom=False)
        #-----------------------------------------------------------------------
        rect = [self.bounds[0],
                self.bounds[1],
                self.cut[0] * self.bounds[2] - 0.025,
                self.cut[1] * self.bounds[3] - 0.025]
        self.laneSpectrum = self.figure.add_axes(rect, \
                                              frameon=True, axisbg='w',\
                                              sharex=self.imagePort)
        
        self.laneSpectrum.tick_params('y', which='minor', labelleft=False)
        self.laneSpectrum.set_yticks([0, 128, 255])
        self.laneSpectrum.set_ylim(0, 255)
        
        #-----------------------------------------------------------------------
        rect = [self.bounds[0] + self.cut[0] * self.bounds[2],
                self.bounds[1] + self.cut[1] * self.bounds[3],
                (1-self.cut[0]) * self.bounds[2] - 0.025,
                (1-self.cut[1]) * self.bounds[3] - 0.025]
        self.laneLevels = self.figure.add_axes(rect, frameon=True, axisbg='w', \
                                              sharey=self.imagePort)
        
        self.laneLevels.tick_params('x', which='minor', labelleft=False)
        self.laneLevels.tick_params('y', which='major', labelleft=False, 
                                      labelright=True)
        self.laneLevels.tick_params('x', which='major', labelleft=False)
        self.laneLevels.set_xticks([0, 128, 255])
        self.laneLevels.set_xlim(0, 255)
        self.laneLevels.set_xticklabels([0, 128, 255], rotation='vertical')
        
        #-----------------------------------------------------------------------
        
        
        self.canvas = FigureCanvas(self, wx.ID_ANY, self.figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        self.addToolbar()  # comment this out for no toolbar
        
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        if self.Parent.options.step == 5: #TODO: bug with limits on resize 
            if self.Parent.dataStore.hasTree(): 
                self.imagePort.set_xlim(self.Parent.dataStore.treeViewLims[0])
                self.imagePort.set_xlim(self.Parent.dataStore.treeViewLims[1])
        else:
            if self.image != None:
                self.imagePort.set_xlim([0, self.image.size[0]])
                self.imagePort.set_ylim([0, self.image.size[1]])
        event.Skip()

    def addToolbar(self):
        self.toolbar = GelToolbar(self.canvas)
        self.toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        
        self.toolbar.ShowTool('addLane', False) #TODO:
        self.toolbar.ShowTool('removeLane', False)
        self.toolbar.ShowTool('defineLaneWidth', False)
        self.toolbar.ShowTool('addBand', False)
        self.toolbar.ShowTool('removeBand', False)
        
        # update the axes menu on the toolbar
        self.toolbar.update()

    def OnPaint(self, event):
        self.canvas.draw()

#-------------------------------------------------------------------------------

    def ShowImage(self, filename):
        if filename != None:
            # open file
            self.image = Image.open(filename).convert('L')
            self.originalImage = self.image.copy()
            self.SetImage()
            return self.image.size
            
    def SetImage(self):
        # create thumbnail image to draw
        resizeImg = self.image.copy()
        resizeImg.thumbnail(self.maxRes)
        
        # extract data to draw
        data = array(resizeImg.getdata()).reshape(
                                (resizeImg.size[1], resizeImg.size[0]))
#            print data.shape
        
        # draw image
        self.imagePort.clear()
        self.laneSpectrum.clear()
        self.laneLevels.clear()
        size = self.image.size
        self.imagePort.imshow(data, cmap=cm.gray,\
                              interpolation='nearest', origin='upper',\
                              extent=(0, size[0], 0, size[1]))
        self.canvas.draw()
        
        # reset toolbar
        self.toolbar.reset()
    
    def RestoreImage(self):
        self.image = self.originalImage.copy()
        self.SetImage()
        self.SetLaneLines([])
        self.SetLaneSpectrum()
        self.Parent.dataStore.transform = []
        self.Parent.dataStore.modified = True
    
    def SaveImageWithBackground(self):
        self.imageWithBackg = self.image.copy()
        self.Parent.dataStore.data = array(self.image.getdata()) \
                     .reshape((self.image.size[1], self.image.size[0]))
    
    def RestoreBackground(self, all=True):
        self.image = self.imageWithBackg.copy()
        self.Parent.dataStore.showBackgroundSubstraction = False
        self.SetImage()
        if all:
            self.SetLaneLines(self.Parent.dataStore.lanes)
            self.SetLaneSpectrum()
    
    def RemoveBackground(self, removeBack):
        if self.Parent.dataStore.modified:
            data = self.Parent.dataStore.data
            back = removeBack(data, self.Parent.dataStore.lanes)
            self.Parent.dataStore.back = back
        
        self.image = Image.fromarray(self.Parent.dataStore.back)
        self.Parent.dataStore.showBackgroundSubstraction = True
        
        self.SetImage()
        self.SetLaneLines(self.Parent.dataStore.lanes)
        self.SetLaneSpectrum()
    
    def CropImage(self, x0, y0, x1, y1):
        y1, y0 = map(lambda val: self.image.size[1] - val, (y0, y1))
        self.image = self.image.crop((x0, y0, x1, y1)).copy()
        self.SetImage()
        self.Parent.dataStore.transform.append(('crop', (x0, y0, x1, y1)))
        self.Parent.dataStore.modified = True
    
    def RotateImage(self, angle):
        if angle%90 == 0:
            rot = (Image.ROTATE_90, Image.ROTATE_180,
                   Image.ROTATE_270)[angle/90-1]
            self.image = self.image.transpose(rot)
        else:
            self.image = self.image.rotate(angle, expand=True)
        self.SetImage()
        self.Parent.dataStore.transform.append(('rotate', angle))
        self.Parent.dataStore.modified = True

#-------------------------------------------------------------------------------
    # Lane Methods
    def SelectLane(self, x, getLevels):
#        print 'select lane lines'
        if self.Parent.dataStore.selectedLane >=0:
            idx = self.Parent.dataStore.selectedLane
            lines = self.Parent.dataStore.laneLines[idx]
            map(lambda line, c: line.set_color(c), lines, self.laneColors)
        
        idx = ''.join(map(lambda lane: str(int(lane[0] <= x <= lane[1])),
                          self.Parent.dataStore.lanes)).find('1')
        if idx >= 0:
            lines = self.Parent.dataStore.laneLines[idx]
            map(lambda line, c: line.set_color(c), lines, self.laneSelectColors)
            
            levels = getLevels(self.Parent.dataStore.data,
                               self.Parent.dataStore.lanes[idx])
            self.SetLaneLevels(levels) #TODO: compatibility
            self.OnPaint(None)
        else:
            self.SetLaneLevels(None)
        self.Parent.dataStore.selectedLane = idx
    
    def DeselectLane(self):
#        print 'deselect lane lines'
        if self.Parent.dataStore.selectedLane >=0 \
           and self.Parent.dataStore.hasLanes():
            idx = self.Parent.dataStore.selectedLane
            lines = self.Parent.dataStore.laneLines[idx]
            map(lambda line, c: line.set_color(c), lines, self.laneColors)
            self.SetLaneLevels(None)
            self.Parent.dataStore.selectedLane = -1
    
    def AddLane(self, newLane):
        lanes = self.Parent.dataStore.lanes
        if lanes == None:
            self.Parent.dataStore.lanes = lanes = []
        
#        print newLane, lanes
        if len(lanes) == 0:
            idx = 0
        elif len(lanes) == 1:
            idx = -1
            if lanes[0][1] < newLane[0]:
                idx = 1
            elif newLane[1] < lanes[0][0]:
                idx = 0
        else:
#            print lanes[:-1]
#            print lanes[1:]
#            print ''.join(map(lambda lane, nextLane:
#                  str(int(lane[1] <= newLane[0] and newLane[1] <= nextLane[0])),
#                  lanes[:-1], lanes[1:]))
            idx = ''.join(map(lambda lane, nextLane:
                  str(int(lane[1] <= newLane[0] and newLane[1] <= nextLane[0])),
                  lanes[:-1], lanes[1:])).find('1')
#            print idx
            if idx == -1:
                if lanes[-1][1] < newLane[0]:
                    idx = len(lanes)
                elif newLane[1] < lanes[0][0]:
                    idx = 0
            else:
                idx += 1
#            print idx
        
        if idx >= 0:
#            print lanes
            lanes.insert(idx, newLane)
            idxBegin, idxEnd = newLane
            idxMiddle = (idxBegin + idxEnd)/2
            
            self.Parent.dataStore.laneLines.insert(idx,
                   tuple(map(lambda x, c: self.imagePort.add_line(Line2D([x, x],
                              [0, self.image.size[1]], color=c, linewidth=1.2)),
                          (idxBegin, idxMiddle, idxEnd), self.laneColors) )
                )
            
            texts = self.Parent.dataStore.treeTexts
            texts.insert(idx,
                         self.imagePort.text(idxMiddle+1, self.image.size[1]-1,
                                    '%d' % (idx+1), color='w',
                                    ha='left', va='top'))

            for k in range(idx+1, len(texts)):
                texts[k].set_text('%d' % (k+1))
#            print lanes
            self.Parent.dataStore.modified = True
        else:
            self.ShowInvalidLaneWarning()
    
    def RemoveLane(self, x):
        idx = ''.join(map(lambda lane: str(int(lane[0] <= x <= lane[1])),
                          self.Parent.dataStore.lanes)).find('1')
        
        if idx >= 0:
#            print self.Parent.dataStore.lanes
            del self.Parent.dataStore.lanes[idx]
            laneLines = self.Parent.dataStore.laneLines[idx]
            map(lambda line: self.imagePort.lines.remove(line), laneLines)
            del self.Parent.dataStore.laneLines[idx]
#            print self.Parent.dataStore.lanes

            texts = self.Parent.dataStore.treeTexts
            self.imagePort.texts.remove(texts[idx])
            del texts[idx]
            for k in range(idx, len(texts)):
                texts[k].set_text('%d' % (k+1))

            self.OnPaint(None)
            self.Parent.dataStore.modified = True
    
    def SetLaneLines(self, lanes):
#        print 'set lane lines'
        self.Parent.dataStore.laneLines = []
        self.imagePort.lines = []
        self.Parent.dataStore.treeTexts = []
        self.imagePort.texts = []
        k=0
        for idxBegin, idxEnd in lanes:
            idxMiddle = (idxBegin + idxEnd)/2
            self.Parent.dataStore.laneLines.append(
                tuple(map(lambda x, c: self.imagePort.add_line(Line2D([x, x],
                              [0, self.image.size[1]], color=c, linewidth=1.2)),
                          (idxBegin, idxMiddle, idxEnd), self.laneColors) )
                )
            self.Parent.dataStore.treeTexts.append(
                self.imagePort.text(idxMiddle+1, self.image.size[1]-1,
                                    '%d' % (k+1), color='w',
                                    ha='left', va='top')
                )
            k += 1
        self.OnPaint(None)
    
    def SetLaneSpectrum(self, clear=False): # TODO: open button in toolbar
#        print 'set lane spectrum'
        
        self.laneSpectrum.clear()
        if self.Parent.dataStore.hasData() and not clear:
            laneData = self.Parent.dataStore.data.max(0)
            self.laneSpectrum.plot(laneData, 'k')
            self.laneSpectrum.set_xlim([0, laneData.size])
            self.laneSpectrum.set_ylim([0, 255])
        self.OnPaint(None)
    
    def SetLaneLevels(self, laneData): # TODO: open button in toolbar
#        print 'set lane spectrum'
        self.laneLevels.clear()
        if laneData != None:
            limy = self.laneLevels.get_ylim()
            self.laneLevels.plot(list(reversed(laneData)),
                                 range(laneData.size), 'k')
            self.laneLevels.set_xlim([0, 255])
            self.laneLevels.set_ylim(limy)
        self.OnPaint(None)

#-------------------------------------------------------------------------------
    # Band Methods
    def SetBands(self, bands):
        map(lambda line: self.imagePort.lines.remove(line),
            self.Parent.dataStore.bandLines)
        self.Parent.dataStore.bandLines = []
        xlim = self.imagePort.get_xlim()
        ylim = self.imagePort.get_xlim()
        for b in bands:
            if len(b) > 0:
                x, y = zip(*b)
                y = map(lambda val: self.image.size[1] - val, y)
                self.Parent.dataStore.bandLines.append(
                 *self.imagePort.plot(x, y, 'bx', mew=1.5) #, markersize=8)
                )
        self.imagePort.set_xlim(xlim)
        self.imagePort.set_xlim(ylim)
        self.OnPaint(None)
    
    def AddBand(self, x, y):
        if self.Parent.dataStore.bands == None:
            self.Parent.dataStore.bands = \
                                    [[] for lane in self.Parent.dataStore.lanes]
#        print x, y, self.image.size
        y = int(self.image.size[1] - y)
#        print x, y, self.image.size
        idx = ''.join(map(lambda lane: str(int(lane[0] <= x <= lane[1])),
                          self.Parent.dataStore.lanes)).find('1')
        if idx >= 0:
            x = int(sum(self.Parent.dataStore.lanes[idx])/2)
#            print x
            b = self.Parent.dataStore.bands[idx]
            i = ''.join(map(lambda band: str(int(y <= band[1])), b)).find('1')
#            print i, ''.join(map(lambda band: str(int(y <= band[1])), b))
#            print b
            if i >= 0:
                if b[i][1] != y:
                    b.insert(i, [x, y])
            else:
                b.append([x, y])
#            print b
            self.SetBands(self.Parent.dataStore.bands)
            
            self.Parent.dataStore.modified = True
    
    def RemoveBands(self, x0, y0, x1, y1): # TODO:
        y1, y0 = map(lambda val: self.image.size[1] - val, (y0, y1))
        for b in self.Parent.dataStore.bands:
            k = 0;
            while k < len(b):
                if x0 <= b[k][0] <= x1 and y0 <= b[k][1] <= y1:
                    del b[k]
                    self.Parent.dataStore.modified = True
                else:
                    k += 1
        self.SetBands(self.Parent.dataStore.bands)

#-------------------------------------------------------------------------------
    def SetBandClusters(self, clusters):
        map(lambda line: self.imagePort.lines.remove(line),
            self.Parent.dataStore.bandMatchLines)
        self.Parent.dataStore.bandMatchLines = []
        xlim = self.imagePort.get_xlim()
        ylim = self.imagePort.get_xlim()
        for k, cl in enumerate(clusters):
            if len(cl) > 0:
#                print 'cluster:', cl
                x, y = zip(*cl)[:2]
                y = map(lambda val: self.image.size[1] - val, y)
                if k % 2:
                    self.Parent.dataStore.bandMatchLines.append(
                                              *self.imagePort.plot(x, y, 'y-o'))
                else:
                    self.Parent.dataStore.bandMatchLines.append(
                                              *self.imagePort.plot(x, y, 'r-o'))
        self.imagePort.set_xlim(xlim)
        self.imagePort.set_xlim(ylim)
        self.OnPaint(None)
    
#-------------------------------------------------------------------------------
    # Phylogenetic Tree
    
    def longestPath(self, tree, dist, current):
        new = argwhere(tree == current)
        if new.size == 0:
            return current, dist[current]
        else:
            nodeL, pathDistL = self.longestPath(tree, dist, new[0])
            nodeR, pathDistR = self.longestPath(tree, dist, new[1])
            if pathDistL < pathDistR:
                if current >= 0:
                    return nodeR, dist[current] + pathDistR
                else:
                    return nodeR, pathDistR
            else:
                if current >=0:
                    return nodeL, dist[current] + pathDistL
                else:
                    return nodeL, pathDistL
    
    def buildPathsForward(self, current, line, col, c, show = False):
        treeLines = self.Parent.dataStore.treeLines
        treeTexts = self.Parent.dataStore.treeTexts
        endCol = col
        new = argwhere(self.Parent.dataStore.tree == current)
        if current >= 0:
            endCol += self.Parent.dataStore.dist[current]
            if new.size == 0:
                treeLines.append(*self.imagePort.plot((col, endCol), [line]*2, 'k-'))
                if show:
                    treeTexts.append(self.imagePort.text((col + endCol)/2.0,
                         line+0.1, '%.1f' % self.Parent.dataStore.dist[current],
                         ha='center', va='bottom'))
        
        if new.size == 0:
            treeTexts.append(self.imagePort.text(endCol+0.1, line,
                                self.Parent.dataStore.laneNames[current],
                                ha='left', va='center'))
            return line + 2*c, line
        
        line1, use1 = self.buildPathsForward(new[0][0], line, endCol, c, show)
        line2, use2 = self.buildPathsForward(new[1][0], line1, endCol, c, show)

        if current >= 0:
            treeLines.append(*self.imagePort.plot((col, endCol), [(use1+use2)/2.0]*2, 'k-'))
            if show:
                treeTexts.append(self.imagePort.text((col + endCol)/2.0,
                    (use1+use2)/2.0+0.1, '%.1f' % self.Parent.dataStore.dist[current],
                    ha='center', va='bottom'))
        
        treeLines.append(*self.imagePort.plot([endCol]*2, (use1, use2), 'k-'))
        
        return line2, (use1+use2)/2.0

#TODO: old version, to delete     
#    def buildPathsForward_rev1(self, current, line, col, c, show = False):
#        treeLines = self.Parent.dataStore.treeLines
#        treeTexts = self.Parent.dataStore.treeTexts
#        endCol = col
#        new = argwhere(self.Parent.dataStore.tree == current)
#        if current >= 0:
##            print 'dist:', self.Parent.dataStore.dist[current], '->', self.Parent.dataStore.dist[current]*c
#            endCol += self.Parent.dataStore.dist[current]*c
#            if new.size == 0:
#                treeLines.append(*self.imagePort.plot((col, endCol), [line]*2, 'k-'))
#            else:
#                treeLines.append(*self.imagePort.plot((col, endCol), [line+1]*2, 'k-'))
#            if show:
#                treeTexts.append(self.imagePort.text((col + endCol)/2.0,
#                         line+0.1, '%.1f' % self.Parent.dataStore.dist[current],
#                         ha='center', va='bottom'))
#        
#        if new.size == 0:
#            treeTexts.append(self.imagePort.text(endCol+0.1, line,
#                                self.Parent.dataStore.laneLabels[current],
#                                ha='left', va='center'))
#            return line + 2, True
#        
#        newLine1, leaf1 = self.buildPathsForward_rev1(new[0][0], line, endCol, c, show)
#        newLine2, leaf2 = self.buildPathsForward_rev1(new[1][0], newLine1, endCol, c, show)
#        if not leaf1:
#            line += 1
#        if not leaf2:
#            newLine1 += 1
#        treeLines.append(*self.imagePort.plot([endCol]*2, (line, newLine1), 'k-'))
#        return newLine2, False
#
#TODO: old version, to delete    
#    def buildPathsForward_old(self, current, line, col, c, show = False):
#        treeLines = self.Parent.dataStore.treeLines
#        treeTexts = self.Parent.dataStore.treeTexts
#        endCol = col
#        if current >= 0:
##            print 'dist:', self.Parent.dataStore.dist[current], '->', self.Parent.dataStore.dist[current]*c
#            endCol += self.Parent.dataStore.dist[current]*c
#            treeLines.append(*self.imagePort.plot((col, endCol), [line]*2, 'k-'))
#            if show:
#                treeTexts.append(self.imagePort.text((col + endCol)/2.0,
#                         line+0.1, '%.1f' % self.Parent.dataStore.dist[current],
#                         ha='center', va='bottom'))
#        
#        new = argwhere(self.Parent.dataStore.tree == current)
#        if new.size == 0:
#            treeTexts.append(self.imagePort.text(endCol+0.1, line,
#                                self.Parent.dataStore.laneLabels[current],
#                                ha='left', va='center'))
#            return line + 2
#        
#        newLine = self.buildPathsForward_old(new[0][0], line, endCol, c, show)
#        
#        treeLines.append(*self.imagePort.plot([endCol]*2, (line, newLine), 'k-'))
#        
#        return self.buildPathsForward_old(new[1][0], newLine, endCol, c, show)
    
    def SetTree(self, tree, dist):
        map(lambda line: self.imagePort.lines.remove(line),
            self.Parent.dataStore.treeLines)
        self.Parent.dataStore.treeLines = []
        
        map(lambda text: self.imagePort.texts.remove(text),
            self.Parent.dataStore.treeTexts)
        self.Parent.dataStore.treeTexts = []
        
        self.imagePort.clear()
        self.laneSpectrum.clear()
        self.laneLevels.clear()
        
        length = self.longestPath(tree, dist, -1)[1][0]
        height = 2.0 * len(self.Parent.dataStore.lanes)
        
#        print length, height
#        print 'factor:', height/length
#        print tree
#        print dist
        self.buildPathsForward(-1, 0, 0, length/height, #height/length,
                               self.Parent.dataStore.showTreeDistanceLabels)
        
        self.imagePort.set_xlim((-2, length + 4)) #TODO: limits on resize
        self.imagePort.set_ylim((-2, length + 4))
        self.toolbar.reset()
        self.Parent.dataStore.treeViewLims = (-2, length + 4), (-2, length + 4)
        
        self.OnPaint(None)
#-------------------------------------------------------------------------------
    def ShowError(self, msg):
        msgDialog = wx.MessageDialog(self.Parent, msg, 'Error',
                                     style=wx.OK | wx.ICON_WARNING)
        msgDialog.ShowModal()
        msgDialog.Destroy()
    
    def ShowWarning(self, msg):
        msgDialog = wx.MessageDialog(self.Parent, msg, 'Warning',
                                     style=wx.OK | wx.ICON_WARNING)
        msgDialog.ShowModal()
        msgDialog.Destroy()
    
    def ShowNoImageWarning(self):
        if self.image == None:
            self.ShowWarning('Please load an image first!')
            return True
        return False
    
    def ShowNoLanesWarning(self):
        if not self.Parent.dataStore.hasLanes():
            self.ShowWarning('Need lanes for this option!') # TODO:
            return True
        return False
    
    def ShowInvalidLaneWarning(self):
        self.ShowWarning('Invalid lane - overlapping!') # TODO:
    
    def ShowNoBandsWarning(self):
        if not self.Parent.dataStore.hasBands():
            self.ShowWarning('Need bands for this option!') # TODO:
            return True
        return False
    
    def ShowEmptyLanesWarning(self):
        list = zip(*filter(lambda x: len(x[1])==0,
                      enumerate(self.Parent.dataStore.bands)))
        if len(list) > 0:
            list = map(lambda x: x+1, list[0])
            self.ShowWarning('Lanes ' + str(list) + ' are empty!') # TODO:
            return True
        return False
    
    def ShowNoWeightsWarning(self):
        if not self.Parent.dataStore.hasWeights():
            self.ShowWarning('Need weights for this option!') # TODO:
            return True
        return False
    
    def ShowNoMatchingWarning(self):
        if not self.Parent.dataStore.hasMatching():
            self.ShowWarning("Need bands' match for this operation!") #TODO:
            return True
        return False