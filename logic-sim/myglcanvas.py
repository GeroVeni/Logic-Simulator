"""Display the monitoring signals on a wx.glcanvas.

Used in the Logic Simulator project to display the monitoring signals of the
simulated circuit, using OpenGL.

Classes:
--------
MyGLCanvasWrapper - toggles between 2D and 3D drawing mode.
MyGLCanvas_2D - handles all 2D canvas drawing operations.
MyGLCanvas_3D - handles all 3D canvas drawing operations.
"""
import wx
import wx.glcanvas as wxcanvas
import numpy as np
import math
from OpenGL import GL, GLU, GLUT
from colors import ColorScheme


class MyGLCanvasWrapper(wxcanvas.GLCanvas):
    """Handle toggling between 2D and 3D drawing mode.

    This class manages drawing onto the canvas and toggles between 2D and  3D
    drawing mode. It acts as an interface of the Gui class with the
    MyGLCanvas_2D and MyGLCanvas_3D classes.

    Parameters
    ----------
    parent: parent window.

    Public methods
    --------------
    toggle_drawing_mode(self): Toggles between 2D and 3D drawing mode.

    render(self, text): Calls the appropriate method for 2D or 3D mode, that
                        handles all drawing operations.

    recenter(self, pan_to_end): Calls the appropriate method for 2D or 3D mode,
                        that restores canvas to its default pan position and
                        zoom state.

    restore_state(self): Calls the appropriate method for 2D or 3D mode, that
                         restores the state of the canvas when a new circuit
                         definition file is loaded using the gui, or when the
                         number of monitors is changed in the gui.
    """

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

        # set up drawing modes
        self.draw_2D = MyGLCanvas_2D(self)  # default mode
        self.draw_3D = MyGLCanvas_3D(self)

        # start in 2D mode
        self.current_mode = self.draw_2D

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.current_mode.on_paint)
        self.Bind(wx.EVT_SIZE, self.current_mode.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.current_mode.on_mouse)

    def toggle_drawing_mode(self):
        """Toggles between 2D and 3D drawing mode."""
        # Unbind events from the canvas
        self.Unbind(wx.EVT_PAINT)
        self.Unbind(wx.EVT_SIZE)
        self.Unbind(wx.EVT_MOUSE_EVENTS)

        # Togge drawing mode
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

        # Initialise variables for zooming
        self.current_mode.zoom = 1

        self.recenter()

    def render(self, text):
        """Interface method for the render() method in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.render(text)

    def recenter(self, pan_to_end=False):
        """Interface method for the recenter() method in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.recenter(pan_to_end)

    def restore_state(self):
        """Interface method for the restore_state() method in MyGLCanvas_2D and
        MyGLCanvas_3D."""
        self.current_mode.restore_state()


class MyGLCanvas_2D():
    """Handle all 2D drawing operations.

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
        self._update_zoom_lower_bound()
        self.zoom = self.zoom_lower

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.parent.GetClientSize()
        self.parent.SetCurrent(self.parent.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(self.margin_left, 0, size.width - self.margin_left,
                      size.height)
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
        self._update_zoom_lower_bound()
        self._bound_zooming()
        self._update_borders()
        self._bound_panning()

        self.parent.SetCurrent(self.parent.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Enable line below only when debugging the canvas
        # self.render_text(text, 10, 10)

        # Set the left margin for the canvas
        if self.parent.parent.monitors.get_margin() is not None:
            self.margin_left = (
                self.parent.parent.monitors.get_margin() *
                self.character_width +
                10)

        size = self.parent.GetClientSize()

        # Render canvas canvas components
        self._render_grid(size)

        # Render signal traces starting from the top of the canvas
        num_monitors = len(self.parent.parent.monitors.monitors_dictionary)
        if num_monitors > 0:
            y_pos = self.border_bottom + self.margin_bottom + \
                (num_monitors - 1) * self.monitor_spacing
            for device_id, output_id in self.parent.parent.monitors.\
                    monitors_dictionary:
                self._render_monitor(
                    device_id,
                    output_id,
                    y_pos,
                    y_pos +
                    self.trace_height, size)
                y_pos -= self.monitor_spacing

        # Render ruler components
        # Render ruler background across the whole width of the canvas
        GL.glViewport(0, 0, size.width, size.height)
        self._render_ruler_background(size)
        GL.glViewport(self.margin_left, 0, size.width - self.margin_left,
                      size.height)
        self._render_cycle_numbers(size)
        self._render_grid(size, render_only_on_ruler=True)

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
        self._update_zoom_lower_bound()
        self.zoom = self.zoom_lower
        self._update_borders()
        self._bound_panning()

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

    def _bound_panning(self):
        """Bound pan_x, pan_y variables with respect to the signal traces."""
        size = self.parent.GetClientSize()
        # Calculate allowable pan values
        allowable_pan_right = -self.border_right * self.zoom + size.width
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

        # if true, some monitors are hidden (y dir)
        if allowable_pan_top < 0:
            if self.pan_y < allowable_pan_top:
                self.pan_y = allowable_pan_top
        else:
            if self.pan_y < 0:
                self.pan_y = 0

        if self.pan_y > allowable_pan_bottom:
            self.pan_y = allowable_pan_bottom

    def _bound_zooming(self):
        """Bound zoom."""
        if self.zoom > self.zoom_upper:
            self.zoom = self.zoom_upper
        elif self.zoom < self.zoom_lower:
            self.zoom = self.zoom_lower

    def _update_zoom_lower_bound(self):
        """Adjust zoom lower bound when the canvas is resized or the number of
        monitors changes."""
        size = self.parent.GetClientSize()

        # Allow a max number of 7 monitors to be displayed at once
        num_monitors = min(7, len(self.parent.parent.monitors.
                                  monitors_dictionary))

        # Adjust zoom bounds depending on number of monitors
        visible_objects_height = self.margin_bottom + \
            num_monitors * self.monitor_spacing + self.ruler_height
        self.zoom_lower = min(
            size.height /
            (visible_objects_height),
            self.zoom_upper)

    def _update_borders(self):
        """Update the borders of the canvas depending on the number of monitors
        and the number of cycles to be simulated."""
        num_monitors = len(self.parent.parent.monitors.monitors_dictionary)
        # border_top depends only on the number of monitors
        self.border_top = self.border_bottom + self.margin_bottom + \
            num_monitors * self.monitor_spacing + self.ruler_height / self.zoom
        # border_right depends only on the number of cycles to be simulated
        self.border_right = self.parent.parent.cycles_completed * \
            self.cycle_width

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

    def _render_monitor(self, device_id, output_id, y_min, y_max, size):
        """Handle monitor name and signal trace drawing for a single
        monitor."""
        monitor_name = self.parent.parent.devices.get_signal_name(
            device_id, output_id)
        signal_list = self.parent.parent.monitors.monitors_dictionary[(
            device_id, output_id)]

        # Draw monitor name
        # Render on different viewport
        GL.glViewport(0, 0, self.margin_left, size.height)
        text_x_pos = -self.pan_x / self.zoom + 4
        text_y_pos = (y_min + y_max) / 2 - \
            self.character_height / (2 * self.zoom)
        self.render_text(monitor_name, text_x_pos, text_y_pos)
        GL.glViewport(self.margin_left, 0, size.width - self.margin_left,
                      size.height)

        # Draw rectangles underneath HIGH signals for more clarlity
        x_pos = 0
        fill_color = [103 / 255, 218 / 255, 255 / 255]
        GL.glColor3fv(fill_color)
        for signal in signal_list:
            if (signal == self.parent.parent.devices.HIGH) \
                    or (signal == self.parent.parent.devices.RISING):
                self._render_rectangle((x_pos, y_min),
                                       (x_pos + self.cycle_width, y_max))
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

    def _render_line(self, start_point, end_point):
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

    def _render_rectangle(self, bottom_left_point, top_right_point):
        """Render a rectangle on the canvas, with the given end points."""
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

    def _render_cycle_numbers(self, size):
        """Handle cycle numbers drawing at the top of the canvas (ruler)."""
        if self.parent.parent.cycles_completed == 0:
            return

        for cycle in range(self.parent.parent.cycles_completed):
            # count number of digits in number
            num_digits = len(str(cycle + 1))
            # draw cycle number
            text_x_pos = - 0.5 * num_digits * self.character_width / \
                self.zoom + (cycle + 0.5) * self.cycle_width
            text_y_pos = (size.height - self.pan_y -
                          self.character_height) / self.zoom
            self.render_text(str(cycle + 1), text_x_pos, text_y_pos)

    def _render_ruler_background(self, size):
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

    def _render_grid(self, size, render_only_on_ruler=False):
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
        self._render_line((line_x_pos, line_y_pos_start),
                          (line_x_pos, line_y_pos_end))
        for cycle in range(self.parent.parent.cycles_completed):
            line_x_pos += self.cycle_width
            self._render_line((line_x_pos, line_y_pos_start),
                              (line_x_pos, line_y_pos_end))

    def recenter(self, pan_to_end=False):
        """Restore canvas to its default pan position and zoom state. If
        pan_to_end argument is true, the canvas is panned to the end of the
        signal traces."""
        self.zoom = self.zoom_lower
        self.pan_y = self.border_bottom
        if pan_to_end:  # if true pan to the end of the signal trace
            self._update_borders()
            size = self.parent.GetClientSize()
            allowable_pan_right = -self.border_right * self.zoom + size.width
            self.pan_x = allowable_pan_right
        else:
            self.pan_x = self.border_left

        self.init = False
        self.render("Recenter canvas")

    def restore_state(self):
        """Restore the state of the canvas when a new circuit definition file
        is loaded using the gui, or when the number of monitors is changed in
        the gui.

        restore_state() should be called whenever the gui method
        on_open() and set_monitor() is called."""
        self.init = False
        self._update_zoom_lower_bound()
        self.zoom = self.zoom_lower
        self.render("")


class MyGLCanvas_3D():
    """Handle all 3D drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos, z_pos): Handles text drawing
                                                  operations.

    restore_state(self): Restore the state of the canvas when a new circuit
                         definition file is loaded using the gui, or when the
                         number of monitors is changed in the gui.

    recenter(self, pan_to_end = False): Restore canvas to its default pan
                                position, zoom state and orientation.
    """

    def __init__(self, parent):
        """Initialise canvas properties and useful variables."""
        # keep reference to parent
        self.parent = parent
        self.color_scheme = ColorScheme.get_default()

        self.init = False

        # Constants for OpenGL materials and lights
        self.mat_diffuse = [0.0, 0.0, 0.0, 1.0]
        self.mat_no_specular = [0.0, 0.0, 0.0, 0.0]
        self.mat_no_shininess = [0.0]
        self.mat_specular = [0.5, 0.5, 0.5, 1.0]
        self.mat_shininess = [50.0]
        self.top_right = [1.0, 1.0, 1.0, 0.0]
        self.straight_on = [0.0, 0.0, 1.0, 0.0]
        self.no_ambient = [0.0, 0.0, 0.0, 1.0]
        self.dim_diffuse = [0.5, 0.5, 0.5, 1.0]
        self.bright_diffuse = [1.0, 1.0, 1.0, 1.0]
        self.med_diffuse = [0.75, 0.75, 0.75, 1.0]
        self.full_specular = [0.5, 0.5, 0.5, 1.0]
        self.no_specular = [0.0, 0.0, 0.0, 1.0]

        # 3D rendering settings
        self.cycle_depth = 20  # equivalent to cycle_width for 2D class
        self.trace_height = 10
        self.trace_width = 10
        self.monitor_spacing = self.trace_width + 10  # from centerline
        self.margin = 10

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise the scene rotation matrix
        self.scene_rotate = np.identity(4, 'f')

        # Initialise variables for zooming
        self.zoom = 1

        # Offset between viewpoint and origin of the scene
        self.depth_offset = 1000

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.parent.GetClientSize()
        self.parent.SetCurrent(self.parent.context)

        GL.glViewport(0, 0, size.width, size.height)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(45, size.width / size.height, 10, 10000)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()  # lights positioned relative to the viewer
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, self.med_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, self.top_right)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, self.dim_diffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, self.straight_on)

        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, self.mat_specular)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, self.mat_shininess)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE,
                        self.mat_diffuse)
        GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glCullFace(GL.GL_BACK)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_LIGHT1)
        GL.glEnable(GL.GL_NORMALIZE)

        # Viewing transformation - set the viewpoint back from the scene
        GL.glTranslatef(0.0, 0.0, -self.depth_offset)

        # Modelling transformation - pan, zoom and rotate
        GL.glTranslatef(self.pan_x, self.pan_y, 0.0)
        GL.glMultMatrixf(self.scene_rotate)
        GL.glScalef(self.zoom, self.zoom, self.zoom)

    def render(self, text=""):
        """Handle all drawing operations."""
        self.parent.SetCurrent(self.parent.context)
        if not self.init:
            # Configure the OpenGL rendering context
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Draw monitors' signal traces and cycle numbers
        num_monitors = len(self.parent.parent.monitors.monitors_dictionary)
        if num_monitors > 0:
            x_pos = -(num_monitors - 1) * self.monitor_spacing / 2
            self._render_cycle_numbers(x_pos - self.monitor_spacing)
            self.color_scheme.reset_colors()
            for device_id, output_id in self.parent.parent.monitors.\
                    monitors_dictionary:
                GL.glColor3fv(self.color_scheme.get_next_color())
                self._render_monitor(device_id, output_id, x_pos)
                x_pos += self.monitor_spacing

            self._render_cycle_numbers(x_pos)

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.parent.SwapBuffers()

    def _draw_cuboid(self, x_pos, z_pos, half_width, half_depth, height):
        """Draw a cuboid.

        Draw a cuboid at the specified position, with the specified
        dimensions.
        """
        GL.glBegin(GL.GL_QUADS)
        GL.glNormal3f(0, -1, 0)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)
        GL.glNormal3f(0, 1, 0)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)
        GL.glNormal3f(-1, 0, 0)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)
        GL.glNormal3f(1, 0, 0)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)
        GL.glNormal3f(0, 0, -1)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)
        GL.glNormal3f(0, 0, 1)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)
        GL.glEnd()

    def on_paint(self, event):
        """Handle the paint event."""
        self.parent.SetCurrent(self.parent.context)
        if not self.init:
            # Configure the OpenGL rendering context
            self.init_gl()
            self.init = True

        size = self.parent.GetClientSize()
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        self.parent.SetCurrent(self.parent.context)

        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()

        if event.Dragging():
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            x = event.GetX() - self.last_mouse_x
            y = event.GetY() - self.last_mouse_y
            if event.LeftIsDown():
                GL.glRotatef(math.sqrt((x * x) + (y * y)), y, x, 0)
            if event.MiddleIsDown():
                GL.glRotatef((x + y), 0, 0, 1)
            if event.RightIsDown():
                self.pan_x += x
                self.pan_y -= y
            GL.glMultMatrixf(self.scene_rotate)
            GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, self.scene_rotate)
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False

        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False

        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False

        self.parent.Refresh()  # triggers the paint event

    def render_text(self, text, x_pos, y_pos, z_pos):
        """Handle text drawing operations."""
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(x_pos, y_pos, z_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_10

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos3f(x_pos, y_pos, z_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

        GL.glEnable(GL.GL_LIGHTING)

    def _render_monitor(self, device_id, output_id, x_pos):
        """Handle monitor name and signal trace drawing for a single
        monitor."""
        monitor_name = self.parent.parent.devices.get_signal_name(
            device_id, output_id)
        signal_list = self.parent.parent.monitors.monitors_dictionary[(
            device_id, output_id)]

        # Draw signal traces
        cycles = self.parent.parent.cycles_completed
        z_pos = -0.5 * (cycles - 1) * self.cycle_depth
        for signal in signal_list:
            if signal != self.parent.parent.devices.BLANK:
                if signal == self.parent.parent.devices.HIGH:
                    height = self.trace_height
                elif signal == self.parent.parent.devices.LOW:
                    height = 0
                elif signal == self.parent.parent.devices.RISING:
                    height = self.trace_height
                elif signal == self.parent.parent.devices.FALLING:
                    height = 0
                self._draw_cuboid(x_pos, z_pos, self.trace_width / 2,
                                  self.cycle_depth / 2, height + 1)
            z_pos += self.cycle_depth

        # Draw monitor name
        GL.glColor3f(1.0, 1.0, 1.0)  # text is white
        self.render_text(monitor_name, x_pos, 0, z_pos)

    def _render_cycle_numbers(self, x_pos):
        """Handle rendering cycle numbers over the signal traces."""
        GL.glColor3f(1.0, 1.0, 1.0)  # text is white
        cycles = self.parent.parent.cycles_completed
        z_pos = -0.5 * (cycles - 1) * self.cycle_depth
        for cycle in range(1, cycles + 1):
            self.render_text(str(cycle), x_pos, self.trace_height, z_pos)
            z_pos += self.cycle_depth

    def restore_state(self):
        """Restore the state of the canvas when a new circuit definition file
        is loaded using the gui, or when the number of monitors is changed in
        the gui."""
        # This method is needed only for MyGLCanvas_2D, but is called by the
        # GLCanvasWrapper everytime a file is opened or a monitor is added.
        pass

    def recenter(self, pan_to_end=False):
        """Restore canvas to its default pan position, zoom state and
        orientation."""
        self.pan_x = 0
        self.pan_y = 0
        self.zoom = 1
        self.init = False

        # Restore initial viewing angle
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glRotatef(20, 1, 0, 0)
        GL.glRotatef(20, 0, 1, 0)
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, self.scene_rotate)

        self.render("Recenter canvas")
