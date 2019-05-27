"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.
    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

        self.devices = devices
        self.monitors = monitors

        self.cycles_completed = 30 # updated when the gui calls render() TODO initialize to 0

        # Variables for drawing text
        self.font = GLUT.GLUT_BITMAP_9_BY_15
        self.character_width = 9
        self.character_height = 15

        # Variables for canvas drawing
        self.border_left = 10 # constant
        self.border_right = 400
        self.border_top = 200
        self.border_bottom = 0 # constant

        self.zoom_lower = 0.8
        self.zoom_upper = 5

        self.margin_left = 100 # margin for placement of device name
        self.margin_bottom = 30
        self.cycle_width = 20
        self.trace_height = 30
        self.monitor_spacing = 40 # spacing between different monitor_signals

        self.ruler_height = 1.3 * self.character_height

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def render(self, text, cycles=None):
        """Handle all drawing operations."""
        # Update cycles_completed if required
        if cycles is not None:
            self.cycles_completed = cycles

        # Adjust zoom bounds depending on number of monitors
        # num_monitors = len(self.monitors.monitors_dictionary)
        # self.zoom_lower = min((self.margin_bottom + num_monitors * self.monitor_spacing)/50 * 0.2, self.zoom_upper)

        size = self.GetClientSize()
        self.bound_panning()
        self.bound_zooming()

        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Draw specified text at position (10, 10)
        self.render_text(text, 10, 10)

        self.render_grid()
        # Render signal traces
        # TODO uncomment bottom line
        # self.margin_left = max((self.monitors.get_margin()*self.character_width + 10)/self.zoom, 100)
        y_pos = self.margin_bottom
        for device_id, output_id in self.monitors.monitors_dictionary:
            self.render_monitor(device_id, output_id, y_pos, y_pos + self.trace_height)
            y_pos += self.monitor_spacing

        # Draw ruler components
        self.render_ruler_background()
        self.render_cycle_numbers()
        self.render_grid(render_on_ruler = True)

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        size = self.GetClientSize()
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

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
            self.Refresh()  # triggers the paint event

    def bound_panning(self):
        """Makes sure the canvas is always panned within the bounds of the
        signal traces."""
        size = self.GetClientSize()
        if self.pan_x < self.border_left:
            self.pan_x = self.border_left
        elif self.pan_x > self.border_right:
            self.pan_x = self.border_right
        if self.pan_y < self.border_bottom:
            self.pan_y = self.border_bottom
        elif self.pan_y > self.border_top:
            self.pan_y = self.border_top

    def bound_zooming(self):
        """Makes sure the zoom is bounded."""
        if self.zoom > self.zoom_upper:
            self.zoom = self.zoom_upper
        elif self.zoom < self.zoom_lower:
            self.zoom = self.zoom_lower

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

    def render_monitor(self, device_id, output_id, y_min, y_max):
        """Draw monitor name and signal trace for a particular monitor."""
        # TODO uncomment monitor_name
        monitor_name = "Device 1"
        # monitor_name = self.devices.get_signal_name(device_id, output_id)
        signal_list = self.monitors.monitors_dictionary[(device_id, output_id)]

        # Draw monitor name
        text_x_pos = self.border_left/self.zoom
        text_y_pos = (y_min + y_max)/2 - self.character_height/(2*self.zoom)
        self.render_text(monitor_name, text_x_pos, text_y_pos)

        # Draw signal trace
        x_pos = self.margin_left/self.zoom # correct for zooming
        currently_drawing = False
        GL.glColor3f(0.0, 0.0, 1.0)  # signal trace is blue
        GL.glLineWidth(1)
        for signal in signal_list:
            if signal == self.devices.BLANK:
                if currently_drawing:
                    GL.glEnd()
                    currently_drawing = False
                x_pos += self.cycle_width
            else:
                if not currently_drawing:
                    GL.glBegin(GL.GL_LINE_STRIP)
                    currently_drawing = True
                if signal == self.devices.HIGH:
                    y = y_max
                if signal == self.devices.LOW:
                    y = y_min
                if signal == self.devices.RISING:
                    y = y_max
                if signal == self.devices.FALLING:
                    y = y_min
                GL.glVertex2f(x_pos, y)
                x_pos += self.cycle_width
                GL.glVertex2f(x_pos, y)
        if currently_drawing:
            GL.glEnd()
            currently_drawing = False

    def render_line(self, start_point, end_point):
        """Renders a straight line on the canvas, with the given end points."""
        if not (isinstance(start_point, tuple) and isinstance(end_point, tuple)):
            raise TypeError("start_point and end_point arguments must be of Type tuple")
        if (len(start_point) != 2  or len(end_point) != 2):
            raise ValueError("start_point and end_point arguments must be tuples of length 2")
        GL.glColor3f(0.9, 0.9, 0.9) # light grey color
        GL.glLineWidth(1)
        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex2f(start_point[0], start_point[1])
        GL.glVertex2f(end_point[0], end_point[1])
        GL.glEnd()

    def render_cycle_numbers(self):
        """Draw a ruler of cycle numbers at the top of the visible part of the
        canvas."""
        if self.cycles_completed == 0:
            return

        canvas_size = self.GetClientSize()
        for cycle in range(self.cycles_completed):
            # count number of digits in number
            num_digits = len(str(cycle + 1))
            # print cycle number
            text_x_pos = (self.margin_left - 0.5 * num_digits * self.character_width)/self.zoom + (cycle + 0.5) * self.cycle_width
            text_y_pos = (canvas_size.height - self.pan_y - self.character_height)/self.zoom
            self.render_text(str(cycle + 1), text_x_pos, text_y_pos)

    def render_ruler_background(self):
        """Draw a background for the ruler numbers at the top of the visible
        part of the canvas.
        """
        size = self.GetClientSize()
        ruler_color = [128/255, 128/255, 128/255]
        #Make sure our transformations don't affect any other transformations in other code
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

    def render_grid(self, render_on_ruler = False):
        """Draw a grid for separating the different cycles in the traces."""
        if self.cycles_completed == 0:
            return

        canvas_size = self.GetClientSize()
        line_y_pos_end = self.border_bottom + (- self.pan_y + canvas_size.height)/self.zoom

        # render either on the ruler or on the rest of the canvas
        if render_on_ruler:
            line_y_pos_start = line_y_pos_end - self.ruler_height/self.zoom
        else:
            line_y_pos_start = self.border_bottom - self.pan_y/self.zoom

        line_x_pos = self.margin_left/self.zoom
        self.render_line((line_x_pos, line_y_pos_start),(line_x_pos, line_y_pos_end))
        for cycle in range(self.cycles_completed):
            line_x_pos = self.margin_left/self.zoom + (cycle + 1) * self.cycle_width
            self.render_line((line_x_pos, line_y_pos_start),(line_x_pos, line_y_pos_end))


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

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenu.Append(wx.ID_EXIT, "&Exit")
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        # Configure toolbar
        toolBar = self.CreateToolBar()
        openIcon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR)
        redoIcon = wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR)
        toolBar.AddTool(1001, "Tool1", openIcon)
        toolBar.AddTool(1002, "Tool2", redoIcon)
        self.SetToolBar(toolBar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, devices, monitors)
        self.cycles_completed = 5  # number of simulation cycles completed

        # Configure the widgets
        self.error_log = wx.TextCtrl(self, wx.ID_ANY, "paparia\n"*20,
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        left_sizer.Add(self.canvas, 2, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.error_log, 1, wx.EXPAND | wx.ALL, 5)

        #right_sizer.Add(self.spin, 0, wx.ALL, 5)
        right_sizer = self.make_right_sizer()

        main_sizer.Add(left_sizer, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(right_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizeHints(1200, 800)
        self.SetSizer(main_sizer)

    #Sizer helper functions
    def make_right_sizer(self):
        """Helper function that creates the right sizer"""
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the notebook to hold tabs
        nb = wx.Notebook(self)

        # Create the tabs
        tab1 = CustomTab(nb)
        tab2 = CustomTab(nb)

        nb.AddPage(tab1, "Switches")
        nb.AddPage(tab2, "Monitors")

        right_sizer.Add(nb, 1, wx.EXPAND | wx.ALL, 5)
        return right_sizer

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nCreated by Mojisola Agboola\n2017",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)
        if Id == 1002: # run button
            text = "Run button pressed."
            self.canvas.render(text, self.cycles_completed)

    def on_spin(self, event):
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join(["New spin control value: ", str(spin_value)])
        self.canvas.render(text)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        text = "Run button pressed."
        self.canvas.render(text)

    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join(["New text box value: ", text_box_value])
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

    TBD
    """

    def __init__(self, parent):
        """Attach parent to panel and create the list control widget."""
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        #Constants
        self.LIST_WIDTH = 165
        self.LIST_STATUS_WIDTH = 90

        self.gui = parent.GetParent()

        mon_list = wx.CheckListBox(self, size = (self.LIST_WIDTH, -1), style = wx.LB_SINGLE);
        #mon_list.AppendColumn("Name")
        #mon_list.AppendColumn("Status")
        for i in range(30):
            mon_list.Append(["You" + str(i)])
        #mon_list.SetColumnWidth(0, self.LIST_WIDTH - self.LIST_STATUS_WIDTH)
        #mon_list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        sizer.Add(mon_list, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        #print("Run button pressed.")
