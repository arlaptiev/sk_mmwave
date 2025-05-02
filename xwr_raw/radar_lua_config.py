"""Wrapper for .lua file used to configure radar EVM.

WARNING! This is not rigorously tested. Use at your own risk.

Also computes derived parameters from the config using get_params().
"""

from collections import OrderedDict
import re


class LuaRadarConfig(OrderedDict):
    """
    WARNING! This is not rigorously tested. Use at your own risk.

    Extracts user-defined variables and function calls with arguments from a Lua mmWave configuration script.
    Replaces any variable references in function arguments with their resolved values.
    """

    def __init__(self, lua_lines):
        super().__init__()
        self.variables = OrderedDict()
        self.functions = OrderedDict()
        self.from_lua(lua_lines)

    def from_lua(self, lines):
        for line in lines:
            line = line.split('--')[0].strip()
            if not line:
                continue

            # Match and store variable definitions
            var_match = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$', line)
            if var_match:
                name, value = var_match.groups()
                value = self._parse_value(value.strip())
                self.variables[name] = value
                continue

            # Match function calls like ar1.SomeFunc(...)
            func_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', line)
            if func_match:
                obj, func_name, args = func_match.groups()
                full_func_name = f"{obj}.{func_name}"
                args_list = self._parse_args(args)
                if full_func_name not in self.functions:
                    self.functions[full_func_name] = []
                self.functions[full_func_name].append(args_list)

    def _parse_value(self, val):
        val = val.strip()
        if val in self.variables:
            return self.variables[val]
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except ValueError:
            return val.strip('"').strip("'")

    def _parse_args(self, args_str):
        if not args_str:
            return []
        args = [a.strip() for a in args_str.split(',')]
        parsed_args = []
        for arg in args:
            # Replace with value if it's a known variable
            parsed_args.append(self._parse_value(arg))
        return parsed_args

    def get_variables(self):
        return self.variables

    def get_functions(self):
        return self.functions
    
    def get_params(self):
        params = OrderedDict()

        vars = self.get_variables()
        funcs = self.get_functions()

        # Unambiguous
        params['sdk'] = None  # TODO: Not specified in Lua script
        params['platform'] =  funcs.get("ar1.SelectChipVersion", [[None]])[-1][0] if 'ar1.SelectChipVersion' in funcs else None

        lua2cfg_platform = {                                        # map .lua platform to .cfg platform
            'XWR1443': 'xWR18xx',
            None: None,
        }
        params['platform'] = lua2cfg_platform[params['platform']]

        params['adc_output_fmt'] = funcs.get("ar1.DataPathConfig", [[None]])[0][1] if "ar1.DataPathConfig" in funcs else None
        params['range_bias'] = None     # TODO
        params['rx_phase_bias'] = None  # TODO

        # Calculated values
        try:
            start_chirp = vars["START_CHIRP_TX"]
            end_chirp = vars["END_CHIRP_TX"]
            chirp_loops = vars["CHIRP_LOOPS"]
            n_chirps = (end_chirp - start_chirp + 1) * chirp_loops
            params['n_chirps'] = n_chirps
        except KeyError:
            params['n_chirps'] = None  # TODO

        # RX config from ChanNAdcConfig
        try:
            rx_cfg = funcs.get("ar1.ChanNAdcConfig", [[None]])[0]
            rx_bits = rx_cfg[3:7]  # These correspond to Rx0 - Rx3 enable flags
            rx = [int(x) for x in rx_bits]
            params['rx'] = rx
            params['n_rx'] = sum(rx)
        except (KeyError, IndexError, TypeError):
            params['rx'] = None  # TODO
            params['n_rx'] = None  # TODO

        # TX count
        try:
            tx_count = vars['NUM_TX']
            params['n_tx'] = tx_count
            # TX config not explicitly set as bitmask, so can't determine bit layout
            params['tx'] = None  # TODO
        except KeyError:
            params['n_tx'] = None  # TODO
            params['tx'] = None  # TODO

        # Direct mappings
        params['n_samples'] = vars.get("ADC_SAMPLES", None)
        params['frame_time'] = vars.get("PERIODICITY", None)

        try:
            adc_output_fmt = params['adc_output_fmt']
            multiplier = 4 if adc_output_fmt > 0 else 2  # complex (I,Q) = 4 bytes/sample, real = 2 bytes/sample
            frame_size = params['n_samples'] * params['n_rx'] * params['n_chirps'] * multiplier if None not in (params['n_samples'], params['n_rx'], params['n_chirps']) else None
            params['frame_size'] = frame_size
        except Exception:
            params['frame_size'] = None  # TODO

        # Chirp time = IDLE + RAMP_END
        try:
            chirp_time = vars['IDLE_TIME'] + vars['RAMP_END_TIME']
            params['chirp_time'] = chirp_time
        except KeyError:
            params['chirp_time'] = None  # TODO

        # Chirp slope
        params['chirp_slope'] = vars.get("FREQ_SLOPE", None) * 1e6 if "FREQ_SLOPE" in vars else None  # convert MHz/us to Hz/s

        # Sample rate
        params['sample_rate'] = vars.get("SAMPLE_RATE", None) * 1e3 if "SAMPLE_RATE" in vars else None  # convert ksps to sps

        # Frequency in Hz
        freq = vars.get("START_FREQ", None)
        if freq is not None and params['chirp_time'] is not None and params['n_chirps'] is not None and params['n_tx'] is not None:
            T_chirp = params['chirp_time'] * 1e-6
            λ = 3e8 / (freq * 1e9)
            v_max = λ / (4 * T_chirp)
            v_res = v_max / params['n_chirps']
            params['velocity_max'] = v_max
            params['velocity_res'] = v_res
        else:
            params['velocity_max'] = None  # TODO
            params['velocity_res'] = None  # TODO

        if params['sample_rate'] and params['chirp_slope'] and params['n_samples']:
            range_max = (params['sample_rate'] * 3e8) / (2 * params['chirp_slope'])
            range_res = range_max / params['n_samples']
            params['range_max'] = range_max
            params['range_res'] = range_res
        else:
            params['range_max'] = None  # TODO
            params['range_res'] = None  # TODO

        return params


    def __repr__(self):
        return (f"User-defined Variables:\n{self.variables}\n\n"
                f"Function Calls:\n{self.functions}\n")




if __name__ == '__main__':
    with open('configs/1443/1443_mmwavestudio_config.lua', 'r') as f:
        lua_lines = f.readlines()

    lua_config = LuaRadarConfig(lua_lines)

    # Access results
    print(lua_config)
    print(lua_config.get_params())