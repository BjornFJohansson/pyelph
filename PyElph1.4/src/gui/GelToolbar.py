'''
    PyElph - Matplotlib custom toolbar
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

#Python native
import os

#wxPython
import wx

#matplotlib
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg

#Gel Analysis
from analysis.Lane import getRawLaneLevels
from gui.resources import getResourcesDirectory

resources = getResourcesDirectory() 

class RotateDialog(wx.Dialog):
    
    def __init__(self, parent, id, size=(260, 240), **kwargs):
        wx.Dialog.__init__(self, parent, id, size=size, title='Rotation',
                           **kwargs)
        self.Centre()
        
        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(os.path.join(
                        resources, 'rotate.png'))))
        
        self.options = [None]*4
        
        panel = wx.Panel(self, wx.ID_ANY)
        vbox = wx.BoxSizer(wx.VERTICAL)

        wx.StaticBox(panel, wx.ID_ANY, 'Rotation', (5, 5), (240, 160))
        self.options[0] = wx.RadioButton(panel, wx.ID_ANY, '90 degrees',
                                         (15, 30), style=wx.RB_GROUP)
        self.options[1] = wx.RadioButton(panel, wx.ID_ANY, '180 degrees',
                                         (15, 55))
        self.options[2] = wx.RadioButton(panel, wx.ID_ANY, '270 degrees',
                                         (15, 80))
        self.options[3] = wx.RadioButton(panel, wx.ID_ANY, 'Other',
                                         (15, 130))
        self.angle = wx.Slider(panel, wx.ID_ANY, 180, 1, 359, pos=(95, 105), 
                               size=(120, -1),
                               style=wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.angle.SetTickFreq(45, 0) 
        self.Bind(wx.EVT_SCROLL, self.OnScroll, self.angle)

        hbox = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(vbox)
    
    def OnScroll(self, event):
        self.options[3].SetValue(True)
    
    def getAngle(self):
        result = 1 + map(lambda x: x.GetValue(), self.options).index(True)
        if 0<result<4:
            return result*90
        return self.angle.GetValue()


class GelToolbar(NavigationToolbar2WxAgg):

    def __init__(self, plotCanvas):
        # create the default toolbar
        NavigationToolbar2WxAgg.__init__(self, plotCanvas)
        self.set_status_bar(self.Parent.Parent.statusBar)
        
        self.Tools = {}
        
        # remove the unwanted buttons
        self.ClearTools()
        
        # add new toolbar buttons
        self.SetToolBitmapSize((32,32))
        
        self._NTB2_HOME      = wx.NewId()
        self._NTB2_BACK      = wx.NewId()
        self._NTB2_FORWARD   = wx.NewId()
        self._NTB2_PAN       = wx.NewId()
        self._NTB2_ZOOM      = wx.NewId()
        self._NTB2_SAVE      = wx.NewId()
        
        self.ON_OPEN_IMAGE   = wx.NewId()
#        self.ON_SAVE_IMAGE   = wx.NewId()
        self.ON_CROP_IMAGE   = wx.NewId()
        self.ON_ROTATE_IMAGE = wx.NewId()
        
        self.ON_ADD_LANE     = wx.NewId()
        self.ON_REMOVE_LANE  = wx.NewId()
        self.ON_DEFINE_LANE  = wx.NewId()
        
        self.ON_ADD_BAND     = wx.NewId()
        self.ON_REMOVE_BAND  = wx.NewId()
        
        
        self.AddToolOption('open', self.ON_OPEN_IMAGE, 'open.png', self.open,
                           'Open', 'Open image ...')
        self.AddToolOption('save', self._NTB2_SAVE, 'save.png', self.save,
                           'Save', 'Save plot contents to file')
        self.AddSeparator()
        self.AddSeparator()
        self.AddToolOption('home', self._NTB2_HOME, 'home.png', self.home,
                           'Home', 'Reset original view')
        self.AddToolOption('back', self._NTB2_BACK, 'backward.png', self.back,
                           'Back', 'Back navigation view')
        self.AddToolOption('forward', self._NTB2_FORWARD, 'forward.png',
                           self.forward, 'Forward', 'Forward navigation view')
        self.AddToolOption('pan', self._NTB2_PAN, 'move.png', self.pan,
                           'Pan', 'Pan with left, zoom with right', True)
        self.AddToolOption('zoom', self._NTB2_ZOOM, 'zoom.png', self.zoom,
                           'Zoom', 'Zoom to rectangle', True)
        self.AddSeparator()
        self.AddSeparator()
        self.AddToolOption('crop', self.ON_CROP_IMAGE, 'crop.png', self.crop,
                           'Crop', 'Crop image', True)
        self.AddToolOption('rotate', self.ON_ROTATE_IMAGE, 'rotate.png',
                           self.rotate, 'Rotate Image', 'Rotate Image')
        self.AddToolOption('addLane', self.ON_ADD_LANE, 'add.png', self.addLane,
                           'Add lane', 'Add lane', True)
        self.AddToolOption('removeLane', self.ON_REMOVE_LANE, 'remove.png',
                           self.removeLane, 'Remove lane', 'Remove lane', True)
        self.AddToolOption('defineLaneWidth', self.ON_DEFINE_LANE, 'define.png',
                           self.defineLaneWidth, 'Define lane width',
                           'Define lane width', True)
        self.AddToolOption('addBand', self.ON_ADD_BAND, 'add.png', self.addBand,
                           'Add band', 'Add band', True)
        self.AddToolOption('removeBand', self.ON_REMOVE_BAND, 'remove.png',
                           self.removeBand, 'Remove band', 'Remove band', True)
        
        self.idSelectLane = self.canvas.mpl_connect('button_press_event',
                                                    self.selectLane)
    
    def AddToolOption(self, name, idT, icon, handler, sHelp, lHelp, checked=False):
        if checked:
            self.AddCheckTool(idT, wx.Bitmap(os.path.join(resources, icon)),
                          shortHelp=sHelp, longHelp=lHelp)
        else:
            self.AddSimpleTool(idT, wx.Bitmap(os.path.join(resources, icon)),
                           sHelp, lHelp)
        self.Tools[name] = (idT, self.FindById(idT), self.GetToolPos(idT), checked)
        self.Bind(wx.EVT_TOOL, handler, id=idT)
    
    def ToggleTools(self, selected = None):
        map(lambda tool: self.ToggleTool(tool[0], tool[0] == selected),
            filter(lambda x: x[3], self.Tools.values()))
    
    def ShowTool(self, toolName, show=True):
        id, tool, pos = self.Tools[toolName][:3]
        if self.FindById(id) == None and show:
            pos = min(pos, self.GetToolsCount())
            self.InsertToolItem(pos, tool)
            self.Realize()
        elif self.FindById(id) != None and not show:
            self.RemoveTool(id)
    
    def ShowTools(self, tools, show=True):
        map(lambda tool: self.ShowTool(tool, show), tools)
    
    def deactivate(self):
        self.ToggleTools()
        self._active = None
        self.mode = ''
        if self._idPress is not None:
            self._idPress=self.canvas.mpl_disconnect(self._idPress)

        if self._idRelease is not None:
            self._idRelease=self.canvas.mpl_disconnect(self._idRelease)
        
        self.idSelectLane = self.canvas.mpl_connect('button_press_event',
                                                    self.selectLane)
        
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

#-------------------------------------------------------------------------------
    def processOperation(self, idTool, active, mode, pressHandler, releaseHandler):
        if self._active == active:
            self.idSelectLane = self.canvas.mpl_connect('button_press_event',
                                                        self.selectLane)
            self._active = None
        else:
            self.Parent.DeselectLane()
            self.canvas.mpl_disconnect(self.idSelectLane)
            self.ToggleTools(idTool)
            self._active = active
        
        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)
            self.mode = ''
        
        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
            self.mode = ''
        
        if  self._active:
            if pressHandler:
                self._idPress = self.canvas.mpl_connect('button_press_event',
                                                        pressHandler)
            if releaseHandler:
                self._idRelease = self.canvas.mpl_connect('button_release_event',
                                                          releaseHandler)
            self.mode = mode
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

#-------------------------------------------------------------------------------

    def getCoordinates(self, event, ignoreX=False, ignoreY=False):
        #the release mouse button callback
        if not self._xypress: return None

        for zoom_id in self._ids_zoom:
            self.canvas.mpl_disconnect(zoom_id)

        assert len(self._xypress) == 1

        x, y = event.x, event.y
        lastx, lasty, a = self._xypress[0][:3]
        
        # ignore singular clicks - 5 pixels is a threshold
        if (abs(x-lastx)<5 and not ignoreX) or (abs(y-lasty)<5 and not ignoreY):
            self._xypress = None
            self.release(event)
            self.draw()
            return False

        # transform points to data reference frame
        inverse = a.transData.inverted()
        lastx, lasty = inverse.transform_point( (lastx, lasty) )
        x, y = inverse.transform_point( (x, y) )
        
        lastx, lasty, x, y = map(lambda x: int(round(x)), (lastx, lasty, x, y))
        
        # get max values
        Xmin,Xmax = a.get_xlim()
        Ymin,Ymax = a.get_ylim()
        assert Xmin <= Xmax and Ymin <= Ymax
        Xmin = max(0, Xmin)
        Xmax = min(self.Parent.image.size[0], Xmax)
        Ymin = max(0, Ymin)
        Ymax = min(self.Parent.image.size[1], Ymax)
        
        assert Xmin <= Xmax and Ymin <= Ymax
        
#        print 'lims', Xmin, Xmax, Ymin, Ymax
        
        x0 = max(Xmin, min(x, lastx))
        x1 = max(1+x0, min(Xmax, max(x, lastx)))
        y0 = max(Ymin, min(y, lasty))
        y1 = max(1+y0, min(Ymax, max(y, lasty)))
        
        assert x0 < x1 and y0 < y1
        
        return (x0, x1, y0, y1)
        
    def finishRelease(self, event, saveView=False):
        self._xypress = None
        self._button_pressed = None

        self._zoom_mode = None
        if saveView:
            self.push_current()
        self.release(event)

#-------------------------------------------------------------------------------

    def open(self, event):
        self.deactivate()
        
        #TODO: improve this function; load data from .data file
        filters = 'Image files (*.gif;*.png;*.jpg;*tiff;*tif;*.bmp)|*.gif;*.png;*.jpg;*.tiff;*tif;*.bmp'
        dlg = wx.FileDialog(self, message="Open an Image...",
                            defaultDir=os.getcwd(), defaultFile="",
                            wildcard=filters, style=wx.OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            
            filename = dlg.GetPath()
            self.Parent.Parent.SetTitle(filename)
            
            wx.BeginBusyCursor()
            
            # load the image from file and display it inside the panel
            size = self.Parent.ShowImage(filename)
            
            # set the StatusBar to show the image's size
            self.Parent.Parent.statusBar.SetStatusText(
                                                'Size = %s' % (str(size)), 0)
            
            # save in data store
            self.Parent.Parent.dataStore.reset()
            self.Parent.Parent.dataStore.imageName = filename
            self.Parent.Parent.dataStore.computeDigest(filename)
#            self.Parent.Parent.dataStore.loadData() #TODO: use in future version
                        
            wx.EndBusyCursor()
   
        dlg.Destroy()

#-------------------------------------------------------------------------------

    def zoom(self, *args):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        if self._active == 'ZOOM':
            self.idSelectLane = self.canvas.mpl_connect('button_press_event',
                                                        self.selectLane)
        else:
            self.canvas.mpl_disconnect(self.idSelectLane)
            self.ToggleTools(self._NTB2_ZOOM)
        NavigationToolbar2WxAgg.zoom(self, *args)

    def pan(self, *args):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        if self._active == 'PAN':
            self.idSelectLane = self.canvas.mpl_connect('button_press_event',
                                                        self.selectLane)
        else:
            self.canvas.mpl_disconnect(self.idSelectLane)
            self.ToggleTools(self._NTB2_PAN)
        NavigationToolbar2WxAgg.pan(self, *args)

#-------------------------------------------------------------------------------

    def release_crop(self, event):
        coords = self.getCoordinates(event)
        if not coords:
            return
        x0, x1, y0, y1 = coords
        
        if self._button_pressed == 1:
            self.Parent.CropImage(x0, y0, x1, y1)
        else:
            self.draw()
        
        self.finishRelease(event, True)

    def crop(self, *args):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        self.processOperation(self.ON_CROP_IMAGE, 'CROP', 'crop',
                              self.press_zoom, self.release_crop)

#-------------------------------------------------------------------------------
    
    def rotate(self, event):
        if self.Parent.ShowNoImageWarning():
            return
        self.deactivate()
        
        dialog = RotateDialog(self, wx.ID_ANY)
        if dialog.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()
            self.Parent.RotateImage(dialog.getAngle())
            wx.EndBusyCursor()
        
        dialog.Destroy()

#-------------------------------------------------------------------------------

    def selectLane(self, event):
        if self.Parent.Parent.dataStore.hasLanes():
            a = self.canvas.figure.get_axes()[0]
            inverse = a.transData.inverted()
            x = inverse.transform_point((event.x, event.y))[0]
            
            self.Parent.SelectLane(x, getRawLaneLevels)

#-------------------------------------------------------------------------------

    def press_add_lane(self, event):
#        print 'the press mouse button in add lane mode callback'
        if event.button == 1:
            self._button_pressed=1
        elif  event.button == 3:
            self._button_pressed=3
        else:
            self._button_pressed=None
            return

        x, y = event.x, event.y

        self._xypress=[]
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if x is not None and y is not None and a.in_axes(event) \
                    and a.get_navigate() and a.can_zoom():
                self._xypress.append(( x, y, a, i, a.viewLim.frozen(),
                                       a.transData.frozen()))

        id1 = self.canvas.mpl_connect('motion_notify_event', self.drag_add_lane)

        self._ids_zoom = (id1,)
        self.press(event)

    def drag_add_lane(self, event):
#        'the drag callback in zoom mode'

        if self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a = self._xypress[0][:3]

            # adjust x, last, y, last
            x1, y1, x2, y2 = a.bbox.extents
            x, lastx = max(min(x, lastx), x1), min(max(x, lastx), x2)
#            y, lasty = max(min(y, lasty), y1), min(max(y, lasty), y2)

            self.draw_rubberband(event, x, lasty, lastx, lasty + 8)
    
    def release_add_lane(self, event):
        coords = self.getCoordinates(event, ignoreY=True)
        if not coords:
            return
        x0, x1 = coords[:2]
        
        if self._button_pressed == 1:
#            print x0, x1, y0, y1
            self.Parent.AddLane((x0, x1))
            self.draw()
        else:
            self.draw()
        
        self.finishRelease(event)
    
    def addLane(self, event):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        if self._active != 'ADD_LANE' and \
                        self.Parent.Parent.dataStore.showBackgroundSubstraction:
            self.Parent.RestoreBackground()
            self.Parent.Parent.dataStore.showBackgroundSubstraction = False
            self.Parent.Parent.options.steps[1]['background'].SetValue(False)
        
        self.processOperation(self.ON_ADD_LANE, 'ADD_LANE', 'add lane',
                              self.press_add_lane, self.release_add_lane)

#-------------------------------------------------------------------------------

    def press_remove_lane(self, event):
        a = self.canvas.figure.get_axes()[0]
        inverse = a.transData.inverted()
        x = inverse.transform_point((event.x, event.y))[0]
        
        self.Parent.RemoveLane(x)
    
    def removeLane(self, event):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        if self._active != 'REMOVE_LANE' and self.Parent.ShowNoLanesWarning():
            self.deactivate()
            return
        
        if self._active != 'REMOVE_LANE' and \
                        self.Parent.Parent.dataStore.showBackgroundSubstraction:
            self.Parent.RestoreBackground()
            self.Parent.Parent.dataStore.showBackgroundSubstraction = False
            self.Parent.Parent.options.steps[1]['background'].SetValue(False)
        
        self.processOperation(self.ON_REMOVE_LANE, 'REMOVE_LANE', 'remove lane',
                              self.press_remove_lane, None)

#-------------------------------------------------------------------------------

    def release_define_lane_width(self, event):
#        print 'the release mouse button callback in define lane width mode'
        coords = self.getCoordinates(event, ignoreY=True)
        if not coords:
            return
        x0, x1 = coords[:2]
        
        if self._button_pressed == 1:
#            print x0, x1, y0, y1
            self.Parent.Parent.dataStore.laneWidth = x1 - x0
            self.Parent.Parent.options.steps[1]['laneWidth'].SetChoice(x1-x0, 'manual')
            self.Parent.Parent.options.steps[1]['maxDev'].SetValue(10)
            self.draw()
        else:
            self.draw()
        
        self.finishRelease(event)
    
    def defineLaneWidth(self, event):
#        print 'define lane width'
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        self.processOperation(self.ON_DEFINE_LANE, 'DEFINE_LANE_WIDTH',
                              'define lane width', self.press_add_lane,
                              self.release_define_lane_width)

#-------------------------------------------------------------------------------

    def press_add_band(self, event):
        a = self.canvas.figure.get_axes()[0]
        inverse = a.transData.inverted()
        x, y = inverse.transform_point((event.x, event.y))
        
        self.Parent.AddBand(x, y)
    
    def addBand(self, event):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        if self.Parent.ShowNoLanesWarning():
            self.deactivate()
            return
        
        self.processOperation(self.ON_ADD_BAND, 'ADD_BAND', 'add band',
                              self.press_add_band, None)

#-------------------------------------------------------------------------------

    def release_remove_band(self, event):
        coords = self.getCoordinates(event)
        if not coords:
            return
        x0, x1, y0, y1 = coords
        
        if self._button_pressed == 1:
            self.Parent.RemoveBands(x0, y0, x1, y1)
            self.draw()
        else:
            self.draw()
        
        self.finishRelease(event)

    def removeBand(self, *args):
        if self.Parent.ShowNoImageWarning():
            self.deactivate()
            return
        
        if self.Parent.ShowNoLanesWarning():
            self.deactivate()
            return
        
        if self._active != 'REMOVE_BAND' and self.Parent.ShowNoBandsWarning():
            self.deactivate()
            return
        self.processOperation(self.ON_REMOVE_BAND, 'REMOVE_BAND', 'remove band',
                              self.press_zoom, self.release_remove_band)

#-------------------------------------------------------------------------------

    def reset(self):
        self.update()
        self.push_current()