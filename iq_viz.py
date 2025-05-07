import argparse
import numpy as np
from src.dsp import reshape_frame
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import sys
import pandas as pd
import json


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
        self.scatter.setData(pos=pos)


n_receivers = 4
samples_per_chirp = 128
n_chirps_per_frame = 255

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record data from the DCA1000")
    parser.add_argument("--data", type=str, required=True, help="Path to the .csv file")

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    iq_plot = IQPlot()
    iq_plot.resize(600, 600)
    iq_plot.show()

    # Open up the CSV
    df = pd.read_csv(args.data, chunksize=1)

    for chunk in df:
        data_json = json.loads(chunk["data"].iloc[0])

        data = np.array(data_json, dtype=np.int16)

        reshaped_frame = reshape_frame(
            data,
            n_chirps_per_frame,
            samples_per_chirp,
            n_receivers,
        )

        iq = reshaped_frame.reshape(-1)  # Flatten the array
        iq_plot.update(iq)  # Update the plot with the flattened data
        app.processEvents()