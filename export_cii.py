import subprocess
import csv
import argparse
import os
import copy
import config
from logger import get_logger

logger = get_logger("exporter")

class CaesarExporter:
    def __init__(self, db_path, mode='python'):
        self.mode = mode
        self.db_path = db_path

        if db_path.lower().endswith('.csv'):
            self.load_from_csv(db_path)
            return

        # Extract tables
        try:
            elem_data = subprocess.run(['mdb-export', db_path, 'INPUT_BASIC_ELEMENT_DATA'], capture_output=True, text=True, check=True).stdout
            self.e_rows = list(csv.reader(elem_data.splitlines()))[1:]
        except Exception: self.e_rows = []

        try:
            bend_data = subprocess.run(['mdb-export', db_path, 'INPUT_BENDS'], capture_output=True, text=True, check=True).stdout
            self.b_rows = list(csv.reader(bend_data.splitlines()))[1:]
        except Exception: self.b_rows = []

        try:
            rest_data = subprocess.run(['mdb-export', db_path, 'INPUT_RESTRAINTS'], capture_output=True, text=True, check=True).stdout
            self.r_rows = list(csv.reader(rest_data.splitlines()))[1:]
        except Exception: self.r_rows = []

        try:
            sif_data = subprocess.run(['mdb-export', db_path, 'INPUT_SIFTEES'], capture_output=True, text=True, check=True).stdout
            self.s_rows = list(csv.reader(sif_data.splitlines()))[1:]
        except Exception: self.s_rows = []

    def load_from_csv(self, csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        self.e_rows = []

        for idx, row in df.iterrows():
            new_row = [str(idx+1), str(idx+1)]

            from_node = str(row.get('FROM_NODE', ''))
            if pd.isna(from_node) or from_node == '': from_node = config.CAESAR_AUTO_CALC_STR
            new_row.append(from_node)

            to_node = str(row.get('TO_NODE', ''))
            if pd.isna(to_node) or to_node == '': to_node = config.CAESAR_AUTO_CALC_STR
            new_row.append(to_node)

            full_row = new_row + [config.CAESAR_AUTO_CALC_STR] * 130

            cols = ['DX', 'DY', 'DZ', 'DIAMETER', 'THICKNESS', 'CORROSION', 'INSULATION', 'DENSITY']
            for i, col in enumerate(cols):
                val = row.get(col, '')
                if not pd.isna(val) and val != '':
                    full_row[4 + i] = str(val)

            full_row[config.INDEX_MATERIAL + 10] = str(config.DEFAULT_MATERIAL_ID)
            for i in range(config.INDEX_TEMPERATURE_START, config.INDEX_TEMPERATURE_END + 1):
                full_row[i + 10] = str(config.DEFAULT_TEMPERATURE)
            for i in range(config.INDEX_PRESSURE_START, config.INDEX_PRESSURE_END + 1):
                full_row[i + 10] = str(config.DEFAULT_PRESSURE)

            self.e_rows.append(full_row)

        self.b_rows = []
        self.r_rows = []
        self.s_rows = []

    def fmt_val(self, val_str, width):
        """Implements the Y.(X-Y) Rule for pure python generation"""
        if val_str in ('-1.01010000705719', config.CAESAR_AUTO_CALC_STR.strip()):
            val_str = '-1.0101'
        try:
            val_float = float(val_str)
            if float(val_float) == int(val_float) and val_str.count('.') == 0:
                val_str += "." # CAESAR II requires decimals
        except: pass

        y = len(val_str)
        decimals = width - y
        if decimals < 0: decimals = 0

        try:
            fmt = f"{{:{width}.{decimals}f}}"
            return fmt.format(float(val_str))
        except:
            return str(val_str).rjust(width)

    def write_standalone_python(self, out_file):
        """Generates a properly formatted .CII file matching the CAESAR II neutral file spec."""
        out = ""

        # VERSION section
        out += "#$ VERSION \n"
        out += "    5.00000      11.0000        1256\n"
        out += "    PROJECT:                                                               \n"
        out += "                                                                           \n"
        out += "    CLIENT :                                                               \n"
        out += "                                                                           \n"
        out += "    ANALYST:                                                               \n"
        out += "                                                                           \n"
        out += "    NOTES  :                                                               \n"
        for _ in range(14):
            out += "                                                                           \n"

        # CONTROL section
        num_elements = len(self.e_rows)
        num_bends = len(self.b_rows)
        num_restr = len(self.r_rows)
        num_sifs = len(self.s_rows)

        out += "#$ CONTROL \n"
        # Format: (2X, 6I13) — first line has NUMELT, rest zeros
        out += "  " + "".join(f"{v:>13}" for v in [num_elements, 0, 0, 0, 0, 0]) + "\n"
        # Aux count lines: NUMBND at [0], NUMRES at [3], NUMSIF at aux[10] = line3 pos[4]
        out += "  " + "".join(f"{v:>13}" for v in [num_bends, 0, 0, num_restr, 0, 0]) + "\n"
        out += "  " + "".join(f"{v:>13}" for v in [0, 0, 0, 0, num_sifs, 0]) + "\n"
        out += "  " + f"{0:>13}" + "\n"

        # ELEMENTS section
        out += "#$ ELEMENTS\n"

        auto13 = "    -1.010100"  # 13-char -1.0101 auto-calc float
        zero13 = "     0.000000"  # 13-char zero float

        for row in self.e_rows:
            # All REL values use 13-char fields: format (2X, 6G13.6)
            node1 = self.fmt_val(row[2], 13)
            node2 = self.fmt_val(row[3], 13)
            dx    = self.fmt_val(row[4], 13)
            dy    = self.fmt_val(row[5], 13)
            dz    = self.fmt_val(row[6], 13)
            diam  = self.fmt_val(row[7], 13)
            wall  = self.fmt_val(row[8], 13) if len(row) > 8 and str(row[8]).strip() not in ('', config.CAESAR_AUTO_CALC_STR.strip(), '-1.0101') else zero13

            # 9 REL lines: 8 x 6 floats + 1 x 5 floats = 53 values (padded to 98 by parser)
            out += f"  {node1}{node2}{dx}{dy}{dz}{diam}\n"          # Line 1
            out += f"  {wall}{auto13}{auto13}{auto13}{auto13}{auto13}\n"  # Line 2
            for _ in range(6):                                        # Lines 3–8
                out += f"  {auto13}{auto13}{auto13}{auto13}{auto13}{auto13}\n"
            out += f"  {auto13}{auto13}{auto13}{auto13}{auto13}\n"   # Line 9 (5 values)

            # 2 STR lines: format (7X, I5, 1X, A0) — empty string, length = 0
            out += "           0 \n"
            out += "           0 \n"

            # Color line: (2X, 2I13) = "  " + "           -1" x2
            out += "  " + f"{-1:>13}" + f"{-1:>13}" + "\n"

            # 3 IEL lines: 6 + 6 + 3 integers, format (2X, 6I13)
            out += "  " + "".join(f"{0:>13}" for _ in range(6)) + "\n"  # IEL[0–5]
            out += "  " + "".join(f"{v:>13}" for v in [0, 0, 0, 0, 0, config.DEFAULT_MATERIAL_ID]) + "\n"  # IEL[6–11], material at IEL[11]
            out += "  " + "".join(f"{0:>13}" for _ in range(3)) + "\n"  # IEL[12–14]

        # AUX_DATA section
        out += "#$ AUX_DATA\n"

        # BEND: 3 float lines per record (6 + 6 + 2 values)
        out += "#$ BEND    \n"
        for row in self.b_rows:
            val1 = self.fmt_val(row[4], 13) if len(row) > 4 else zero13
            val2 = self.fmt_val(row[5], 13) if len(row) > 5 else zero13
            out += f"  {val1}{val2}{zero13}{zero13}{zero13}{zero13}\n"
            out += f"  {zero13}{zero13}{zero13}{zero13}{zero13}{zero13}\n"
            out += f"  {zero13}{zero13}\n"

        out += "#$ RIGID   \n"
        out += "#$ EXPJT   \n"

        # RESTRANT: 2 float lines (6 + 3 values) + 2 STR lines per record
        out += "#$ RESTRANT\n"
        for row in self.r_rows:
            node  = self.fmt_val(row[4], 13) if len(row) > 4 else zero13
            rtype = self.fmt_val(row[6], 13) if len(row) > 6 else zero13
            out += f"  {node}{rtype}{zero13}{zero13}{zero13}{zero13}\n"
            out += f"  {zero13}{zero13}{zero13}\n"
            out += "           0 \n"
            out += "           0 \n"

        out += "#$ DISPLMNT\n"
        out += "#$ FORCMNT \n"
        out += "#$ UNIFORM \n"
        out += "#$ WIND    \n"
        out += "#$ OFFSETS \n"

        # ALLOWBLS: standard defaults
        out += "#$ ALLOWBLS\n"
        out += "       0.000000     0.000000     0.000000     0.000000  1.00000      1.00000    \n"
        out += "    1.00000         0.000000     0.000000  9999.99         0.000000  3.00000    \n"
        for _ in range(22):
            out += "       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000\n"
        out += "    1.00000      1.00000      1.00000      1.00000      1.00000      1.00000    \n"

        out += "#$ SIF&TEES\n"
        out += "#$ REDUCERS\n"
        out += "#$ FLANGES \n"
        out += "#$ EQUIPMNT\n"

        with open(out_file, 'w') as f:
            f.write(out)

        print(f"Export completed natively in Python. Standalone file written to {out_file}")

    def export(self, out_file):
        # We always run pure python standalone now, ensuring NO dependencies on original .CII
        self.write_standalone_python(out_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='middle_layer_template.csv')
    parser.add_argument('--output', default='final.cii')
    parser.add_argument('--mode', default='python')
    args = parser.parse_args()

    exporter = CaesarExporter(args.input, mode=args.mode)
    exporter.export(args.output)
