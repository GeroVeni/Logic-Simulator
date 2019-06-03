"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas_2D - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import sys
import os

import wx
import wx.adv
import wx.glcanvas as wxcanvas
import wx.dataview as dv
import wx.lib.mixins.listctrl as listmix
import wx.lib.langlistctrl as langlc
from wx.lib.wordwrap import wordwrap
from OpenGL import GL, GLUT

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
from gui_3D import MyGLCanvas_3D

from contextlib import redirect_stdout
import io

# Constants for internationalization
import app_const as appC

# Install a custom displayhook to keep Python from setting the global
# _ (underscore) to the value of the last evaluated expression.  If
# we don't do this, our mapping of _ to gettext can get overwritten.
# This is useful/needed in interactive debugging with PyShell.

def _displayHook(obj):
    if obj is not None:
        print (repr(obj))

# add translation macro to builtin similar to what gettext does
import builtins
builtins.__dict__['_'] = wx.GetTranslation


class GLCanvasWrapper(wxcanvas.GLCanvas):
    def __init__(self, parent):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.context = wxcanvas.GLContext(self)

        # keep reference to parent
        self.parent = parent

        self.draw_2D = MyGLCanvas_2D(self) # default mode
        self.draw_3D = MyGLCanvas_3D(self)

        self.current_mode = self.draw_2D

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.current_mode.on_paint)
        self.Bind(wx.EVT_SIZE, self.current_mode.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.current_mode.on_mouse)

    def toggle_drawing_mode(self):
        """Toggles between 2D and 3D drawing mode."""
        # Unbind events from the canvas
        # TODO handle cases when they cannot unbind events from the canvas
        self.Unbind(wx.EVT_PAINT)
        self.Unbind(wx.EVT_SIZE)
        self.Unbind(wx.EVT_MOUSE_EVENTS)

        if isinstance(self.current_mode, MyGLCanvas_2D):
            self.current_mode = self.draw_3D
        else:
            # Disable 3D open Gl
            GL.glDisable(GL.GL_COLOR_MATERIAL)
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_LIGHTING)
            GL.glDisable(GL.GL_LIGHT0)
            GL.glDisable(GL.GL_LIGHT1)
            GL.glDisable(GL.GL_NORMALIZE)
            self.current_mode = self.draw_2D

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.current_mode.on_paint)
        self.Bind(wx.EVT_SIZE, self.current_mode.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.current_mode.on_mouse)

        self.current_mode.init = False

        # Initialise variables for panning
        self.current_mode.pan_x = 0
        self.current_mode.pan_y = 0
        self.current_mode.last_mouse_x = 0  # previous mouse x position
        self.current_mode.last_mouse_y = 0  # previous mouse y position

        self.current_mode.zoom = 1

        self.recenter()

    def render(self, text):
        """Interface method for the render() fn in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.render(text)

    def restore_state(self):
        """Interface method for the restore_state() fn in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.restore_state()

    def recenter(self):
        """Interface method for the recenter() fn in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.recenter()


class MyGLCanvas_2D():
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.

    recenter(self): Restores canvas to its default pan position and zoom state.

    restore_state(self): Restores the state of the canvas when a new circuit
                         definition file is loaded using the gui, or when the
                         number of monitors is changed in the gui.
    """

    def __init__(self, parent):
        """Initialise canvas properties and useful variables."""
        self.init = False

        # keep reference to parent
        self.parent = parent

        # Text rendering settings
        self.font = GLUT.GLUT_BITMAP_9_BY_15
        self.character_width = 9
        self.character_height = 15

        # 2D rendering settings
        self.border_left = 1  # constant
        self.border_right = 400
        self.border_top = 200
        self.border_bottom = 0  # constant

        self.margin_left = 100  # margin for placement of monitor name
        self.margin_bottom = 30
        self.cycle_width = 20
        self.trace_height = 30
        self.monitor_spacing = 40  # spacing between different monitor_signals
        self.ruler_height = 1.3 * self.character_height

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise variables for zooming
        self.zoom_lower = 0.8
        self.zoom_upper = 5
        # self.zoom = 1
        self.update_zoom_lower_bound()
        self.zoom = self.zoom_lower

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.parent.GetClientSize()
        self.parent.SetCurrent(self.parent.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(self.margin_left, 0, size.width-self.margin_left, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def render(self, text):
        """Handle all drawing operations."""
        # Update pan and zoom variables
        self.update_zoom_lower_bound()
        self.bound_zooming()
        self.update_borders()
        self.bound_panning()

        self.parent.SetCurrent(self.parent.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Enable line below only when debugging the canvas
        # self.render_text(text, 200, 10)

        # Set the left margin for the canvas
        if self.parent.parent.monitors.get_margin() is not None:
            self.margin_left = (
                self.parent.parent.monitors.get_margin() *
                self.character_width +
                10)

        size = self.parent.GetClientSize()

        # Render canvas canvas components
        self.render_grid(size)

        # Render signal traces starting from the top of the canvas
        num_monitors = len(self.parent.parent.monitors.monitors_dictionary)
        if num_monitors > 0:
            y_pos = self.border_bottom + self.margin_bottom + \
                (num_monitors - 1) * self.monitor_spacing

            for device_id, output_id in self.parent.parent.monitors.monitors_dictionary:
                self.render_monitor(
                    device_id,
                    output_id,
                    y_pos,
                    y_pos +
                    self.trace_height, size)
                y_pos -= self.monitor_spacing

        # Render ruler components
        # Ruler background rendered across the whole width of the canvas
        GL.glViewport(0, 0, size.width, size.height)
        self.render_ruler_background(size)
        GL.glViewport(self.margin_left, 0, size.width-self.margin_left, size.height)
        self.render_cycle_numbers(size)
        self.render_grid(size, render_only_on_ruler=True)

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.parent.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.parent.SetCurrent(self.parent.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        size = self.parent.GetClientSize()
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False
        self.update_zoom_lower_bound()
        self.zoom = self.zoom_lower
        self.render("")

    def on_mouse(self, event):
        """Handle mouse events."""
        text = ""
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if text:
            self.render(text)
        else:
            self.parent.Refresh()  # triggers the paint event

    def bound_panning(self):
        """Bound pan_x, pan_y variables with respect to the signal traces."""
        size = self.parent.GetClientSize()
        # allowable_pan_right = -(self.border_right - size.width / self.zoom)
        allowable_pan_right = -self.border_right*self.zoom + size.width
        allowable_pan_left = self.border_left
        allowable_pan_bottom = self.border_bottom
        allowable_pan_top = -(self.border_top * self.zoom) + size.height

        # if true, some part of the signal traces is hidden (x dir)
        if allowable_pan_right < 0:
            if self.pan_x < allowable_pan_right:
                self.pan_x = allowable_pan_right
        else:
            if self.pan_x < 0:
                self.pan_x = 0

        if self.pan_x > allowable_pan_left:
            self.pan_x = allowable_pan_left

        if allowable_pan_top < 0: # if true, some monitors are hidden (y dir)
            if self.pan_y < allowable_pan_top:
                self.pan_y = allowable_pan_top
        else:
            if self.pan_y < 0:
                self.pan_y = 0

        if self.pan_y > allowable_pan_bottom:
            self.pan_y = allowable_pan_bottom

    def bound_zooming(self):
        """Bound zoom."""
        if self.zoom > self.zoom_upper:
            self.zoom = self.zoom_upper
        elif self.zoom < self.zoom_lower:
            self.zoom = self.zoom_lower

    def update_zoom_lower_bound(self):
        """Adjust zoom lower bound when the canvas is resized or the number of
        monitors changes."""
        size = self.parent.GetClientSize()

        # Allow a max number of 9 monitors to be displayed at once
        num_monitors = min(9, len(self.parent.parent.monitors.monitors_dictionary))

        # Adjust zoom bounds depending on number of monitors
        visible_objects_height = self.margin_bottom + \
            num_monitors * self.monitor_spacing + self.ruler_height
        self.zoom_lower = min(
            size.height /
            (visible_objects_height),
            self.zoom_upper)

    def update_borders(self):
        """Update the borders of the canvas depending on the number of monitors
        and the number of cycles to be simulated."""
        num_monitors = len(self.parent.parent.monitors.monitors_dictionary)
        # self.border_top depends only on the number of monitors
        self.border_top = self.border_bottom + self.margin_bottom + \
            num_monitors * self.monitor_spacing + self.ruler_height / self.zoom
        # self.border_right depends only on the number of cycles to be
        # simulated
        self.border_right = self.parent.parent.cycles_completed * self.cycle_width

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(self.font, ord(character))

    def render_monitor(self, device_id, output_id, y_min, y_max, size):
        """Handle monitor name and signal trace drawing for a single
        monitor."""
        monitor_name = self.parent.parent.devices.get_signal_name(
            device_id, output_id)
        signal_list = self.parent.parent.monitors.monitors_dictionary[(
            device_id, output_id)]

        # Draw monitor name
        # Render on different viewport
        GL.glViewport(0, 0, self.margin_left, size.height)
        text_x_pos = -self.pan_x/self.zoom + 4
        text_y_pos = (y_min + y_max) / 2 - \
            self.character_height / (2 * self.zoom)
        self.render_text(monitor_name, text_x_pos, text_y_pos)
        GL.glViewport(self.margin_left, 0, size.width-self.margin_left, size.height)

        # Draw rectangles underneath HIGH signals for more clarlity
        x_pos = 0
        fill_color = [103 / 255, 218 / 255, 255 / 255]
        GL.glColor3fv(fill_color)
        for signal in signal_list:
            if (signal == self.parent.parent.devices.HIGH) or (signal == self.parent.parent.devices.RISING):
                self.render_rectangle((x_pos, y_min), (x_pos + self.cycle_width, y_max))
                GL.glBegin(GL.GL_LINE_STRIP)
                GL.glVertex2f(x_pos, y_min)
                GL.glVertex2f(x_pos + self.cycle_width, y_min)
                GL.glEnd()
            x_pos += self.cycle_width

        # Draw signal trace
        x_pos = 0
        currently_drawing = False
        trace_color = [0 / 255, 122 / 255, 193 / 255]
        GL.glColor3fv(trace_color)  # signal trace is blue
        GL.glLineWidth(1.5)
        for signal in signal_list:
            if signal == self.parent.parent.devices.BLANK:
                if currently_drawing:
                    GL.glEnd()
                    currently_drawing = False
                x_pos += self.cycle_width
            else:
                if not currently_drawing:
                    GL.glBegin(GL.GL_LINE_STRIP)
                    currently_drawing = True
                if signal == self.parent.parent.devices.HIGH:
                    y = y_max
                if signal == self.parent.parent.devices.LOW:
                    y = y_min
                if signal == self.parent.parent.devices.RISING:
                    y = y_max
                if signal == self.parent.parent.devices.FALLING:
                    y = y_min
                GL.glVertex2f(x_pos, y)
                x_pos += self.cycle_width
                GL.glVertex2f(x_pos, y)

        if currently_drawing:
            GL.glEnd()
            currently_drawing = False

    def render_line(self, start_point, end_point):
        """Render a straight line on the canvas, with the given end points."""
        # check validity of arguments
        if not (
            isinstance(
                start_point,
                tuple) and isinstance(
                end_point,
                tuple)):
            raise TypeError(
                "start_point and end_point arguments must be of Type tuple")
        if (len(start_point) != 2 or len(end_point) != 2):
            raise ValueError("start_point and end_point arguments must be \
                            tuples of length 2")
        # draw line
        GL.glLineWidth(1)
        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex2f(start_point[0], start_point[1])
        GL.glVertex2f(end_point[0], end_point[1])
        GL.glEnd()

    def render_rectangle(self, bottom_left_point, top_right_point):
        """Render a rectangle on the canvas, with the given points."""
        # check validity of arguments
        if not (
            isinstance(
                bottom_left_point,
                tuple) and isinstance(
                top_right_point,
                tuple)):
            raise TypeError("bottom_left_point and top_right_point arguments \
                            must be of Type tuple")
        if (len(bottom_left_point) != 2 or len(top_right_point) != 2):
            raise ValueError("bottom_left_point and top_right_point arguments \
                             must be tuples of length 2")
        # draw rectangle
        GL.glLineWidth(1)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(bottom_left_point[0], bottom_left_point[1])
        GL.glVertex2f(top_right_point[0], bottom_left_point[1])
        GL.glVertex2f(top_right_point[0], top_right_point[1])
        GL.glVertex2f(bottom_left_point[0], top_right_point[1])
        GL.glEnd()

    def render_cycle_numbers(self, size):
        """Handle cycle numbers drawing at the top of the canvas (ruler)."""
        if self.parent.parent.cycles_completed == 0:
            return

        for cycle in range(self.parent.parent.cycles_completed):
            # count number of digits in number
            num_digits = len(str(cycle + 1))
            # print cycle number
            text_x_pos = - 0.5 * num_digits * self.character_width/self.zoom +\
                (cycle + 0.5) * self.cycle_width
            text_y_pos = (size.height - self.pan_y -
                          self.character_height) / self.zoom
            self.render_text(str(cycle + 1), text_x_pos, text_y_pos)

    def render_ruler_background(self, size):
        """Draw a background for the ruler."""
        ruler_color = [200 / 255, 230 / 255, 255 / 255]
        # Make sure transformations don't affect other renderings
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glColor3fv(ruler_color)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(0.0, size.height)
        GL.glVertex2f(0.0, size.height - self.ruler_height)
        GL.glVertex2f(size.width, size.height - self.ruler_height)
        GL.glVertex2f(size.width, size.height)
        GL.glEnd()
        GL.glPopMatrix()

    def render_grid(self, size, render_only_on_ruler=False):
        """Draw a grid for separating the different cycles in the traces."""
        if self.parent.parent.cycles_completed == 0:
            return

        line_y_pos_end = self.border_bottom + \
            (- self.pan_y + size.height) / self.zoom

        # render either only on the ruler or on the whole the canvas
        if render_only_on_ruler:
            line_y_pos_start = line_y_pos_end - self.ruler_height / self.zoom
        else:
            line_y_pos_start = self.border_bottom - self.pan_y / self.zoom

        # render vertical lines
        GL.glColor3f(0.9, 0.9, 0.9)  # light grey color
        line_x_pos = 0
        self.render_line((line_x_pos, line_y_pos_start),
                         (line_x_pos, line_y_pos_end))
        for cycle in range(self.parent.parent.cycles_completed):
            line_x_pos += self.cycle_width
            self.render_line((line_x_pos, line_y_pos_start),
                             (line_x_pos, line_y_pos_end))

    def recenter(self):
        """Restore canvas to its default pan position and zoom state."""
        self.pan_x = self.border_left
        self.pan_y = self.border_bottom
        self.zoom = self.zoom_lower
        self.init = False
        self.render("Recenter canvas")

    def restore_state(self):
        """Restore the state of the canvas when a new circuit definition file
        is loaded using the gui, or when the number of monitors is changed in
        the gui.

        restore_state() should be called whenever the gui method
        on_open() and set_monitor() is called."""
        self.init = False
        self.update_zoom_lower_bound()
        self.zoom = self.zoom_lower
        self.render("")


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_spin(self, event): Event handler for when the user changes the spin
                           control value.

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_text_box(self, event): Event handler for when the user enters text.
    """

    def __init__(self, title):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))
        self.names = Names()
        self.devices = Devices(self.names)
        self.network = Network(self.names, self.devices)
        self.monitors = Monitors(self.names, self.devices, self.network)

        # work around for Python stealing "_"
        sys.displayhook = _displayHook

        # Add locale path and update the language
        self.locale = None
        wx.Locale.AddCatalogLookupPathPrefix('locale')
        #self.update_language(self.appConfig.Read(u"Language"))
        sys_lang = wx.Locale.GetSystemLanguage()
        lang_name = wx.Locale.GetLanguageCanonicalName(sys_lang)
        self.update_language(lang_name[:2])

        # Add fonts
        self.NORMAL_FONT = wx.TextAttr()
        self.MONOSPACE_FONT = wx.TextAttr(
            'BLACK', font=wx.Font(
                wx.FontInfo(10).Family(
                    wx.FONTFAMILY_TELETYPE)))

        # Add IDs for menu and toolbar items
        self.ID_OPEN = 1001
        self.ID_CENTER = 1002
        self.ID_RUN = 1003
        self.ID_CONTINUE = 1004
        self.ID_CYCLES_CTRL = 1005
        self.ID_HELP = 1006
        self.ID_CLEAR = 1007
        self.ID_TOGGLE_3D = 1008
        self.ID_LANG = 1009

        # Configure the file menu
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        runMenu = wx.Menu()
        helpMenu = wx.Menu()
        menuBar = wx.MenuBar()

        fileMenu.Append(self.ID_OPEN, _("&Open") + "\tCtrl+O")
        fileMenu.Append(wx.ID_EXIT, _("&Exit"))

        viewMenu.Append(self.ID_CENTER, _("&Center") + "\tCtrl+E")
        viewMenu.Append(self.ID_TOGGLE_3D, _("&Toggle 2D/3D vew") + "\tCtrl+T")
        viewMenu.Append(self.ID_CLEAR, _("&Clear Activity Log") + "\tCtrl+L")
        viewMenu.Append(self.ID_LANG, _("Change &Language"))

        runMenu.Append(self.ID_RUN, _("&Run") + "\tCtrl+R")
        runMenu.Append(self.ID_CONTINUE, _("&Continue") + "\tCtrl+Shift+C")

        helpMenu.Append(self.ID_HELP, _("&Help") + "\tCtrl+H")
        helpMenu.Append(wx.ID_ABOUT, _("&About"))

        menuBar.Append(fileMenu, _("&File"))
        menuBar.Append(viewMenu, _("&View"))
        menuBar.Append(runMenu, _("&Simulation"))
        menuBar.Append(helpMenu, _("&Help"))
        self.SetMenuBar(menuBar)

        # Load icons
        openIcon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR)
        centerIcon = wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_TOOLBAR)
        runIcon = wx.Bitmap("res/run.png")
        continueIcon = wx.Bitmap("res/continue.png")
        infoIcon = wx.Bitmap("res/info.png")
        self.layout2dIcon = wx.Bitmap("res/layout2d.png")
        self.layout3dIcon = wx.Bitmap("res/layout3d.png")
        flagIcon = langlc.GetLanguageFlag(self.locale.GetLanguage())

        # Configure toolbar
        # Keep a reference to the toolBar to update its icons
        self.toolBar = self.CreateToolBar()
        # TODO Change names icons and event handling of tools
        # TODO Add Shorthelp option to tools (i.e. tooltip)
        # TODO Create matching options in the fileMenu and associate them
        # with shortcuts
        self.spin = wx.SpinCtrl(self.toolBar, value='10')
        self.toolBar.AddTool(self.ID_OPEN, "Tool2", openIcon)
        self.toolBar.AddSeparator()
        self.toolBar.AddTool(self.ID_CENTER, "Tool3", centerIcon)
        self.toolBar.AddSeparator()
        self.toolBar.AddTool(self.ID_RUN, "Tool4", runIcon)
        self.toolBar.AddTool(self.ID_CONTINUE, "Tool5", continueIcon)
        self.toolBar.AddControl(self.spin, "SpinCtrl")
        self.toolBar.AddTool(self.ID_TOGGLE_3D, "Tool6", self.layout2dIcon)
        self.toolBar.AddSeparator()
        self.toolBar.AddTool(self.ID_LANG, "Tool7", flagIcon)
        self.toolBar.AddSeparator()
        self.toolBar.AddTool(self.ID_HELP, "Tool1", infoIcon, shortHelp=_("Help"))
        self.SetToolBar(self.toolBar)

        self.canvas_mode = '2d' # current display mode of canvas
        self.cycles_completed = 0  # number of simulation cycles completed
        # Canvas for drawing signals
        self.canvas = GLCanvasWrapper(self)

        # Configure the widgets
        self.activity_log = wx.TextCtrl(
            self,
            wx.ID_ANY,
            _("Ready. Please load a file."),
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.activity_log_label = wx.StaticText(self, label=_("Activity Log"))

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        left_sizer.Add(self.canvas, 3, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.activity_log_label,
                       0.2, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.activity_log, 1, wx.EXPAND | wx.ALL, 5)

        # right_sizer.Add(self.spin, 0, wx.ALL, 5)
        right_sizer = self.make_right_sizer()

        main_sizer.Add(left_sizer, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(right_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizeHints(1200, 800)
        self.SetSizer(main_sizer)

    def make_right_sizer(self):
        """Helper function that creates the right sizer"""
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the notebook to hold tabs
        self.notebook = wx.Notebook(self, size=(200, -1))

        # Create the tabs
        self.monitor_tab = CustomTab(self.notebook)
        self.switch_tab = CustomTab(self.notebook)
        self.monitor_tab.set_on_item_selected_listener(self.set_monitor)
        self.switch_tab.set_on_item_selected_listener(self.set_switch)

        self.notebook.AddPage(self.monitor_tab, _("Monitors"))
        self.notebook.AddPage(self.switch_tab, _("Switches"))

        right_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        return right_sizer

    def update_language(self, lang):
        """
        Update the language to the requested one.

        Make *sure* any existing locale is deleted before the new
        one is created.  The old C++ object needs to be deleted
        before the new one is created, and if we just assign a new
        instance to the old Python variable, the old C++ locale will
        not be destroyed soon enough, likely causing a crash.

        :param string `lang`: one of the supported language codes

        """
        # if an unsupported language is requested default to English
        if lang in appC.supLang:
            selLang = appC.supLang[lang]
        else:
            selLang = wx.LANGUAGE_ENGLISH

        if self.locale:
            assert sys.getrefcount(self.locale) <= 2
            del self.locale

        # create a locale object for this language
        self.locale = wx.Locale(selLang)
        if self.locale.IsOk():
            self.locale.AddCatalog(appC.langDomain)
        else:
            self.locale = None

    def update_texts(self):
        """Updates the text fields around the application after a change
        of locale.
        """

        # Update menu items
        # WARNING: This update assumes a certain order of menus
        # Does NOT scale; Consider refactoring for robustness
        # 0 -> files
        # 1 -> view
        # 2 -> simulation
        # 3 -> help
        menuBar = self.GetMenuBar()
        menuBar.SetMenuLabel(0, _("&File"))
        menuBar.SetMenuLabel(1, _("&View"))
        menuBar.SetMenuLabel(2, _("&Simulation"))
        menuBar.SetMenuLabel(3, _("&Help"))

        # Update menu subitems
        menuBar.SetLabel(self.ID_OPEN, _("&Open") + "\tCtrl+O")
        menuBar.SetLabel(wx.ID_EXIT, _("&Exit"))

        menuBar.SetLabel(self.ID_CENTER, _("&Center") + "\tCtrl+E")
        menuBar.SetLabel(self.ID_TOGGLE_3D, _("&Toggle 2D/3D vew") + "\tCtrl+T")
        menuBar.SetLabel(self.ID_CLEAR, _("&Clear Activity Log") + "\tCtrl+L")
        menuBar.SetLabel(self.ID_LANG, _("Change &Language"))

        menuBar.SetLabel(self.ID_RUN, _("&Run") + "\tCtrl+R")
        menuBar.SetLabel(self.ID_CONTINUE, _("&Continue") + "\tCtrl+Shift+C")

        menuBar.SetLabel(self.ID_HELP, _("&Help") + "\tCtrl+H")
        menuBar.SetLabel(wx.ID_ABOUT, _("&About"))

        # Update toolbar tooltips
        # TODO

        # Update flag icon
        flagIcon = langlc.GetLanguageFlag(self.locale.GetLanguage())
        self.GetToolBar().SetToolNormalBitmap(self.ID_LANG, flagIcon)

        # Update right panel
        self.notebook.SetPageText(0, _("Monitors"))
        self.notebook.SetPageText(1, _("Switches"))
        self.monitor_tab.update_texts()
        self.switch_tab.update_texts()

        # Update static texts
        self.activity_log_label.SetLabel(_("Activity Log"))

    def update_tabs(self):
        """Update the tabs with new values."""

        # Get monitor names
        [mons, non_mons] = self.monitors.get_signal_names()

        # Get switch names
        switch_ids = self.devices.find_devices(self.devices.SWITCH)
        switch_names = [self.names.get_name_string(
            sw_id) for sw_id in switch_ids]
        switch_signals = [self.devices.get_device(
            sw_id).switch_state for sw_id in switch_ids]
        switch_states = [
            True if sig in [
                self.devices.HIGH,
                self.devices.RISING] else False for sig in switch_signals]

        # Reset tab elements
        self.monitor_tab.clear()
        self.monitor_tab.append(list(zip(mons, [True for i in mons])))
        self.monitor_tab.append(list(zip(non_mons, [False for i in non_mons])))
        self.switch_tab.clear()
        self.switch_tab.append(list(zip(switch_names, switch_states)))

    def set_monitor(self, monitor_name, is_active):
        """Activate or deactivate a monitor.

        Parameters
        ----------
        monitor_id: The id of the monitor to change state
        is_active: The state of the monitor; True to activate
                   and False to deactivate
        """
        # Split the monitor to device name and port name if it exists
        splt = monitor_name.split('.')
        if len(splt) == 1:
            # No port given
            device_id = self.names.query(splt[0])
            port_id = None
        elif len(splt) == 2:
            # Port given
            device_id = self.names.query(splt[0])
            port_id = self.names.query(splt[1])
        else:
            # TODO: Print error
            pass

        if device_id is None:
            # TODO: Reformat error text for consistency with parser
            self.log_message(
                _("Error: Monitor {} not found.").format(monitor_name))
            return
        # Add/remove monitor
        if is_active:
            action = _("activated")
            monitor_error = self.monitors.make_monitor(device_id, port_id,
                                                       self.cycles_completed)
            if monitor_error == self.monitors.NO_ERROR:
                self.log_message(
                    _("Monitor {} was {}.").format(
                        monitor_name, action))
            else:
                # TODO: Print error
                return
        else:
            action = _("deactivated")
            if self.monitors.remove_monitor(device_id, port_id):
                self.log_message(
                    "Monitor {} was {}.".format(
                        monitor_name, action))
            else:
                # TODO: Print error
                return
        self.canvas.restore_state()
        self.canvas.render(_("Monitor changed"))

    def set_switch(self, switch_name, is_on):
        """Turn a swtich on and off.

        Parameters
        ----------
        switch_id: The id of the switch to change output
        is_on: The state of the monitor; True to turn on
               and False to turn off

        """
        # Get the switch id
        switch_id = self.names.query(switch_name)

        if switch_id is None:
            # TODO: Reformat error text for consistency with parser
            self.log_message(
                _("Error: Monitor {} not found.").format(monitor_name))
            return
        # Turn on/off the switch
        if is_on:
            switch_state = 1
            state_text = _("ON")
        else:
            switch_state = 0
            state_text = _("OFF")
        if self.devices.set_switch(switch_id, switch_state):
            self.log_message(
                _("Switch {} was switched {}").format(
                    switch_name, state_text))
        else:
            # TODO: Print error
            return

    def clear_log(self):
        """Clear the error log."""
        self.activity_log.Clear()

    def log_message(self, text, style=None):
        """Add message to the error log."""
        if style is not None:
            self.activity_log.SetDefaultStyle(style)
        self.activity_log.AppendText("\n" + str(text))
        self.activity_log.ShowPosition(self.activity_log.GetLastPosition())
        self.activity_log.SetDefaultStyle(self.NORMAL_FONT)

    #################
    # author: Jorge #
    #################

    def run_parser(self, file_path):
        """Call parse_network() from path specified

        To do so first reinitzialize all modules and cycles_completed.
        """
        # clear all at the begging
        self.cycles_completed = 0
        self.names = Names()
        self.devices = Devices(self.names)
        self.network = Network(self.names, self.devices)
        self.monitors = Monitors(self.names, self.devices, self.network)
        self.scanner = Scanner(file_path, self.names)
        self.parser = Parser(self.names, self.devices, self.network,
                             self.monitors, self.scanner)
        # Capture the stdout from parse_network()
        captured_stdout = io.StringIO()
        with redirect_stdout(captured_stdout):
            if self.parser.parse_network():
                self.log_message(_("Succesfully parsed network."))
            else:
                self.log_message(_("Failed to parse network."))
                # Show error messages captured in activity log
                self.log_message(captured_stdout.getvalue(),
                                 self.MONOSPACE_FONT)

    def on_open(self):
        """Open the file browser and parse the file chosen."""
        text = _("Open file dialog.")
        openFileDialog = wx.FileDialog(
            self,
            _("Open"),
            wildcard="Circuit Definition files (*.txt;*.lcdf)|*.txt;*.lcdf",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR)
        res = openFileDialog.ShowModal()
        if res == wx.ID_OK:  # user selected a file
            file_path = openFileDialog.GetPath()
            self.log_message(_("File opened: {}").format(file_path))
            self.run_parser(file_path)
            self.canvas.restore_state()
            self.update_tabs()
            self.canvas.render(_("Opened file"))

    def run_network(self, cycles):
        """Run the network for the specified number of simulation cycles.

        Return True if successful.
        """
        for _ in range(cycles):
            if self.network is None:
                self.log_message(_("Error! No file loaded."))
                return False
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                self.log_message(_("Error! Network oscillating."))
                return False
        return True

    def run_command(self):
        """Run the simulation from scratch."""
        self.cycles_completed = 0
        cycles = self.spin.GetValue()  # this must get input from other box

        if cycles is not None:  # if the number of cycles provided is valid
            self.monitors.reset_monitors()
            self.log_message(_("Running for {} cycles").format(cycles))
            self.devices.cold_startup()
            if self.run_network(cycles):
                self.cycles_completed += cycles

    def on_run(self):
        """Run the run_command when run button pressed."""
        self.run_command()
        self.canvas.recenter()
        self.canvas.render(_("RUN"))

    def continue_command(self):
        """Continue a previously run simulation."""
        cycles = self.spin.GetValue()
        if cycles is not None:  # if the number of cycles provided is valid
            if self.cycles_completed == 0:
                self.log_message(_("Error! Nothing to continue. Run first."))
            elif self.run_network(cycles):
                self.cycles_completed += cycles
                self.log_message(_("Continuing for {} cycles. Total: {}").format(cycles, self.cycles_completed))

    def on_continue(self):
        """Run the continue_command when run button pressed."""
        self.continue_command()
        self.canvas.render(_("Continue"))

    ####################
    # author: Dimitris #
    ####################

    def on_center(self):
        """Centers the canvas to its default state of zoom and panning."""
        self.log_message(_("Center canvas."))
        self.canvas.recenter()

    def on_help(self):
        """Shows a help window with user instructions."""
        help_title = _("Help - Program controls ")
        # TODO Find a more elegant way to provide localisation for this text
        help_content = ("" +
            _("Shortcuts: \n") +
            _("Ctrl + O: Open file\n") +
            _("Ctrl + H: Help\n") +
            _("Ctrl + R: Run\n") +
            _("Ctrl + Shift + C: Continue\n") +
            _("Ctrl + E: Center canvas\n") +
            _("Ctrl + L: Clear activity log\n\n") +
            _("User Instructions:\n") +
            _("Use the Open file button to select ") +
            _("the desired circuit defnition file.") +
            _("If the file contains no errors the activity") +
            _(" log at the bottom of the window") +
            _("will read \"Succesfully parsed network\". ") +
            _("If there are errors, the error log") +
            _("will read \"Failed to parse network\".\n\n") +
            _("If the network was parsed correctly it can be ran. ") +
            _("Use the plus and minus on the") +
            _("cycle selector to select the desired number") +
            _(" of cycles for the simulation or") +
            _("type in th desired number. Press the Run ") +
            _("button to run the simulator for the number") +
            _("of cycles selected and display the waveforms ") +
            _("at the current monitor points (from a") +
            _("cold-startup of the circuit). Press the ") +
            _("Continue button to run the simulator") +
            _("for an additional number of cycles as selected ") +
            _("in the cycle selector and") +
            _("display the waveforms at the current monitor points.\n\n") +
            _("The canvas can be restored to its default state ") +
            _("of position and zoomby") +
            _("selecting the center button.\n\n") +
            _("Different monitor points can be set ") +
            _("and zapped by first selecting the") +
            _("Monitors tab on the right panel, and then ") +
            _("selecting the desired monitor") +
            _("point from the list.\n\n") +
            _("Switches can be operated by first selecting ") +
            _("the Switches tab on the right") +
            _("panel, and then selecting the desired switches.")
        )

        wx.MessageBox(help_content,
                      help_title, wx.ICON_INFORMATION | wx.OK)

    def  on_toggle_3d_vew(self):
        """Toggle 3D view."""
        if self.canvas_mode == '2d':
            self.canvas_mode = '3d'
            self.toolBar.SetToolNormalBitmap(self.ID_TOGGLE_3D, self.layout3dIcon)
        else:
            self.canvas_mode = '2d'
            self.toolBar.SetToolNormalBitmap(self.ID_TOGGLE_3D, self.layout2dIcon)
        self.canvas.toggle_drawing_mode()

    ##################
    # author: George #
    ##################

    def on_lang_change(self):
        """Show dialog for language change."""
        dlg = LangDialog(self, -1, _("Pick your language"),
                         self.locale.GetLanguage(), size=(350, 200),
                         style=wx.DEFAULT_DIALOG_STYLE,
                         )

        # This does not return until the dialog is closed.
        val = dlg.ShowModal()

        sel_lang = dlg.GetLangSelected()
        if val == wx.ID_OK:
            # User pressed OK
            self.update_language(wx.Locale.GetLanguageCanonicalName(sel_lang)[:2])
            self.update_texts()

        dlg.Destroy()


    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        elif Id == wx.ID_ABOUT:
            wx.MessageBox(_("Logic Simulator\nCreated by Psylinders\n2019"),
                          _("About Logsim"), wx.ICON_INFORMATION | wx.OK)
        elif Id == self.ID_OPEN:  # file dialog
            self.on_open()
        elif Id == self.ID_RUN:  # run button
            self.on_run()
        elif Id == self.ID_CONTINUE:  # continue button
            self.on_continue()
        elif Id == self.ID_CENTER:  # center button
            self.on_center()
        elif Id == self.ID_HELP:  # help button
            self.on_help()
        elif Id == self.ID_CLEAR:  # help button
            self.clear_log()
        elif Id == self.ID_TOGGLE_3D: # togge 3D view button
            self.on_toggle_3d_vew()
        elif Id == self.ID_LANG:
            self.on_lang_change()

    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        # TODO Remove ?
        text_box_value = self.text_box.GetValue()
        text = "".join([_("New text box value: "), text_box_value])
        self.canvas.render(text)


class CustomTab(wx.Panel):
    """Configure the tabs added in the notebook.

    This class provides a generalised method to create tabs with list,
    to aid the creation of the Switch tab and the Monitors tab.

    Parameters
    ----------
    parent: parent of the panel.

    Public methods
    --------------
    def append(self, name_list): Appends the name_list in the item list.

    def clear(self): Clears the item list.

    def update_texts(self): Updates the strings during a locale change.

    def on_item_selected(self, event): Event handler for when an item is
                                       selected.

    def set_on_item_selected_listener(self, listener):
        Setter function for external listener to the on_item_selected event.
    """

    def __init__(self, parent):
        """Attach parent to panel and create the list control widget."""
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Constants
        self.LIST_WIDTH = 165
        self.LIST_STATUS_WIDTH = 90
        self.TEXT_COLUMN = 0
        self.TOGGLE_COLUMN = 1

        self.gui = parent.GetParent()

        # Create Listener
        self.on_item_selected_listener = None

        # Create ListCtrl
        self.item_list = dv.DataViewListCtrl(
            self, style=wx.dataview.DV_ROW_LINES)
        self.item_list.AppendIconTextColumn(_("Names"), width=140, flags=0)
        self.item_list.AppendToggleColumn(
            _("Status"), width=60, align=wx.ALIGN_CENTER, flags=0)
        self.item_list.Bind(
            dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED,
            self.on_item_selected)

        sizer.Add(self.item_list, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def set_on_item_selected_listener(self, listener):
        """Set the listener when an item state is changed."""
        self.on_item_selected_listener = listener

    def on_item_selected(self, event):
        """Handle the event when the user changes the state of an item."""
        if self.on_item_selected_listener is None:
            return
        row = self.item_list.ItemToRow(event.GetItem())
        name = self.item_list.GetValue(row, self.TEXT_COLUMN).GetText()
        state = self.item_list.GetToggleValue(row, self.TOGGLE_COLUMN)
        self.on_item_selected_listener(name, state)

    def update_texts(self):
        """Updates the text fields around the application after a change
        of locale.
        """
        self.item_list.GetColumn(0).SetTitle(_("Names"))
        self.item_list.GetColumn(1).SetTitle(_("Status"))

    def clear(self):
        """Clears the items in the list."""
        self.item_list.DeleteAllItems()

    def append(self, name_list):
        """Appends the name_list in the item list."""
        # ic = wx.Icon(wx.Bitmap(16, 16))
        CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
        ic = wx.Icon(CURRENT_PATH + '/res/empty_circle_w1.png')
        for cnt in range(len(name_list)):
            i, val = name_list[cnt]
            it = dv.DataViewIconText("" + i)
            self.item_list.AppendItem([it, val])


class LangDialog(wx.Dialog):
    """Dialog for change of locale.

    This class inherits from the wx.Dialog class to create a dialog for
    selecting a locale by the user.

    Parameters
    ----------
    parent: parent of the dialog. (see wx.Dialog)
    id: id of the dialog. (see wx.Dialog)
    title: title of the dialog. (see wx.Dialog)
    sel_lang: initially selected language.
    size: size of the dialog. (see wx.Dialog)
    pos: position of the dialog. (see wx.Dialog)
    style: style of the dialog. (see wx.Dialog)
    name: name of the dialog. (see wx.Dialog)

    Public methods
    --------------
    onItemSelected(self, event): Event handler for when the user selects an
                                 item

    onItemActivated(self, event): Event handler for when the user activates an
                                  item (double click or ENTER)

    GetLangSelected(self): Getter function for lang_selected property
    """

    def __init__(
            self, parent, id, title, sel_lang, size=wx.DefaultSize, pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE, name='dialog'
            ):
        """Create language dialog to allow the user to change locale."""

        # Create the dialog
        wx.Dialog.__init__(self)
        self.Create(parent, id, title, pos, size, style, name)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.lang_selected = sel_lang
        self.lang_listctrl = langlc.LanguageListCtrl(self, size=(0,-1), filter=langlc.LC_ONLY, only=[wx.LANGUAGE_ENGLISH, wx.LANGUAGE_GREEK], select=self.lang_selected)
        sizer.Add(self.lang_listctrl, 0, wx.EXPAND, 0)

        # Add dialog buttons
        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Bind event listeners
        self.lang_listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.lang_listctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated)

    def onItemSelected(self, event):
        """Method called when user selects another language."""
        self.lang_selected = self.lang_listctrl.GetLanguage()

    def onItemActivated(self, event):
        """Method called when item is double clicked or ENTER is pressed."""
        self.lang_selected = self.lang_listctrl.GetLanguage()
        self.EndModal(wx.ID_OK)

    def GetLangSelected(self):
        """Getter method for self.lang_selected."""
        return self.lang_selected
