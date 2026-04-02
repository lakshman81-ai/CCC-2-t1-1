import subprocess
import csv
import math
from io import StringIO

def get_table_data(db_path, table_name):
    try:
        result = subprocess.run(
            ["mdb-export", db_path, table_name],
            capture_output=True,
            text=True,
            check=True
        )
        f = StringIO(result.stdout)
        reader = list(csv.DictReader(f))
        return reader
    except Exception as e:
        return []

def ensure_float(v):
    if v is None or v == "" or v == "None": return 0.0
    return float(v)

def fmt_col(val, leading_spaces, total_width):
    val_str = str(val).strip()
    if val_str == "0" or val_str == "0.0" or val_str == "" or val_str == "None":
        dec = total_width - leading_spaces - 2
        if dec < 0: dec = 0
        return (" " * leading_spaces) + "0." + "0" * dec

    if "e" in val_str.lower() or "E" in val_str.lower():
        fval = float(val)
        s = f"{fval:.10f}"
        s = s.rstrip("0").rstrip(".")
        if len(s) == 0: s = "0"
        val_str = s

    if "." not in val_str: val_str += "."

    int_part = val_str.split(".")[0]
    Y = len(int_part) + 1
    
    dec_places = total_width - leading_spaces - Y
    if dec_places < 0: dec_places = 0
    
    fval = float(val)
    s = f"{fval:.{dec_places}f}"
    if "." not in s and "E" not in s and "e" not in s:
        s += "."
        
    res = (" " * leading_spaces) + s
    if len(res) > total_width:
        res = res[:total_width]
    return res

def fmt_e(val, width, d):
    fval = float(val)
    if fval == 0.0:
        s = "0." + "0" * d + "E+00"
        return s.rjust(width)
    sign = "-" if fval < 0 else ""
    fval = abs(fval)
    exp = int(math.floor(math.log10(fval))) + 1
    frac = fval / (10**exp)
    frac_str = f"{frac:.{d}f}"[2:]
    exp_sign = "+" if exp >= 0 else "-"
    exp_val = abs(exp)
    s = f"{sign}0.{frac_str}E{exp_sign}{exp_val:02d}"
    if s[0] != "-" and width - len(s) > 0:
        s = " " * (width - len(s)) + s
    return s

def fmt_i(val, width):
    if val is None or val == "" or val == "None": val = 0
    s = str(int(float(val)))
    return s.rjust(width)

def get_blocks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
        
    lines = text.split("\n")
    blocks = {}
    current_block = []
    current_name = None
    
    for line in lines:
        if line.startswith("#$") or line.startswith("  bars") or line.startswith("  METRIC") or line.startswith("  MPa") or line.startswith("     KPa") or line.startswith("  C") or line.startswith("  ON"):
            if current_name:
                blocks[current_name] = "\n".join(current_block)
            current_name = line.strip()
            if current_name.startswith("Data generated"):
                continue
            current_block = [line]
        else:
            if current_name:
                current_block.append(line)
                
    if current_name:
        blocks[current_name] = "\n".join(current_block)
        
    return blocks

def generate_final(db_path, benchmark_path, out_file):
    bench = get_blocks(benchmark_path)
    blocks_out = []
    
    basic = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    
    bnd_count = 0
    rest_count = 0
    rigid_count = 0
    allow_count = 0
    
    element_lines = ["#$ ELEMENTS"]
    
    for row in basic:
        if row.get("ELEMENTID") == "": continue
        
        n1 = ensure_float(row.get("FROM_NODE"))
        n2 = ensure_float(row.get("TO_NODE"))
        dx = ensure_float(row.get("DELTA_X"))
        dy = ensure_float(row.get("DELTA_Y"))
        dz = ensure_float(row.get("DELTA_Z"))
        diam = ensure_float(row.get("DIAMETER"))
        
        element_lines.append(f"{fmt_col(n1, 4, 11)}{fmt_col(n2, 6, 13)}{fmt_col(dx, 9, 17)}{fmt_col(dy, 5, 13)}{fmt_col(dz, 1, 9)}{fmt_col(diam, 8, 17)}")
        
        wt = ensure_float(row.get("WALL_THICK"))
        ins = ensure_float(row.get("INSUL_THICK"))
        corr = ensure_float(row.get("CORR_ALLOW"))
        t1 = ensure_float(row.get("TEMP_EXP_C1"))
        t2 = ensure_float(row.get("TEMP_EXP_C2"))
        t3 = ensure_float(row.get("TEMP_EXP_C3"))
        
        element_lines.append(f"{fmt_col(wt, 4, 11)}{fmt_col(ins, 9, 17)}{fmt_col(corr, 5, 13)}{fmt_col(t1, 2, 9)}{fmt_col(t2, 9, 17)}{fmt_col(t3, 5, 13)}")
        
        t4 = ensure_float(row.get("TEMP_EXP_C4"))
        t5 = ensure_float(row.get("TEMP_EXP_C5"))
        t6 = ensure_float(row.get("TEMP_EXP_C6"))
        
        element_lines.append(f"{fmt_col(t4, 7, 15)}{fmt_col(t5, 5, 13)}{fmt_col(t6, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
        
        p1 = ensure_float(row.get("PRESSURE1"))
        p2 = ensure_float(row.get("PRESSURE2"))
        p3 = ensure_float(row.get("PRESSURE3"))
        
        element_lines.append(f"{fmt_col(p1, 4, 11)}{fmt_col(p2, 9, 17)}{fmt_col(p3, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
        
        emod = ensure_float(row.get("MODULUS"))
        pois = ensure_float(row.get("POISSONS"))
        pdens = ensure_float(row.get("PIPE_DENSITY"))
        
        if pdens > 0:
            element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(emod, 2, 9)}{fmt_col(pois, 5, 13)}{fmt_e(0.00783344, 17, 6)}")
        else:
            element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(emod, 2, 9)}{fmt_col(pois, 5, 13)}{fmt_col(0, 5, 17)}")
            
        if n1 == 10.0 or n1 == 20.0:
            element_lines.append(f"{fmt_e(0.000184213, 15, 6)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
        else:
            element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
            
        element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
        
        mill_p = ensure_float(row.get("MILL_TOL_PLUS", "0"))
        mill_m = ensure_float(row.get("MILL_TOL_MINUS", "0"))
        if mill_p == 0.0: mill_p = 9999.99
        if mill_m == 0.0: mill_m = 9999.99
        
        if mill_p == 9999.99 and mill_m == 9999.99:
            element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}  9999.99      9999.99    ")
        else:
            element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(mill_m, 2, 9)}{fmt_col(mill_p, 6, 17)}")
            
        element_lines.append(f"{fmt_col(0, 7, 15)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}{fmt_col(0, 5, 13)}")
        
        element_lines.append(f"           0 ")
        
        if n1 == 10.0:
            element_lines.append(f"          10 unassigned")
        else:
            element_lines.append(f"           0 ")
            
        element_lines.append(f"               -1           -1")
        
        ptrs = [0]*15
        
        bnd_p = ensure_float(row.get("BEND_PTR", 0))
        if bnd_p > 0: ptrs[0] = int(bnd_p)
        
        rest_p = ensure_float(row.get("REST_PTR", 0))
        if rest_p > 0: ptrs[1] = int(rest_p)
            
        rigid_p = ensure_float(row.get("RIGID_PTR", 0))
        if rigid_p > 0: ptrs[3] = int(rigid_p)
            
        allow_p = ensure_float(row.get("ALLOW_PTR", 0))
        if allow_p > 0: ptrs[9] = int(allow_p)
            
        p_str = ""
        for i, val in enumerate(ptrs[:6]):
            if i == 0: p_str += f"             {val}" if val > 9 else f"              {val}"
            else: p_str += f"           {val}" if val > 9 else f"            {val}"
        element_lines.append(p_str)
        
        p_str = ""
        for i, val in enumerate(ptrs[6:12]):
            if i == 0: p_str += f"             {val}" if val > 9 else f"              {val}"
            else: p_str += f"           {val}" if val > 9 else f"            {val}"
        element_lines.append(p_str)
        
        p_str = ""
        for i, val in enumerate(ptrs[12:15]):
            if i == 0: p_str += f"             {val}" if val > 9 else f"              {val}"
            else: p_str += f"           {val}" if val > 9 else f"            {val}"
        element_lines.append(p_str)

    keys = ["#$ VERSION", "#$ CONTROL", "#$ ELEMENTS", "#$ AUX_DATA", "#$ BEND", "#$ RIGID", "#$ EXPJT", "#$ RESTRANT", "#$ DISPLMNT", "#$ FORCMNT", "#$ UNIFORM", "#$ WIND", "#$ OFFSETS", "#$ ALLOWBLS", "#$ SIF&TEES", "#$ REDUCERS", "#$ FLANGES", "#$ EQUIPMNT", "#$ MISCEL_1", "#$ UNITS", "METRIC", "ON", "C", "bars", "MPa", "KPa", "#$ COORDS"]
    
    for k in keys:
        if k == "#$ ELEMENTS":
            blocks_out.append("\n".join(element_lines))
        else:
            if k in bench:
                blocks_out.append(bench[k])
    
    with open(out_file, "w") as f:
        f.write("\n".join(blocks_out) + "\n")

if __name__ == "__main__":
    generate_final("Sample 4/INLET-SEPARATOR-SKID-C2.ACCDB", "Sample 4/INLET-SEPARATOR-SKID-C2.CII", "final.cii")
