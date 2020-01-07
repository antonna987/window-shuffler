#!/usr/bin/env python3
import os
import subprocess
import gi
gi.require_version("Wnck", "3.0")
from gi.repository import Wnck
from gi.repository import Gdk


"""
WindowShuffler
Author: Jacob Vlijm
Copyright © 2017-2018 Ubuntu Budgie Developers
Website=https://ubuntubudgie.org
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or any later version. This
program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details. You
should have received a copy of the GNU General Public License along with this
program.  If not, see <https://www.gnu.org/licenses/>.
"""


# paths
userdata = os.path.join(
    os.environ["HOME"], ".config/budgie-extras/windowshuffler",
)


try:
    os.makedirs(userdata)
except FileExistsError:
    pass


matr_file = os.path.join(userdata, "matrix")
app_path = os.path.dirname(os.path.abspath(__file__))
shortcuts = os.path.join(app_path, "shortcuts")
firstrun = os.path.join(userdata, "firstrun")
recorded_layout = os.path.join(userdata, "recorded")


def get(cmd):
    try:
        return subprocess.check_output(cmd).decode("utf-8".strip())
    except subprocess.CalledProcessError:
        pass


def check_windowtype(window):
    try:
        return "WNCK_WINDOW_NORMAL" in str(
            window.get_window_type()
        )
    except AttributeError:
        pass


def get_activities_bar_height():
    xprop_data = get(["xprop", "-root", "_NET_WORKAREA"])
    try:
        vals = xprop_data.split("=")[1].strip().split(", ")
        activities_bar_height = int(vals[1])
        return activities_bar_height
    except IndexError:
        return 0


def calc_playfield(win_geodata):
    wins = win_geodata["windows"]
    offset = win_geodata["offset"]
    wa = win_geodata["wa"]
    return [
        [offset[0] + wa[0], offset[1] + wa[1]],
        [wa[2], wa[3] - get_activities_bar_height()],
    ]


def get_yshift(window):
    """
    windows with property NET_FRAME_EXTENTS are not positioned correctly.
    we can fix that by looking up the top- extent value, add it to the
    targeted y- position.
    """
    wid = window.get_xid()
    xprop_data = get(["xprop", "-id", str(wid)])
    try:
        check = [
            l.split("=")[1].strip().split(", ")
            for l in xprop_data.splitlines()
            if "_NET_FRAME_EXTENTS(CARDINAL)" in l
        ][0]
        y_shift = - int(check[2])
    except IndexError:
        y_shift = 0
    return y_shift + get_activities_bar_height()


def get_window(win_title):
    # see if window exists
    return get(["xdotool", "search", win_title])


def save_grid(x, y):
    open(matr_file, "wt").write(str(x) + " " + str(y))


def get_initialgrid():
    try:
        return [
            int(n) for n in open(matr_file).read().strip().split()
        ]
    except FileNotFoundError:
        return [2, 2]


def windowtarget(span, cols, rows, playfield, yoffset=0, overrule=None):
    # calculates the targeted position and size of a window
    colwidth = int(playfield[1][0] / cols)
    rowheight = int(playfield[1][1] / rows)
    window_width = (span[1][0] + 1 - span[0][0]) * colwidth
    window_height = (span[1][1] + 1 - span[0][1]) * rowheight
    originx = (span[0][0] * colwidth) + playfield[0][0]
    originy = (span[0][1] * rowheight) + playfield[0][1] + yoffset

    # get scale factor
    display = Gdk.Display.get_default()
    seat = display.get_default_seat()
    device = seat.get_pointer()
    (screen, x, y) = device.get_position()
    monitor = display.get_monitor_at_point(x, y)
    scale_factor = monitor.get_scale_factor()

    return [
        originx * scale_factor,
        originy * scale_factor,
        window_width * scale_factor,
        window_height * scale_factor
    ]


def shuffle(win, x, y, w, h):
    win.unmaximize()
    g = Wnck.WindowGravity.NORTHWEST
    flags = Wnck.WindowMoveResizeMask.X | \
        Wnck.WindowMoveResizeMask.Y | \
        Wnck.WindowMoveResizeMask.WIDTH | \
        Wnck.WindowMoveResizeMask.HEIGHT
    win.set_geometry(g, flags, x, y, w, h)
