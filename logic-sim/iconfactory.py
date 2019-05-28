"""Create a utility class to simpify the creation of icons.

Used in the Logic Simulator project, in the gui module.

Classes:
--------
IconFactory - creates a specified icon.
"""


import wx

class IconFactory:
    """Create a specified icon.
    
    This class is a convenience for creating wx.Bitmap objects
    and then converting them to wx.Icon objects.

    Parameters:
    -----------
    id: wx.ArtID unique identifier of the bitmap
    client: wx.ArtClient identifier of the client (i.e. who is asking
            for the bitmap
    size: wx.Size of the returned bitmap or wx.DefaultSize if
          size doesn't matter

    Public methods:
    ---------------
    getIcon(self): Creates a wx.Icon using a wx.Bitmap.
    """

    def __init__(self, id, client=wx.ART_OTHER, size=wx.DefaultSize):
        self.id = id
        self.client = client
        self.size = size

    def getIcon(self):
        bmp = wx.ArtProvider.GetBitmap(self.id, self.client, self.size)
