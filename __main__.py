import numpy as np
from matplotlib import pyplot as plt

from axes_sequence import AxesSequence

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
axes.show(block=True)
