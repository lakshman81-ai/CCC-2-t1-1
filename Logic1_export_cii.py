"""
Logic1_export_cii.py — CAESAR II .CII standalone generator for Logic 1.

Differences from P1 export_cii.py:
  - Fix 1.1: Dual column name lookup (ACCDB names + P1 legacy names)
  - Fix 1.2: No subprocess; from_tables() classmethod for browser use
  - Fix 1.3: All IEL pointer slots mapped (BEND, RIGID, EXPJ, REST, DISP,
              FORCMNT, ULOAD, WLOAD, EOFF, ALLOW, INT, MATERIAL_NUM,
              FLANGE, REDUCER, HGR, NOZ)
  - Import: Logic1_config, Logic1_logger
"""
import csv
import argparse
import copy
import pandas as pd
from typing import List, Dict, Any, Optional

import Logic1_config as config
from Logic1_logger import get_logger

logger = get_logger("Logic1_export_cii")

# ── CAESAR II auto sentinel ────────────────────────────────────────────────
_AUTO = config.get_sentinel_str()
_AUTO_F = config.get_sentinel_float()

# ── Universal aux_data record templates (correct line-count per type) ─────────
# Matches Logic2_importer._AUX_TEMPLATES
_BEND_TEMPLATE = [
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000     0.000000"
]
_RESTRANT_TEMPLATE = [
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000     0.000000     0.000000",
    "           0 ",
    "           0 "
]
_RIGID_TEMPLATE = [
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000"
]
_SIF_TEMPLATE = [
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
    "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000"
]


class CaesarExporter:

    # ── Construction from CLI / file paths ───────────────────────────────────
    def __init__(self, db_path: str, mode: str = 'python'):
        self.mode = mode
        self.db_path = db_path

        if db_path.lower().endswith('.csv'):
            self.load_from_csv(db_path)
            return

        # Subprocess path (desktop only — will not work in browser)
        try:
            import subprocess
            elem_data = subprocess.run(
                ['mdb-export', db_path, 'INPUT_BASIC_ELEMENT_DATA'],
                capture_output=True, text=True, check=True).stdout
            self.e_rows = list(csv.reader(elem_data.splitlines()))[1:]
        except Exception:
            self.e_rows = []

        for attr, table in [('b_rows', 'INPUT_BENDS'), ('r_rows', 'INPUT_RESTRAINTS'),
                            ('rg_rows', 'INPUT_RIGIDS'), ('s_rows', 'INPUT_SIFTEES')]:
            try:
                import subprocess
                data = subprocess.run(
                    ['mdb-export', db_path, table],
                    capture_output=True, text=True, check=True).stdout
                setattr(self, attr, list(csv.reader(data.splitlines()))[1:])
            except Exception:
                setattr(self, attr, [])

    # ── Construction from JS mdb-reader (browser / PyScript) ─────────────────
    @classmethod
    def from_tables(cls,
                    elem_rows: List[Dict],
                    bend_rows: Optional[List[Dict]] = None,
                    rest_rows: Optional[List[Dict]] = None,
                    rigid_rows: Optional[List[Dict]] = None,
                    sif_rows: Optional[List[Dict]] = None) -> 'CaesarExporter':
        """
        Create from pre-extracted dicts from JS mdb-reader (browser-safe).
        Each list is a list of row dicts with ACCDB column names.
        """
        obj = cls.__new__(cls)
        obj.mode = 'python'
        obj.db_path = '<browser>'

        # Store rows as dicts (ACCDB column names) — write_standalone_python reads them directly
        obj.e_dicts = elem_rows or []
        obj.b_dicts = bend_rows or []
        obj.r_dicts = rest_rows or []
        obj.rg_dicts = rigid_rows or []
        obj.s_dicts = sif_rows or []

        # Legacy positional rows not used in from_tables path
        obj.e_rows = []
        obj.b_rows = []
        obj.r_rows = []
        obj.rg_rows = []
        obj.s_rows = []
        return obj

    # ── CSV loading (Fix 1.1: dual column names) ─────────────────────────────
    def load_from_csv(self, csv_path: str):
        df = pd.read_csv(csv_path)
        self.e_dicts = []
        self.b_dicts = []
        self.r_dicts = []
        self.rg_dicts = []
        self.s_dicts = []
        self.e_rows = []
        self.b_rows = []
        self.r_rows = []
        self.rg_rows = []
        self.s_rows = []

        for idx, row in df.iterrows():
            d = {}
            d['FROM_NODE'] = row.get('FROM_NODE', '')
            d['TO_NODE'] = row.get('TO_NODE', '')
            # Fix 1.1: dual column name lookup
            d['DELTA_X'] = row.get('DELTA_X', row.get('DX', ''))
            d['DELTA_Y'] = row.get('DELTA_Y', row.get('DY', ''))
            d['DELTA_Z'] = row.get('DELTA_Z', row.get('DZ', ''))
            d['DIAMETER'] = row.get('DIAMETER', '')
            d['WALL_THICK'] = row.get('WALL_THICK', row.get('THICKNESS', ''))
            d['CORR_ALLOW'] = row.get('CORR_ALLOW', row.get('CORROSION', ''))
            d['INSUL_THICK'] = row.get('INSUL_THICK', row.get('INSULATION', ''))
            d['PIPE_DENSITY'] = row.get('PIPE_DENSITY', row.get('DENSITY', ''))
            d['INSUL_DENSITY'] = row.get('INSUL_DENSITY', '')
            d['FLUID_DENSITY'] = row.get('FLUID_DENSITY', '')
            d['MODULUS'] = row.get('MODULUS', '')
            d['POISSONS'] = row.get('POISSONS', '')
            d['MATERIAL_NUM'] = row.get('MATERIAL_NUM', config.DEFAULT_MATERIAL_ID)
            d['MATERIAL_NAME'] = row.get('MATERIAL_NAME', '')
            d['MILL_TOL_PLUS'] = row.get('MILL_TOL_PLUS', 9999.99)
            d['MILL_TOL_MINUS'] = row.get('MILL_TOL_MINUS', 9999.99)
            # Thermal
            for i in range(1, 10):
                d[f'TEMP_EXP_C{i}'] = row.get(f'TEMP_EXP_C{i}', '')
            # Pressure
            for i in range(1, 10):
                d[f'PRESSURE{i}'] = row.get(f'PRESSURE{i}', '')
            # Pointers
            for ptr in ['BEND_PTR','RIGID_PTR','EXPJ_PTR','REST_PTR','DISP_PTR',
                        'FORCMNT_PTR','ULOAD_PTR','WLOAD_PTR','EOFF_PTR','ALLOW_PTR',
                        'INT_PTR','HGR_PTR','NOZ_PTR','REDUCER_PTR','FLANGE_PTR']:
                d[ptr] = row.get(ptr, 0)
            # BND_ columns → bend row
            if str(row.get('BND_RADIUS', '')).strip() not in ('', 'nan', 'None'):
                bd = {
                    'BEND_PTR':  row.get('BEND_PTR', 0),
                    'RADIUS':     row.get('BND_RADIUS', 0),
                    'ANGLE1':     row.get('BND_ANGLE1', 0),
                    'NODE1':      row.get('BND_NODE1', 0),
                    'ANGLE2':     row.get('BND_ANGLE2', 0),
                    'NODE2':      row.get('BND_NODE2', 0),
                    'ANGLE3':     row.get('BND_ANGLE3', 0),
                    'NODE3':      row.get('BND_NODE3', 0),
                    'NUM_MITER':  row.get('BND_NUM_MITER', 0),
                    'FIT_THICK':  row.get('BND_FIT_THICK', 0),
                    'KFACTOR':    row.get('BND_KFACTOR', 0),
                    'WI_FACTOR':  row.get('BND_WI_FACTOR', 0),
                }
                self.b_dicts.append(bd)
            # RST_ columns → restraint row
            if str(row.get('RST_NODE_NUM', '')).strip() not in ('', 'nan', 'None'):
                rd = {
                    'REST_PTR':   row.get('REST_PTR', 0),
                    'NODE_NUM':   row.get('RST_NODE_NUM', 0),
                    'RES_TYPEID': row.get('RST_RES_TYPEID', 0),
                    'STIFFNESS':  row.get('RST_STIFFNESS', 0),
                    'GAP':        row.get('RST_GAP', 0),
                    'FRIC_COEF':  row.get('RST_FRIC_COEF', 0),
                    'CNODE':      row.get('RST_CNODE', 0),
                    'XCOSINE':    row.get('RST_XCOSINE', 0),
                    'YCOSINE':    row.get('RST_YCOSINE', 0),
                    'ZCOSINE':    row.get('RST_ZCOSINE', 0),
                }
                self.r_dicts.append(rd)
            # RGD_ columns → rigid row
            if str(row.get('RGD_RIGID_WGT', '')).strip() not in ('', 'nan', 'None'):
                self.rg_dicts.append({
                    'RIGID_PTR': row.get('RIGID_PTR', 0),
                    'RIGID_WGT': row.get('RGD_RIGID_WGT', 0),
                    'RIGID_TYPE': row.get('RGD_RIGID_TYPE', ''),
                })
            # SIF_ columns → sif row
            if str(row.get('SIF_SIF_NUM', '')).strip() not in ('', 'nan', 'None'):
                sd = {'SIF_PTR': row.get('INT_PTR', 0), 'SIF_NUM': row.get('SIF_SIF_NUM', 0)}
                for col in ['NODE','TYPE','SIF_IN','SIF_OUT','SIF_TORSION','SIF_AXIAL',
                            'SIF_PRESSURE','WELD_d','FILLET','PAD_THK','FTG_RO',
                            'CROTCH','WELD_ID','B1','B2']:
                    sd[col] = row.get(f'SIF_{col}', 0)
                self.s_dicts.append(sd)

            self.e_dicts.append(d)

    # ── Float formatter ───────────────────────────────────────────────────────
    def fmt_val(self, val_str, width: int) -> str:
        if str(val_str).strip() in ('-1.01010000705719', _AUTO.strip(), '-1.0101', str(_AUTO_F)):
            val_str = str(_AUTO_F)
        try:
            val_float = float(val_str)
            s = str(val_str)
            if float(val_float) == int(val_float) and '.' not in s:
                s += "."
            val_str = s
        except Exception:
            pass

        y = len(str(val_str))
        decimals = max(0, width - y)
        try:
            return f"{{:{width}.{decimals}f}}".format(float(val_str))
        except Exception:
            return str(val_str).rjust(width)

    def _fv(self, val, width: int = 13) -> str:
        """Format a value from ACCDB row dict (float or sentinel)."""
        _auto_str = config.get_sentinel_str()
        _auto_f = config.get_sentinel_float()

        try:
            f = float(val)
            # Use a tiny tolerance for floating point comparisons
            if abs(f - _auto_f) < 0.0001 or abs(f - (-1.01010000705719)) < 0.0001:
                return _auto_str
            return self.fmt_val(f, width)
        except Exception:
            return "     0.000000"

    # ── Main writer ───────────────────────────────────────────────────────────
    def write_standalone_python(self, out_file: Optional[str] = None) -> str:
        """
        Generates a .CII file from e_dicts (ACCDB-format row dicts).
        Returns the CII text; also writes to out_file if given.
        """
        _auto_f = config.get_sentinel_float()
        zero13 = "     0.000000"
        auto13 = self.fmt_val(_auto_f, 13)

        out = ""

        # ── VERSION ──────────────────────────────────────────────────────────
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

        # ── CONTROL ──────────────────────────────────────────────────────────
        ne  = len(self.e_dicts)
        nb  = len(self.b_dicts)
        nr  = len(self.r_dicts)
        nrg = len(self.rg_dicts)
        ns  = len(self.s_dicts)

        out += "#$ CONTROL \n"
        out += "  " + "".join(f"{v:>13}" for v in [ne, 0, 0, 0, 0, 0]) + "\n"
        out += "  " + "".join(f"{v:>13}" for v in [nb, nrg, 0, nr, 0, 0]) + "\n"
        out += "  " + "".join(f"{v:>13}" for v in [0, 0, 0, 0, ns, 0]) + "\n"
        out += "  " + f"{0:>13}" + "\n"

        # ── ELEMENTS ─────────────────────────────────────────────────────────
        out += "#$ ELEMENTS\n"

        for d in self.e_dicts:
            g = lambda col: self._fv(d.get(col, 0))

            # REL lines (9 lines × 6 floats = 54 values)
            out += f"  {g('FROM_NODE')}{g('TO_NODE')}{g('DELTA_X')}{g('DELTA_Y')}{g('DELTA_Z')}{g('DIAMETER')}\n"
            out += f"  {g('WALL_THICK')}{g('INSUL_THICK')}{g('CORR_ALLOW')}{g('TEMP_EXP_C1')}{g('TEMP_EXP_C2')}{g('TEMP_EXP_C3')}\n"
            out += f"  {g('TEMP_EXP_C4')}{g('TEMP_EXP_C5')}{g('TEMP_EXP_C6')}{zero13}{zero13}{zero13}\n"
            out += f"  {g('PRESSURE1')}{g('PRESSURE2')}{g('PRESSURE3')}{zero13}{zero13}{zero13}\n"

            pdens = d.get('PIPE_DENSITY', 0)
            try:
                pd_f = float(pdens)
            except Exception:
                pd_f = 0.0

            emod_str = g('MODULUS')
            pois_str = g('POISSONS')

            if pd_f > 0:
                # Use scientific notation for density matching CAESAR II format
                pd_sci = f"{pd_f:13.6E}"
                out += f"  {zero13}{zero13}{zero13}{emod_str}{pois_str}{pd_sci}\n"
            else:
                out += f"  {zero13}{zero13}{zero13}{emod_str}{pois_str}{zero13}\n"

            out += f"  {zero13}{zero13}{zero13}{zero13}{zero13}{zero13}\n"
            out += f"  {zero13}{zero13}{zero13}{zero13}{zero13}{zero13}\n"

            mp  = d.get('MILL_TOL_PLUS', 9999.99)
            mm  = d.get('MILL_TOL_MINUS', 9999.99)
            try:
                mp_f, mm_f = float(mp), float(mm)
                if mp_f <= 0 or abs(mp_f - 9999.99) < 1: mp_f = 9999.99
                if mm_f <= 0 or abs(mm_f - 9999.99) < 1: mm_f = 9999.99
            except Exception:
                mp_f = mm_f = 9999.99

            if mp_f == 9999.99 and mm_f == 9999.99:
                out += f"  {zero13}{zero13}{zero13}{zero13}  9999.99      9999.99    \n"
            else:
                out += f"  {zero13}{zero13}{zero13}{zero13}{self.fmt_val(mm_f,13)}{self.fmt_val(mp_f,13)}\n"

            out += f"  {zero13}{zero13}{zero13}{zero13}{zero13}\n"

            # STR lines (element name / pipeline reference)
            elem_name = str(d.get('ELEMENT_NAME', d.get('LINE_NO', ''))).strip()
            if elem_name in ('None', 'nan', ''):
                out += "           0 \n"
            else:
                out += f"       {len(elem_name):5d} {elem_name}\n"
            out += "           0 \n"

            # Color line
            out += f"  " + f"{-1:>13}" + f"{-1:>13}" + "\n"

            # IEL lines (3 lines × 6 ints = 18 values)
            def _ip(col):
                try:
                    v = int(float(d.get(col, 0)))
                    return v if v > 0 else 0
                except Exception:
                    return 0

            mat = _ip('MATERIAL_NUM') or config.DEFAULT_MATERIAL_ID
            iel = [
                _ip('BEND_PTR'),    # 0
                _ip('RIGID_PTR'),   # 1
                _ip('EXPJ_PTR'),    # 2
                _ip('REST_PTR'),    # 3
                _ip('DISP_PTR'),    # 4
                _ip('FORCMNT_PTR'), # 5
                _ip('ULOAD_PTR'),   # 6
                _ip('WLOAD_PTR'),   # 7
                _ip('EOFF_PTR'),    # 8
                _ip('ALLOW_PTR'),   # 9
                _ip('INT_PTR'),     # 10
                mat,                # 11 — MATERIAL_NUM
                0,                  # 12 — reserved
                _ip('FLANGE_PTR'),  # 13
                _ip('REDUCER_PTR'), # 14
                _ip('HGR_PTR'),     # 15
                _ip('NOZ_PTR'),     # 16
                0,                  # 17
            ]
            out += "  " + "".join(f"{v:>13}" for v in iel[0:6]) + "\n"
            out += "  " + "".join(f"{v:>13}" for v in iel[6:12]) + "\n"
            out += "  " + "".join(f"{v:>13}" for v in iel[12:18]) + "\n"

        # ── AUX_DATA ─────────────────────────────────────────────────────────
        out += "#$ AUX_DATA\n"

        # BEND
        out += "#$ BEND    \n"
        for row in self.b_dicts:
            g = lambda col: self._fv(row.get(col, 0))
            out += f"  {g('RADIUS')}{g('ANGLE1')}{g('NODE1')}{g('ANGLE2')}{g('NODE2')}{g('ANGLE3')}\n"
            out += f"  {g('NODE3')}{g('NUM_MITER')}{g('FIT_THICK')}{g('KFACTOR')}{g('WI_FACTOR')}     0.000000\n"
            out += f"       0.000000     0.000000\n"

        # RIGID
        out += "#$ RIGID   \n"
        for row in self.rg_dicts:
            wgt = self._fv(row.get('RIGID_WGT', 0))
            z   = "     0.000000"
            out += f"  {wgt}{z}{z}{z}{z}{z}\n"
            out += f"  {z}{z}{z}{z}{z}{z}\n"
            out += f"  {z}\n"

        out += "#$ EXPJT   \n"

        # RESTRANT
        out += "#$ RESTRANT\n"
        for row in self.r_dicts:
            g = lambda col: self._fv(row.get(col, 0))
            out += f"  {g('NODE_NUM')}{g('RES_TYPEID')}{g('STIFFNESS')}{g('GAP')}{g('FRIC_COEF')}{g('CNODE')}\n"
            out += f"  {g('XCOSINE')}{g('YCOSINE')}{g('ZCOSINE')}\n"
            tag  = str(row.get('RES_TAG', '') or '').strip()
            guid = str(row.get('RES_GUID', '') or '').strip()
            if tag and tag not in ('None', 'nan'):
                out += f"       {len(tag):5d} {tag}\n"
            else:
                out += "           0 \n"
            if guid and guid not in ('None', 'nan'):
                out += f"       {len(guid):5d} {guid}\n"
            else:
                out += "           0 \n"

        out += "#$ DISPLMNT\n"
        out += "#$ FORCMNT \n"
        out += "#$ UNIFORM \n"
        out += "#$ WIND    \n"
        out += "#$ OFFSETS \n"

        # ALLOWBLS (standard 25-line default)
        out += "#$ ALLOWBLS\n"
        out += "       0.000000     0.000000     0.000000     0.000000  1.00000      1.00000    \n"
        out += "    1.00000         0.000000     0.000000  9999.99         0.000000  3.00000    \n"
        for _ in range(22):
            out += "       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000\n"
        out += "    1.00000      1.00000      1.00000      1.00000      1.00000      1.00000    \n"

        # SIF&TEES
        out += "#$ SIF&TEES\n"
        for row in self.s_dicts:
            g = lambda col: self._fv(row.get(col, 0))
            out += f"  {g('SIF_NUM')}{g('NODE')}{g('TYPE')}{g('SIF_IN')}{g('SIF_OUT')}{g('SIF_TORSION')}\n"
            out += f"  {g('SIF_AXIAL')}{g('SIF_PRESSURE')}{g('WELD_d')}{g('FILLET')}{g('PAD_THK')}{g('FTG_RO')}\n"

        out += "#$ REDUCERS\n"
        out += "#$ FLANGES \n"
        out += "#$ EQUIPMNT\n"

        if out_file:
            with open(out_file, 'w') as f:
                f.write(out)
            logger.info(f"Logic1: CII written to {out_file}")

        return out

    def export(self, out_file: str = None) -> str:
        return self.write_standalone_python(out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='middle_layer_template.csv')
    parser.add_argument('--output', default='output_logic1.cii')
    args = parser.parse_args()
    exp = CaesarExporter(args.input)
    exp.export(args.output)
    print(f"Logic1: exported to {args.output}")
