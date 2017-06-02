from itertools import product
from typing import Iterable

import numpy as np
from PyQt5 import QtCore
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.gridspec import GridSpec
from matplotlib.pyplot import Axes


class AxesGrid(Iterable):
    def __init__(self, fig, shape, initialize_grid, title=None, title_kwargs=None, gridspec_kwargs=None):
        # Settings
        self._simple = initialize_grid
        self._fig = fig
        self.shape = shape
        self._axes = []

        # Title matter
        self._title_str = title
        self._title_kwargs = title_kwargs if title_kwargs is not None else dict()
        self._title = None

        # Grid
        gridspec_kwargs = gridspec_kwargs if gridspec_kwargs is not None else dict()
        self._gs = GridSpec(shape[0], shape[1], **gridspec_kwargs)

        # Initialization
        if initialize_grid:
            for row, col in product(range(shape[0]), range(shape[1])):
                ax = self._add_slice_to_grid((row, col))
                ax.set_visible(False)

    def __getitem__(self, item):
        # Check if user wants an initializes axis
        if isinstance(item, int):
            return self.axes[item]

        # Slicing enables accessing gridspec
        else:
            if self._simple:
                raise ValueError("Attempting to access grid (advanced feature) of AxesGrid that has "
                                 "been simply initialized.")
            ax = self._add_slice_to_grid(item)
            ax.set_visible(False)
            return ax

    def _add_slice_to_grid(self, item):
        ax = self._fig.add_subplot(self._gs[item])  # type: Axes
        self._axes.append(ax)
        return ax

    def set_visible(self, visible=True):
        for ax in self.axes:
            ax.set_visible(visible)

        # Overall title
        if visible:
            if self._title_str is not None:
                self._title = self._fig.suptitle(self._title_str, **self._title_kwargs)
                self._title.set_visible(True)
        else:
            if self._title is not None:
                self._title.set_visible(False)

    @property
    def axes(self):
        return self._axes

    @property
    def top_right_axis(self):
        # Get top-right corners of all axes in frame
        corners = [(idx, *ax.get_position().max) for idx, ax in enumerate(self._axes)]

        # Find top of axes
        top = max([corner[2] for corner in corners])

        # Find all axes at the top
        potential_corners = [corner for corner in corners if np.isclose(corner[2], top)]

        # Find right-most position of axes
        right = max([corner[1] for corner in potential_corners])

        # Find top-right corner
        top_right_corner = [corner for corner in corners if np.isclose(corner[1], right)][0]

        # Get top-right axis
        top_right_axis = self._axes[top_right_corner[0]]

        return top_right_axis

    def __iter__(self):
        return (item for item in self.axes)

    def __str__(self):
        return f"{type(self).__name__}{self.shape}"

    def __repr__(self):
        return str(self)


class AxesSequence(object):
    def __init__(self, page_number_on_top=True, include_frame_numbers=True):
        self.page_number_on_top = page_number_on_top
        self.include_frame_numbers = include_frame_numbers

        # Figure and canvas
        self._fig = plt.figure()
        self._canvas = self._fig.canvas
        self._canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self._canvas.setFocus()
        self._canvas.mpl_connect('key_press_event', self._on_keypress)

        # List of axes, index and number of axes
        self._frames = []
        self._plot_idx = 0  # type: int
        self._n_plots = 0  # Last created axes index

        # Add-ons for writing extras on each plot
        self._addons = []

    def __iter__(self):
        """
        For creating many plots in a zip().
        :return:
        """
        while True:
            yield self._new()

    def __next__(self):
        return self._new()

    def _new(self):
        """
        Create new plot.
        :rtype: plt.Axes
        """
        frame = self._fig.add_axes([0.15, 0.1, 0.8, 0.8], visible=False, label=self._n_plots)
        self._n_plots += 1
        self._frames.append(frame)
        return frame

    def new_axis_subplots(self, shape, title=None, title_kwargs=None, gridspec_kwargs=None):
        """
        Creates an object with multiple axes in it, arrange in a simple grid.
        The returned object is an iterable where you can loop over the subplots.
        :param tuple shape: A tuple with the number of rows (first value) and columns (second value) in the grid.
        :param str title: Overall title above grid.
        :param dict title_kwargs: Settings passed on to title (matplotlib-text object).
        :param dict gridspec_kwargs: Settings passed on to GridSpec.
        :return: AxesGrid
        """
        frame = AxesGrid(self._fig, shape, initialize_grid=True, title=title,
                         title_kwargs=title_kwargs, gridspec_kwargs=gridspec_kwargs)
        self._n_plots += 1
        self._frames.append(frame)
        return frame

    def new_axis_grid(self, shape, title=None, title_kwargs=None, gridspec_kwargs=None):
        """
        Creates an object with multiple axes in it, arrange in a gridspec.
        This allows for creating advanced subplot-arrangements, such as one subplot taking up more than one grid-cell.
        :param tuple shape: A tuple with the number of rows (first value) and columns (second value) in the grid.
        :param str title: Overall title above grid.
        :param dict title_kwargs: Settings passed on to title (matplotlib-text object).
        :param dict gridspec_kwargs: Settings passed on to GridSpec.
        :return: AxesGrid
        """
        frame = AxesGrid(self._fig, shape, initialize_grid=False, title=title,
                         title_kwargs=title_kwargs, gridspec_kwargs=gridspec_kwargs)
        self._n_plots += 1
        self._frames.append(frame)
        return frame

    def _on_keypress(self, event):
        key = event.key.lower()

        # Next plot
        if key in ["right", "pagedown", "down"]:
            if self._plot_idx < self._n_plots - 1:
                self.switch_to_plot(self._plot_idx + 1)

        # Previous plot
        elif key in ["left", "pageup", "up"]:
            if self._plot_idx > 0:
                self.switch_to_plot(self._plot_idx - 1)

        # Last plot
        elif key == "end":
            self.switch_to_plot(self._n_plots - 1)

        # First plot
        elif key == "home":
            self.switch_to_plot(0)

        # Clear add-ons
        elif key == "delete":
            if self.include_frame_numbers:
                self.include_frame_numbers = False
                self._clear_addons()
            else:
                self.include_frame_numbers = True
                self._make_addons()

        # Irrelevant key
        else:
            return

        # Draw canvas
        self._canvas.draw()

    def _make_addons(self):
        """
        Add additional information to plot, which can be removed afterwards (ex. plot number).
        """
        # Get frame and index
        idx = self._plot_idx
        frame = self._frames[idx]  # type: plt.Axes

        if self.include_frame_numbers:
            if isinstance(frame, AxesGrid):
                frame = frame.top_right_axis

            if self.page_number_on_top:
                text = frame.text(1, 1, f"Axis {idx+1} / {self._n_plots}", transform=frame.transAxes,
                                  ha="right", va="bottom", fontproperties=FontProperties(family='monospace'))
            else:
                text = frame.text(1, -0.001, f"Axis {idx+1} / {self._n_plots}", transform=frame.transAxes,
                                  ha="right", va="top", fontproperties=FontProperties(family='monospace'))
            self._addons.append(text)

    def _clear_addons(self):
        """
        Remove add-ons from plot.
        """
        while self._addons:
            addon = self._addons.pop()
            addon.remove()

    def _set_invisible(self):
        """
        Make axis go away and clear all addons.
        """
        self._clear_addons()

        # Get frame and index
        idx = self._plot_idx
        frame = self._frames[idx]  # type: plt.Axes

        frame.set_visible(False)

    def _set_visible(self):
        """
        Make axis appear and create addons.
        """
        # Get frame and index
        idx = self._plot_idx
        frame = self._frames[idx]  # type: plt.Axes

        # Check type of frame
        frame.set_visible(True)

        # Add ons
        self._make_addons()

    def switch_to_plot(self, idx):
        """
        Switch to specified plot.
        :param int idx:
        """
        if 0 <= idx < self._n_plots:
            self._set_invisible()
            self._plot_idx = idx
            self._set_visible()
        else:
            raise IndexError(f"index for axis is incorrect: {idx} ({self._n_plots} axes available).")

    def show(self):
        """
        Show yourself!
        """
        for frame_idx in range(self._n_plots):
            self._set_invisible()
        self._set_visible()
        plt.show()


if __name__ == "__main__":
    plt.close("all")

    # Make axes-sequence
    axes = AxesSequence()

    # Add a couple of plots
    for i, frame in zip(range(3), axes):
        x = np.linspace(0, 10, 100)
        frame.plot(x, np.sin(i * x))
        frame.set_title('Line {}'.format(i + 1))

    # Add another set of plots
    for i, frame in zip(range(2), axes):
        frame.imshow(np.random.random((10, 10)))
        frame.set_title('Image {}'.format(i + 1))

    # Add a single plot
    frame = next(axes)
    frame.plot([1, 4, 2, 3], [1, 2, 3, 4])
    frame.set_title("Lonely plot")

    # Add a grid-frame (advanced interface)
    frame = axes.new_axis_grid(shape=(2, 2), title="Advanced interface grid-plot.")
    ax = frame[0, 0]
    ax.plot([1, 2, 3, 4], [4, 1, 3, 2])
    ax = frame[0, 1]
    ax.plot([1, 2, 3, 4], [4, 1, 3, 2])
    ax = frame[1, :]
    ax.plot([1, 2, 3, 4], [4, 1, 3, 2])

    # Add a subplot-frame (simple interface)
    frame = axes.new_axis_subplots(shape=(3, 2), title="Simple interface grid-plot.",
                                   gridspec_kwargs=dict(wspace=0.15, hspace=0.35))
    for idx, ax in enumerate(frame):  # type: int, Axes
        x = list(range(10))
        y = [x_val ** idx for x_val in x]
        ax.plot(x, y)
        ax.set_title(str(idx))

    # Show axes-sequence figure
    axes.show()
