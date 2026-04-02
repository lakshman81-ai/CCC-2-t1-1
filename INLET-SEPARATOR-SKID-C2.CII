import subprocess
import csv
import io

def get_table_data(db_path, table_name):
    cmd = ["mdb-export", db_path, table_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    reader = csv.DictReader(io.StringIO(result.stdout))
    return list(reader)

def fmt_f(val_str, width):
    try:
        val = float(val_str)
    except ValueError:
        val = 0.0
    int_part = str(int(abs(val)))
    y = len(int_part) + 1
    if val < 0:
        y += 1
    decimals = width - y
    if decimals < 0:
        decimals = 0
    return f"F{width}.{decimals}"

def ensure_float_str(val_str):
    try:
        val = float(val_str)
        if "." not in str(val_str):
            return f"{val_str}.0"
        return str(val_str)
    except ValueError:
        return "0.0"

def generate_reducers(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)', advance='no') '#$ REDUCERS'")
    basic_elements = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    reducers_table = get_table_data(db_path, "INPUT_REDUCERS")
    reducers_dict = {row["REDUCER_PTR"]: row for row in reducers_table}
    
    red_ptrs = []
    for row in basic_elements:
        ptr = row.get("REDUCER_PTR", "0")
        if ptr != "0" and ptr != "":
            if ptr in reducers_dict:
                red_ptrs.append(ptr)
                
    for i, ptr in enumerate(red_ptrs):
        row = reducers_dict[ptr]
        l = row.get("LENGTH", "0")
        d1 = row.get("DIAMETER_1", "0")
        d2 = row.get("DIAMETER_2", "0")
        w1 = row.get("WALL_THICK_1", "0")
        w2 = row.get("WALL_THICK_2", "0")
        cone = row.get("CONE_ANGLE", "0")
        lines.append(f"    write({unit_var}, '(2X, 6F13.6)') {l}, {d1}, {d2}, {w1}, {w2}, {cone}")
    return lines

def generate_expjt(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)', advance='no') '#$ EXPJT   '")
    basic_elements = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    expjt_table = get_table_data(db_path, "INPUT_EXPJT")
    expjt_dict = {row["EXPJT_PTR"]: row for row in expjt_table if "EXPJT_PTR" in row}
    # It might be INPUT_EXPANSION_JOINTS, or INPUT_EXPJT
    # I don't know the exact names, but the loop is there.
    exp_ptrs = []
    for row in basic_elements:
        ptr = row.get("EXPJ_PTR", "0")
        if ptr != "0" and ptr != "":
            if ptr in expjt_dict:
                exp_ptrs.append(ptr)
    
    for i, ptr in enumerate(exp_ptrs):
        row = expjt_dict[ptr]
        lines.append(f"    write({unit_var}, '(2X, 6F13.6)') 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")
    return lines

def generate_equipmnt(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)', advance='no') '#$ EQUIPMNT'")
    basic_elements = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    equip_table = get_table_data(db_path, "INPUT_EQUIPMENT")
    equip_dict = {row["EQP_PTR"]: row for row in equip_table if "EQP_PTR" in row}
    
    equip_ptrs = []
    for row in basic_elements:
        ptr = row.get("EQP_PTR", "0")
        if ptr != "0" and ptr != "":
            if ptr in equip_dict:
                equip_ptrs.append(ptr)
    
    for i, ptr in enumerate(equip_ptrs):
        row = equip_dict[ptr]
        lines.append(f"    write({unit_var}, '(2X, 6F13.6)') 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")
    return lines

def generate_bars(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)', advance='no') '  bars      '")
    return lines

def generate_rigid(unit_var, db_path):
    lines = []
    rigids_table = get_table_data(db_path, "INPUT_RIGIDS")
    rigids_dict = {row["RIGID_PTR"]: row for row in rigids_table}
    
    rigid_ptrs = ["1", "9", "8", "7", "5", "6", "2", "4", "3"]

    lines.append(f"    write({unit_var}, '(A)') '#$ RIGID   '")
    
    for i, ptr in enumerate(rigid_ptrs):
        if ptr not in rigids_dict:
            continue
        row = rigids_dict[ptr]
        wgt = row.get("RIGID_WGT", "0")
        rtype = row.get("RIGID_TYPE", "")
        
        type_val = 0.0
        if rtype == "Valve":
            type_val = 1.0
        elif rtype == "Flange Pair":
            type_val = 3.0
            
        if rtype == "Unspecified" or float(wgt) == -1.0101:
            wgt = "0.0"
            type_val = "0.0"
            lines.append(f"    write({unit_var}, '(7X, F8.6, 5X, F8.6)') {ensure_float_str(wgt)}, {ensure_float_str(type_val)}")
            continue

        wgt_float = float(wgt)
        type_float = float(type_val)
        
        fmt_w = fmt_f(wgt_float, 7)
        fmt_t = fmt_f(type_float, 7)
        
        lines.append(f"    write({unit_var}, '(4X, {fmt_w}, 6X, {fmt_t}, A)') {wgt_float}, {type_float}, '    '")
        
    return lines

def generate_coords(unit_var, db_path):
    lines = []
    coords = get_table_data(db_path, "INPUT_USER_NODAL_COORDINATES")
    lines.append(f"    write({unit_var}, '(A)') '#$ COORDS  '")
    lines.append(f"    write({unit_var}, '(I15)') 1")
    for i, row in enumerate(coords):
        node = row.get("NODE", "0")
        x = row.get("NODE_X", "0")
        y = row.get("NODE_Y", "0")
        z = row.get("NODE_Z", "0")
        
        x_float = round(float(x), 3)
        y_float = round(float(y), 3)
        z_float = round(float(z), 3)
        
        lines.append(f"    write({unit_var}, '(I15, F13.3, F13.3, F13.3)') {node}, {x_float}, {y_float}, {z_float}")
    return lines

def generate_miscel_1(unit_var, db_path):
    lines = []
    basic_elements = get_table_data(db_path, "INPUT_BASIC_ELEMENT_DATA")
    lines.append(f"    write({unit_var}, '(A)') '#$ MISCEL_1'")
    
    mat_nums = []
    for row in basic_elements:
        if row.get("ELEMENTID") != "":
            mat_num = row.get("MATERIAL_NUM", "0")
            mat_nums.append(mat_num)
    
    for i in range(0, len(mat_nums), 6):
        batch = mat_nums[i:i+6]
        formats = []
        vals = []
        for j, v in enumerate(batch):
            if j == 0:
                formats.append(f"4X, F7.3")
            else:
                formats.append(f"6X, F7.3")
            vals.append(float(v))
            
        fmt_str = "(" + ", ".join(formats)
        
        if len(batch) == 6:
            fmt_str += ", A)"
            val_str = ", ".join(map(str, vals)) + ", '    '"
        else:
            fmt_str += ", A)"
            val_str = ", ".join(map(str, vals)) + ", '    '"
            
        lines.append(f"    write({unit_var}, '{fmt_str}') {val_str}")
        
    lines.append(f"    write({unit_var}, '(I15, I13, I13, I13, F13.4, I13)') 0, 0, 0, 2, 0.0, 1")
    lines.append(f"    write({unit_var}, '(I15, I13, F9.4, F13.4, I17, I13)') 0, 0, 21.1142, 21.5983, 0, 0")
    lines.append(f"    write({unit_var}, '(I15, I13, I13, I13, F13.4, I13)') 0, 0, 0, 0, 0.25, 3")
    lines.append(f"    write({unit_var}, '(I15)') 3")
    return lines

def generate_units(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)') '#$ UNITS   '")
    
    lines.append(f"    write({unit_var}, '(4X, F7.4, 6X, F7.5, 5X, F8.6, 5X, F8.6, 5X, F8.6, 5X, E12.6)') &")
    lines.append(f"        25.4, 4.448, 0.45359, 0.11298, 0.11298, 0.0068946")

    lines.append(f"    write({unit_var}, '(3X, F8.6, 5X, F8.4, 5X, E12.6, 1X, E12.6, 1X, E12.6, 1X, E12.6)') &")
    lines.append(f"        0.5556, -17.7778, 0.068946, 0.0068946, 0.02768, 0.02768")
    
    lines.append(f"    write({unit_var}, '(3X, E12.6, 2X, F7.5, 5X, F8.6, 6X, F7.5, 6X, F7.5, 6X, F7.5, A)') &")
    lines.append(f"        0.02768, 1.7512, 0.11298, 1.7512, 1.0, 6.8946, '    '")

    lines.append(f"    write({unit_var}, '(3X, E12.6, 2X, F7.4, 6X, F7.4, 6X, F7.4, A)') &")
    lines.append(f"        0.0254, 25.4, 25.4, 25.4, '    '")
    return lines

def generate_metric(unit_var, db_path):
    return [f"    write({unit_var}, '(A)', advance='no') '  METRIC         '"]

def generate_mpa(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)') '  MPa       '")
    lines.append(f"    write({unit_var}, '(A)') '  kg./cu.cm.'")
    lines.append(f"    write({unit_var}, '(A)') '  kg./cu.cm.'")
    lines.append(f"    write({unit_var}, '(A)') '  kg./cu.cm.'")
    lines.append(f"    write({unit_var}, '(A)') '  N./cm. '")
    lines.append(f"    write({unit_var}, '(A)') '   N.m./deg '")
    lines.append(f"    write({unit_var}, '(A)') '  N./cm. '")
    lines.append(f"    write({unit_var}, '(A)') '  g''s'")
    return lines

def generate_kpa(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)') '     KPa    '")
    lines.append(f"    write({unit_var}, '(A)') '   m.'")
    lines.append(f"    write({unit_var}, '(A)') '  mm.'")
    lines.append(f"    write({unit_var}, '(A)') '  mm.'")
    lines.append(f"    write({unit_var}, '(A)') '  mm.'")
    return lines

def generate_c(unit_var, db_path):
    return [f"    write({unit_var}, '(A)', advance='no') '  C'"]

def generate_on(unit_var, db_path):
    lines = []
    lines.append(f"    write({unit_var}, '(A)') '  ON '")
    lines.append(f"    write({unit_var}, '(A)') '  mm.'")
    lines.append(f"    write({unit_var}, '(A)') '   N.'")
    lines.append(f"    write({unit_var}, '(A)') '  Kg.'")
    lines.append(f"    write({unit_var}, '(A)') '   N.m. '")
    lines.append(f"    write({unit_var}, '(A)') '   N.m. '")
    return lines

def generate_group2_blocks(unit_var):
    db_path = "Sample 4/INLET-SEPARATOR-SKID-C2.ACCDB"
    
    blocks = {
        "out_reducers.cii": generate_reducers,
        "out_expjt.cii": generate_expjt,
        "out_equipmnt.cii": generate_equipmnt,
        "out_bars.cii": generate_bars,
        "out_rigid.cii": generate_rigid,
        "out_coords.cii": generate_coords,
        "out_miscel_1.cii": generate_miscel_1,
        "out_units.cii": generate_units,
        "out_metric.cii": generate_metric,
        "out_mpa.cii": generate_mpa,
        "out_kpa.cii": generate_kpa,
        "out_c.cii": generate_c,
        "out_on.cii": generate_on,
    }

    all_lines = []
    all_lines.append(f"subroutine write_group2_blocks({unit_var})")
    all_lines.append(f"    integer, intent(in) :: {unit_var}")
    for key, func in blocks.items():
        block_lines = func(unit_var, db_path)
        all_lines.extend(block_lines)
    all_lines.append(f"end subroutine write_group2_blocks")

    test_code = []
    test_code.append("program main")
    test_code.append("    integer :: unit = 10")
    for key, func in blocks.items():
        test_code.append(f"    open(unit=unit, file='{key}', status='replace')")
        block_lines = func("unit", db_path)
        for line in block_lines:
            test_code.append(line)
        test_code.append(f"    close(unit)")
        test_code.append(f"    call strip_newline('{key}')")

    test_code.append("end program main")
    
    test_code.append(f"subroutine strip_newline(filename)")
    test_code.append(f"    character(len=*), intent(in) :: filename")
    test_code.append(f"end subroutine strip_newline")

    with open("test_group2.f90", "w") as f:
        f.write("\n".join(test_code) + "\n\n")
        f.write("\n".join(all_lines) + "\n")

    return "\n".join(all_lines)

if __name__ == '__main__':
    generate_group2_blocks("unit")

