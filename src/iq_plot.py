import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import numpy as np


class IQPlot(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live IQ Plot")
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.scatter = pg.ScatterPlotItem(
            size=2, pen=None, brush=pg.mkBrush(0, 255, 255, 150)
        )
        self.plot_widget.addItem(self.scatter)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setLabel("bottom", "In-phase (I)")
        self.plot_widget.setLabel("left", "Quadrature (Q)")

    def update(self, iq_data: np.ndarray):
        """Expects iq_data to be a 1D complex numpy array."""
        if iq_data.size == 0:
            return
        pos = np.column_stack((iq_data.real, iq_data.imag))
        self.scatter.clear()
        self.scatter.setData(pos=pos)


class VibrationIntensityPlot(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vibration Intensity Plot")
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.line = pg.PlotDataItem(
            pen=pg.mkPen(color=(0, 255, 255), width=2), symbol=None
        )
        self.plot_widget.addItem(self.line)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setLabel("bottom", "Frequency (Hz)")
        self.plot_widget.setLabel("left", "Intensity")

    def update(self, points: list[tuple[float, float]]):
        if not points:
            return
        self.line.setData(*zip(*points))


class VibrationIntensityHeatmap(QtWidgets.QMainWindow):
    def __init__(self, start_freq: float, range_res: float):
        super().__init__()

        self.start_freq = start_freq
        self.range_res = range_res

        self.setWindowTitle("Vibration Intensity Heatmap")

        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)
        self.plot_widget.setLabel("bottom", "Frequency (Hz)")
        self.plot_widget.setLabel("left", "Time Bins")
        self.plot_widget.setAspectLocked(False)

        # Optional: color map
        cbi = pg.ColorBarItem(colorMap="CET-L3")
        plot_item = self.plot_widget.getPlotItem()
        cbi.setImageItem(self.img_item, insert_in=plot_item)

    def update(self, data: np.ndarray):
        if data.ndim != 2:
            raise ValueError("Expected 2D array (n_bins, n_freqs)")

        n_freqs, n_freq_bins = data.shape

        self.plot_widget.setXRange(self.start_freq, self.start_freq + n_freqs)
        self.plot_widget.setYRange(0, n_freq_bins * self.range_res)

        self.img_item.setImage(data, levels=(0, 4))

        image_rect = QtCore.QRectF(
            self.start_freq,
            0,
            n_freqs,
            n_freq_bins * self.range_res,
        )
        self.img_item.setRect(image_rect)