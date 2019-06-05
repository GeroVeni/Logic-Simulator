"""This module encapsulates all color related operation, to allow the app
to have a consistent color scheme.

Classes:
----------
ColorScheme - The class that determines the color corresponding to an id and
              a style
"""


class ColorScheme:
    """The class that determines the color corresponding to an id and a
    style.

    Parameters:
    -----------
    color_list: Colors corresponding to the normal style
    light_color_list: Colors corresponding to the light style
    medium_color_list: Colors corresponding to the medium style

    Public methods:
    ---------------
    get_color(self, color_id, style): Returns the corresponding color
    get_next_color(self): Returns the next color
    reset_color(self): Resets the color pointer to the first color
    get_default(): (static) Return the default colorscheme
    """

    def __init__(self, color_list=[], light_color_list=[],
                 medium_color_list=[]):
        """Creates the colorscheme and assigns a list of colors."""
        if not isinstance(color_list, list):
            raise ValueError("color_list should be a list of colors")
        if not isinstance(light_color_list, list):
            raise ValueError("light_color_list should be a list of colors")
        if not isinstance(medium_color_list, list):
            raise ValueError("medium_color_list should be a list of colors")
        # TODO Check that lists have the same size
        self.next_col = 0
        self.color_list = color_list
        self.light_color_list = light_color_list
        self.medium_color_list = medium_color_list

    def reset_color(self):
        """Reset the color counter and starting getting colors from the
        start.
        """
        self.next_col = 0

    def get_next_color(self, style=None):
        """Get the next color in the given style."""
        col = self.get_color(self.next_col, style)
        self.next_col += 1
        return col

    def get_color(self, color_id, style=None):
        """Gets a color from the colorscheme."""
        if style == 'medium':
            return self.medium_color_list[
                    color_id % len(self.medium_color_list)]
        elif style == 'light':
            return self.light_color_list[color_id % len(self.light_color_list)]
        else:
            return self.color_list[color_id % len(self.color_list)]

    @staticmethod
    def get_default():
        """Returns the default ColorScheme. See Tableau 10"""
        norm = [[31, 119, 180], [255, 127, 14],
                [44, 160, 44], [214, 39, 40],
                [148, 103, 189], [140, 86, 75],
                [227, 119, 194], [127, 127, 127],
                [188, 189, 34], [23, 190, 207]]

        light = [[174, 199, 232], [255, 187, 120],
                 [152, 223, 138], [255, 152, 150],
                 [197, 176, 213], [196, 156, 148],
                 [247, 182, 210], [199, 199, 199],
                 [219, 219, 141], [158, 218, 229]]

        medium = [[114, 199, 232], [255, 158, 74],
                  [103, 191, 92], [237, 102, 93],
                  [173, 139, 201], [168, 120, 110],
                  [237, 151, 202], [162, 162, 162],
                  [205, 204, 93], [109, 204, 218]]

        norm = [[col_com / 255 for col_com in col] for col in norm]
        light = [[col_com / 255 for col_com in col] for col in light]
        medium = [[col_com / 255 for col_com in col] for col in medium]

        return ColorScheme(norm, light, medium)
