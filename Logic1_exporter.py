"""
Logic1_exporter.py — Exports parsed CII data to 41-column CSV for Logic 1.
Ported from P1 exporter.py. Change: logger import uses Logic1_logger.
"""
import csv
import pandas as pd
from typing import List, Dict, Any, Tuple
from Logic1_logger import get_logger

logger = get_logger("Logic1_exporter")


def extract_guid_for_restraint(rest_ptr: int, restraint_block: List[List[str]]) -> str:
    if rest_ptr <= 0 or not restraint_block:
        return ""
    idx = rest_ptr - 1
    if idx < len(restraint_block):
        record = restraint_block[idx]
        for line in record:
            if len(line) > 13:
                try:
                    str_len = int(line[7:12].strip())
                    if str_len > 0 and len(line) > 13:
                        text = line[13:13+str_len].strip()
                        if text:
                            return text
                except ValueError:
                    pass
    return ""


def get_starting_coords(coords_block: List[Dict[str, float]]) -> Tuple[float, float, float]:
    if coords_block and len(coords_block) > 0:
        first = coords_block[0]
        return first.get('x', 0.0), first.get('y', 0.0), first.get('z', 0.0)
    return 0.0, 0.0, 0.0


def generate_custom_csv(parsed_data: Dict[str, Any], output_path: str = None) -> pd.DataFrame:
    logger.info(f"[EXPORT] Logic1: Exporting CSV...")

    columns = [
        "#", "CSV SEQ NO", "Type", "TEXT", "PIPELINE-REFERENCE", "REF NO.", "BORE",
        "EP1 COORDS", "EP2 COORDS", "CP COORDS", "BP COORDS", "SKEY", "SUPPORT COOR",
        "SUPPORT GUID", "CA 1", "CA 2", "CA 3", "CA 4", "CA 5", "CA 6", "CA 7",
        "CA 8", "CA 9", "CA 10", "CA 97", "CA 98", "Fixing Action", "LEN 1", "AXIS 1",
        "LEN 2", "AXIS 2", "LEN 3", "AXIS 3", "BRLEN", "DELTA_X", "DELTA_Y", "DELTA_Z",
        "DIAMETER", "WALL_THICK", "BEND_PTR", "RIGID_PTR", "INT_PTR"
    ]
    for i in range(98):
        columns.append(f"REL_{i:02d}")
    for i in range(18):
        columns.append(f"IEL_{i:02d}")

    parsed_elements = parsed_data.get("elements", [])
    coords_block = parsed_data.get("coords", [])
    aux_data = parsed_data.get("aux_data", {})
    restraint_block = aux_data.get("RESTRANT", [])

    rows = []
    running_idx = 1
    seq_idx = 1

    current_x, current_y, current_z = get_starting_coords(coords_block)

    for idx, el in enumerate(parsed_elements):
        row = {col: "" for col in columns}

        rel = el.get('REL', [])
        iel = el.get('IEL', [])

        if len(rel) < 8:
            continue

        from_node = rel[0]
        to_node = rel[1]
        dx = rel[2]
        dy = rel[3]
        dz = rel[4]
        diameter = rel[5]
        wall_thk = rel[6]

        bend_ptr = iel[0] if len(iel) > 0 else 0
        rigid_ptr = iel[1] if len(iel) > 1 else 0
        rest_ptr = iel[3] if len(iel) > 3 else 0
        int_ptr = iel[10] if len(iel) > 10 else 0
        flange_ptr = iel[13] if len(iel) > 13 else 0

        ep1 = (current_x, current_y, current_z)
        current_x += dx
        current_y += dy
        current_z += dz
        ep2 = (current_x, current_y, current_z)
        cp = ((ep1[0]+ep2[0])/2, (ep1[1]+ep2[1])/2, (ep1[2]+ep2[2])/2)

        comp_type = "Pipe"
        if bend_ptr > 0: comp_type = "Bend"
        elif int_ptr > 0: comp_type = "Tee/Olet"
        elif flange_ptr > 0: comp_type = "Flange"
        elif rest_ptr > 0: comp_type = "Support"
        elif rigid_ptr > 0: comp_type = "Rigid"

        if dx != 0:
            row["LEN 1"] = abs(dx)
            row["AXIS 1"] = "East" if dx > 0 else "West"
        if dy != 0:
            row["LEN 2"] = abs(dy)
            row["AXIS 2"] = "Up" if dy > 0 else "Down"
        if dz != 0:
            row["LEN 3"] = abs(dz)
            row["AXIS 3"] = "North" if dz > 0 else "South"

        row["#"] = running_idx
        row["CSV SEQ NO"] = seq_idx
        row["Type"] = comp_type
        row["TEXT"] = f"{comp_type} {int(from_node)}-{int(to_node)}"
        row["PIPELINE-REFERENCE"] = el.get('STR', ["", ""])[1] if len(el.get('STR', [])) > 1 else ""
        row["BORE"] = diameter
        row["DIAMETER"] = diameter
        row["WALL_THICK"] = wall_thk
        row["DELTA_X"] = dx
        row["DELTA_Y"] = dy
        row["DELTA_Z"] = dz
        row["EP1 COORDS"] = f"({ep1[0]},{ep1[1]},{ep1[2]})"
        row["EP2 COORDS"] = f"({ep2[0]},{ep2[1]},{ep2[2]})"
        row["CP COORDS"] = f"({cp[0]},{cp[1]},{cp[2]})"
        row["BEND_PTR"] = bend_ptr
        row["RIGID_PTR"] = rigid_ptr
        row["INT_PTR"] = int_ptr

        if rest_ptr > 0:
            row["SUPPORT GUID"] = extract_guid_for_restraint(rest_ptr, restraint_block)
            row["SUPPORT COOR"] = row["EP2 COORDS"]

        for i, val in enumerate(rel):
            row[f"REL_{i:02d}"] = val
        for i, val in enumerate(iel):
            row[f"IEL_{i:02d}"] = val

        running_idx += 1
        seq_idx += 1
        rows.append(row)

    df = pd.DataFrame(rows)
    if output_path:
        df.to_csv(output_path, index=False)
        logger.info(f"[EXPORT] Logic1: CSV exported to {output_path}")
    return df
