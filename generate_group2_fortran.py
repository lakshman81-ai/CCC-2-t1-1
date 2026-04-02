import subprocess
import csv
from io import StringIO
import re

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

def fortran_f(val, width, fill_empty=True):
    val_str = str(val).strip()
    if val_str == "0" or val_str == "0.0" or val_str == "" or val_str == "None":
        if not fill_empty:
            return " " * width
        return ("0." + "0" * (width - 3)).rjust(width)

    if "e" in val_str.lower() or "E" in val_str.lower():
        fval = float(val)
        s = f"{fval:.10f}"
        s = s.rstrip("0").rstrip(".")
        if len(s) == 0: s = "0"
        val_str = s

    if "." not in val_str: val_str += "."

    int_part = val_str.split(".")[0]
    int_len = len(int_part) + 1
    dec_places = width - int_len
    if dec_places < 0: dec_places = 0
    
    fval = float(val)
    s = f"{fval:.{dec_places}f}"
    return s.rjust(width)

def fortran_e(val, width):
    fval = float(val)
    if fval == 0.0:
        s = "0." + "0" * (width - 6) + "E+00"
        return s.rjust(width)
    s = f"{fval:>{width}.6E}"
    s = s.replace("E-0", "E-").replace("E+0", "E+")
    # Fortran format is slightly different
    return s.rjust(width)

def fortran_i(val, width):
    if val is None or val == "" or val == "None": val = 0
    s = str(int(float(val)))
    return s.rjust(width)

def ensure_float(v):
    if v is None or v == "" or v == "None": return 0.0
    return float(v)

def generate_blocks():
    db_path = "Sample 4/INLET-SEPARATOR-SKID-C2.ACCDB"
    blocks = []
    
    # BEND
    bends_table = get_table_data(db_path, "INPUT_BENDS")
    basic = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    bends_dict = {row["BEND_PTR"]: row for row in bends_table if "BEND_PTR" in row}
    
    bend_lines = ["#$ BEND    "]
    for row in basic:
        ptr = row.get("BND_PTR", "0")
        if ptr != "0" and ptr != "":
            b_row = bends_dict.get(ptr, {})
            r = ensure_float(b_row.get("BEND_RADIUS", 0))
            a = ensure_float(b_row.get("BEND_ANGLE", 0))
            
            l1 = f"    {fortran_f(r, 7)}{fortran_f(0, 6)}  {fortran_f(45, 7)}      {fortran_f(a, 7)}{fortran_f(0, 6)}  {fortran_f(a-1, 7)}    "
            l2 = f"       {fortran_f(0, 6)}     {fortran_f(0, 6)}     {fortran_f(0, 6)}  {fortran_f(0, 7)}         {fortran_f(0, 6)}     {fortran_f(0, 6)}"
            l3 = f"       {fortran_f(0, 8)}     {fortran_f(0, 8)}"
            bend_lines.extend([l1, l2, l3])
    
    blocks.extend(bend_lines)
    
    # RESTRANT
    rest_lines = ["#$ RESTRANT"]
    rest_table = get_table_data(db_path, "INPUT_RESTRAINTS")
    rest_dict = {row["REST_PTR"]: row for row in rest_table if "REST_PTR" in row}
    type_map = {"ANC": 1.0, "Y": 2.0}
    
    for row in basic:
        ptr = row.get("REST_PTR", "0")
        if ptr != "0" and ptr != "":
            r_row = rest_dict.get(ptr, {})
            for idx in range(1, 5):
                rt = r_row.get(f"REST_TYPE_{idx}", "")
                node = ensure_float(r_row.get(f"REST_NODE_{idx}", 0))
                if rt == "" or rt == "None" or node == 0: continue
                
                stiff = ensure_float(r_row.get(f"REST_STIFF_{idx}", 0))
                gap1 = ensure_float(r_row.get(f"REST_GAP_1_{idx}", 0))
                gap2 = ensure_float(r_row.get(f"REST_GAP_2_{idx}", 0))
                mu = ensure_float(r_row.get(f"REST_MU_{idx}", 0))
                tval = type_map.get(rt, 1.0)
                
                l1 = f"    {fortran_i(node, 7)}      {fortran_f(tval, 6)}      {fortran_f(stiff, 8)}     {fortran_f(gap1, 8)}"
                l2 = f"       {fortran_f(gap2, 8)}     {fortran_f(mu, 8)}     {fortran_f(0, 8)}     {fortran_f(0, 8)}"
                
                dx = ensure_float(r_row.get(f"REST_DX_{idx}", 0))
                dy = ensure_float(r_row.get(f"REST_DY_{idx}", 0))
                dz = ensure_float(r_row.get(f"REST_DZ_{idx}", 0))
                
                l3 = f"       {fortran_f(dx, 8)}     {fortran_f(dy, 8)}     {fortran_f(dz, 8)}     {fortran_f(0, 8)}"
                rest_lines.extend([l1, l2, l3])
    blocks.extend(rest_lines)
    
    # ELEMENTS
    elem_lines = ["#$ ELEMENTS"]
    
    # Needs full pointer map calculation
    bnd_count = 0
    rest_count = 0
    
    for row in basic:
        if row.get("ELEMENTID") == "": continue
        
        n1 = ensure_float(row.get("FROM_NODE"))
        n2 = ensure_float(row.get("TO_NODE"))
        dx = ensure_float(row.get("DX"))
        dy = ensure_float(row.get("DY"))
        dz = ensure_float(row.get("DZ"))
        diam = ensure_float(row.get("DIAMETER"))
        
        elem_lines.append(f"    {fortran_f(n1, 6)}      {fortran_f(n2, 6)}      {fortran_f(dx, 8)}     {fortran_f(dy, 8)}     {fortran_f(dz, 8)}     {fortran_f(diam, 8)}")
        
        wt = ensure_float(row.get("WALL_THICK"))
        ca = ensure_float(row.get("CORROSION"))
        mill = ensure_float(row.get("MILL_TOL"))
        in_d = ensure_float(row.get("INSUL_THICK"))
        in_dens = ensure_float(row.get("INSUL_DENSITY"))
        mat_num = ensure_float(row.get("MATERIAL_NUM"))
        
        elem_lines.append(f"       {fortran_f(wt, 8)}     {fortran_f(ca, 8)}  {fortran_f(mill, 7)}      {fortran_f(in_d, 7)}         {fortran_f(in_dens, 8)}     {fortran_f(mat_num, 8)}")

    blocks.extend(elem_lines)
    
    with open("final.cii", "w") as f:
        f.write("\n".join(blocks) + "\n")

if __name__ == '__main__':
    generate_blocks()
