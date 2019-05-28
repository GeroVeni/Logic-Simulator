"""Create a utility class to simpify the creation of icons.

Used in the Logic Simulator project, in the gui module.

Classes:
--------
IconFactory - creates a specified icon.
"""


class IconFactory:
    """Create a specified icon.
    
    This class is a convenience for creating wx.Bitmap objects using the
    wx.ArtProvider and then converting them to wx.Icon objects.

    Parameters:
    -----------
    id: 

    Public methods:
    ---------------
    create(self, id, client, size): Creates a wx.Icon using a wx.Bimap.
    """

    def __init__(self):

