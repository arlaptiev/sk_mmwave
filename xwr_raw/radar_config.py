#!/usr/bin/env python3

"""Wrapper for .lua file used to configure the radar

Also computations derived parameters from the config using get_params().

Modified from: https://github.com/ConnectedSystemsLab/xwr_raw_ros/blob/main/src/xwr_raw/radar_config.py
"""

from collections import OrderedDict
import pprint
import re


class RadarConfig(OrderedDict):

    platforms = {
        "XWR1443": "xWR14xx",
    }

    def __init__(self):
        super(RadarConfig, self).__init__()

    def __init__(self, cfg: str):
        """Initialize RadarConfig from a .lua file used in mmWaveStudio to configure the radar

        Args:
            cfg: Path to the .lua file
        """
        super(RadarConfig, self).__init__()

        self.from_cfg(cfg)

    def from_cfg(self, cfg: str):
        """
        Parses the .lua file and populates the RadarConfig object with the parameters
        """

        with open(cfg, "r") as f:
            for line in f:
                # See if it's a variable assignment
                match = re.match(r"(\w+)\s*=\s*([^\n]*?)(?=\s*--|$)", line)
                if match:
                    key, value = match.groups()
                    self[key] = self._extract_value(value)
                    continue

                # See if it's a function call
                match = re.match(r"([\w\.]+)\((.+?)\)", line)

                if match:
                    f, args = match.groups()
                    args = args.strip()

                    self[f] = args.split(",")

                    continue

    def _extract_value(self, value):
        """
        Extracts the value from a string, removing any quotes or extra characters
        """
        if isinstance(value, str):
            value = value.strip().strip('"').strip("'")
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
        return value

    def get_params(self):
        """
        Computes derived parameters from the config

        Equations copied from the .lua file
        """

        arg_platform = self["ar1.SelectChipVersion"][0].strip('"').strip("'")

        platform = self.platforms.get(arg_platform, "Unknown")

        # TODO: Only portions of this value actually matter see LUA_API.md
        adc_output_fmt = int(
            self["ar1.ChanNAdcConfig"][8]
        )  # 0 - real, 1 - complex 1x, 2- complex 2x

        # Calculate number of chirps
        start_chirp = int(self["START_CHIRP_TX"])
        end_chirp = int(self["END_CHIRP_TX"])
        chirp_loops = int(self["CHIRP_LOOPS"])
        n_chirps = (end_chirp - start_chirp + 1) * chirp_loops

        # Determine the number of RX and TX antennas
        rx = [int(x) for x in self["ar1.ChanNAdcConfig"][3:7]]  # RX1, RX2, RX3, RX4
        n_rx = sum(rx)

        tx = [int(x) for x in self["ar1.ChanNAdcConfig"][0:3]]  # TX1, TX2, TX3
        n_tx = sum(tx)

        # Calculate the number of samples
        n_samples = self["ADC_SAMPLES"]

        # Calculate the frame size
        frame_size = (
            n_samples * n_rx * n_chirps * 2 * (2 if adc_output_fmt > 0 else 1)
        )  # For each chrip we collect n_samples for each rx antenna where each sample is 2 bytes and we collect I and Q if complex

        # Calculate the frame time
        frame_time = self["PERIODICITY"]  # in ms

        # Calculate the chirp time
        chirp_time = self["IDLE_TIME"] + self["RAMP_END_TIME"]  # In us

        # Calculate the chirp slope (convert from MHz/us to Hz/s)
        chirp_slope = self["FREQ_SLOPE"] * 1e12

        # Calculate the sample rate
        sample_rate = self["SAMPLE_RATE"] * 1e3  # ksps to sps

        # Calculate the sweep time
        t_sweep = self["ADC_SAMPLES"] / sample_rate  # in seconds

        # Calculate the chirp sampling rate
        chrip_sampling_rate = chirp_loops * (1 / (frame_time * 1e-3))  # Hz

        # Calculate the maximum velocity
        operating_freq = self["START_FREQ"] * 1e9  # GHz to Hz
        wavelength = 3e8 / operating_freq  # lambda = c / f
        velocity_max = (wavelength) / (4 * chirp_time * 1e-6)  # m/s
        velocity_res = velocity_max / n_chirps  # m/s

        # Calculate the maximum range
        range_max = (sample_rate * 3e8) / (2 * chirp_slope)  # m
        range_res = range_max / n_samples  # m

        return OrderedDict(
            [
                ("platform", platform),
                ("adc_output_fmt", adc_output_fmt),
                ("n_chirps", n_chirps),
                ("rx", rx),
                ("n_rx", n_rx),
                ("tx", tx),
                ("n_tx", n_tx),
                ("n_samples", n_samples),
                ("frame_size", frame_size),
                ("frame_time", frame_time),
                ("chirp_time", chirp_time),
                ("chirp_slope", chirp_slope),
                ("sample_rate", sample_rate),
                ("chirp_sampling_rate", chrip_sampling_rate),
                ("velocity_max", velocity_max),
                ("velocity_res", velocity_res),
                ("range_max", range_max),
                ("range_res", range_res),
                ("t_sweep", t_sweep),
            ]
        )

    def __str__(self):
        """
        Returns a nicely formatted string with all the radar configuration parameters
        and appropriate units.
        """
        try:
            params = self.get_params()
        except Exception as e:
            return f"Error generating config parameters: {e}"

        # Define units for known parameters
        units = {
            "frame_time": "ms",
            "chirp_time": "µs",
            "chirp_slope": "Hz/s",
            "sample_rate": "samples/s",
            "chirp_sampling_rate": "Hz",
            "velocity_max": "m/s",
            "velocity_res": "m/s",
            "range_max": "m",
            "range_res": "m",
            "t_sweep": "s",
            "frame_size": "bytes",
        }

        # Format each parameter with units if known
        lines = []
        for key, value in params.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            elif isinstance(value, float):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)

            unit = units.get(key, "")
            lines.append(f"{key:25}: {value_str} {unit}".rstrip())

        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python radar_config.py <path_to_lua_file>")
        sys.exit(1)

    cfg = RadarConfig(sys.argv[1])
    pprint.pprint(cfg.get_params())
