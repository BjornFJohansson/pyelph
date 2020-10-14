'''
    PyElph - GUI main frame and wxPython application
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


import wx

from gui.GelImageView_mpl import GelDataWindow
from gui.OptionPanel import OptionWindow
from gui.DataStore import DataStore


class GelAnalysis(wx.Frame):
    
    def __init__(self, parent, id, size=(640, 480), style=wx.DEFAULT_FRAME_STYLE):        
        wx.Frame.__init__(self, parent, id, title='PyElph', size=size, style=style)
        self.Center()
        
        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Data Store
        self.dataStore = DataStore()
        
        # TODO: design StatusBar
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusText('No image specified', 0)
        self.statusBar.set_function = (lambda string: self.SetStatusText("%s" % string, 1))
        self.statusBar.SetStatusText(u'PyElph \u00A9 2011 Ana Brandusa Pavel, Cristian Vasile', 2)
        
        # image panel
#        self.imagePanel = ImagePanel(self, wx.ID_ANY)
        self.imagePanel = GelDataWindow(self, wx.ID_ANY)
        self.Sizer.Add(self.imagePanel, 1, wx.ALL | wx.EXPAND, 0)
        
        # custom options panel
        self.options = OptionWindow(self, wx.ID_ANY)
        self.Sizer.Add(self.options, 0, wx.ALL | wx.EXPAND, 5)

    def ShowImage(self, image):
        return self.imagePanel.ShowImage(image)

    def SetImage(self, image):
        self.imagePanel.image = image
        self.imagePanel.SetImage()
    
    def SetTitle(self, title):
        wx.Frame.SetTitle(self, 'PyElph - ' + title)
        
    def OnExit(self, event):
        self.Destroy()


class GelAnalysisApp(wx.App):

    def OnInit(self):
        wx.InitAllImageHandlers()
        
        self.frame = GelAnalysis(None, wx.ID_ANY)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        
        return True


if __name__ == '__main__':
    app = GelAnalysisApp(redirect=False)
    app.MainLoop()