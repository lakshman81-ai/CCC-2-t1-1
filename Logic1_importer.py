"""
Logic1_importer.py — CAESAR II CSV→parsed_data importer for Logic 1.
Ported from P1 importer.py. Change: logger import uses Logic1_logger.
"""
import pandas as pd
from typing import Dict, Any, List
import copy
from Logic1_logger import get_logger

logger = get_logger("Logic1_importer")


def get_boilerplate_cii_data() -> Dict[str, Any]:
    """Generates a skeleton CAESAR II parsed dictionary if no original file is present."""
    title_lines = [" " * 75 for _ in range(21)]
    title_lines[0] = "    PROJECT:                                                               "
    title_lines[2] = "    CLIENT :                                                               "
    title_lines[4] = "    ANALYST:                                                               "
    title_lines[6] = "    NOTES  :                                                               "

    return {
        "version": {
            "VERSION": [5.0, 11.0],
            "GVERSION_RAW": "    5.00000      11.0000        1256",
            "title_lines_raw": title_lines
        },
        "control": {
            "NUMELT": 0,
            "counts_raw": [
                "           0           0           0           0           0           0",
                "           0           0           0           0           0           0",
                "           0           0           0           0           0           0",
                "           0"
            ]
        },
        "elements": [],
        "aux_data": {
            "BEND": [], "RIGID": [], "EXPJT": [], "RESTRANT": [], "DISPLMNT": [],
            "FORCMNT": [], "UNIFORM": [], "WIND": [], "OFFSETS": [], "ALLOWBLS": [],
            "SIF&TEES": [], "REDUCERS": [], "FLANGES": [], "EQUIPMNT": []
        }
    }


def reconstruct_from_csv(csv_path, base_parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges edits from a CSV into an existing parsed .cii dictionary.
    Accepts a DataFrame or a file path string.
    """
    logger.info("[IMPORT] Logic1: Merging elements from CSV table...")

    try:
        if isinstance(csv_path, pd.DataFrame):
            df = csv_path
        else:
            df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"[IMPORT] Failed to read CSV: {e}")
        return base_parsed_data if base_parsed_data else get_boilerplate_cii_data()

    is_standalone = False
    if not base_parsed_data:
        base_parsed_data = get_boilerplate_cii_data()
        is_standalone = True

    original_elements = base_parsed_data.get("elements", [])
    new_elements = []

    for idx, row in df.iterrows():
        if idx < len(original_elements):
            el = copy.deepcopy(original_elements[idx])
        else:
            el = {
                "REL": [0.0] * 98,
                "IEL": [0] * 18,
                "STR": ["", ""],
                "REL_RAW": [],
                "IEL_RAW": [],
                "STR_RAW": []
            }

        def update_rel(index, new_val):
            try:
                if new_val is None or (hasattr(new_val, '__class__') and pd.isna(new_val)) or new_val == "":
                    return
                orig_val = float(el["REL"][index]) if len(el["REL"]) > index else 0.0
                new_fval = float(new_val)
                diff = abs(new_fval - orig_val)
                rel_diff = diff / max(abs(orig_val), 1e-9)
                if diff > 1e-4 and rel_diff > 1e-3:
                    while len(el["REL"]) <= index:
                        el["REL"].append(0.0)
                    el["REL"][index] = new_fval
                    line_idx = index // 6
                    if "REL_RAW" in el and len(el["REL_RAW"]) > line_idx:
                        el["REL_RAW"][line_idx] = None
            except Exception:
                pass

        def update_iel(index, new_val):
            try:
                if new_val is None or (hasattr(new_val, '__class__') and pd.isna(new_val)):
                    return
                orig_val = int(el["IEL"][index]) if len(el["IEL"]) > index else 0
                if int(float(new_val)) != orig_val:
                    while len(el["IEL"]) <= index:
                        el["IEL"].append(0)
                    el["IEL"][index] = int(float(new_val))
                    line_idx = index // 6
                    if "IEL_RAW" in el and len(el["IEL_RAW"]) > line_idx:
                        el["IEL_RAW"][line_idx] = None
            except Exception:
                pass

        def update_str(index, new_val):
            try:
                if new_val is None or (hasattr(new_val, '__class__') and pd.isna(new_val)):
                    return
                new_str_val = str(new_val)
                orig_val = el["STR"][index] if len(el["STR"]) > index else ""
                if new_str_val != orig_val:
                    while len(el["STR"]) <= index:
                        el["STR"].append("")
                    el["STR"][index] = new_str_val
                    if "STR_RAW" in el and len(el["STR_RAW"]) > index:
                        el["STR_RAW"][index] = None
            except Exception:
                pass

        # FROM_NODE / TO_NODE
        update_rel(0, row.get("FROM_NODE"))
        update_rel(1, row.get("TO_NODE"))

        # Geometry (dual-column name support: ACCDB names take priority, P1 names as fallback)
        update_rel(2, row.get("DELTA_X", row.get("DX")))
        update_rel(3, row.get("DELTA_Y", row.get("DY")))
        update_rel(4, row.get("DELTA_Z", row.get("DZ")))
        update_rel(5, row.get("DIAMETER"))
        update_rel(6, row.get("WALL_THICK", row.get("THICKNESS")))
        update_rel(7, row.get("INSUL_THICK", row.get("INSULATION")))
        update_rel(8, row.get("CORR_ALLOW", row.get("CORROSION")))

        # Thermal
        for i, col in enumerate(["TEMP_EXP_C1","TEMP_EXP_C2","TEMP_EXP_C3",
                                   "TEMP_EXP_C4","TEMP_EXP_C5","TEMP_EXP_C6"]):
            update_rel(9 + i, row.get(col))

        # Pressure
        for i, col in enumerate(["PRESSURE1","PRESSURE2","PRESSURE3"]):
            update_rel(15 + i, row.get(col))

        # Material properties
        update_rel(18, row.get("MODULUS"))
        update_rel(19, row.get("POISSONS"))
        update_rel(20, row.get("PIPE_DENSITY", row.get("DENSITY")))
        update_rel(21, row.get("INSUL_DENSITY"))
        update_rel(22, row.get("FLUID_DENSITY"))

        # String (pipeline reference / element name)
        for accdb_ref_col in ["PIPELINE-REFERENCE", "ELEMENT_NAME", "LINE_NO", "FROM_NODE_NAME"]:
            val = row.get(accdb_ref_col)
            if val is not None and str(val).strip() and str(val) not in ("None", "nan"):
                update_str(1, str(val))
                break

        # IEL pointer mapping — all confirmed slots
        iel_ptr_map = [
            ("BEND_PTR",     0),
            ("RIGID_PTR",    1),
            ("EXPJ_PTR",     2),
            ("REST_PTR",     3),
            ("DISP_PTR",     4),
            ("FORCMNT_PTR",  5),
            ("ULOAD_PTR",    6),
            ("WLOAD_PTR",    7),
            ("EOFF_PTR",     8),
            ("ALLOW_PTR",    9),
            ("INT_PTR",     10),
            ("FLANGE_PTR",  13),
            ("REDUCER_PTR", 14),
            ("HGR_PTR",     15),
            ("NOZ_PTR",     16),
        ]
        for col, idx in iel_ptr_map:
            update_iel(idx, row.get(col))

        # MATERIAL_NUM → IEL[11]
        update_iel(11, row.get("MATERIAL_NUM"))

        # Generic fallback columns
        for i in range(98):
            col_name = f"REL_{i:02d}"
            if col_name in row and not pd.isna(row[col_name]):
                update_rel(i, row[col_name])
        for i in range(18):
            col_name = f"IEL_{i:02d}"
            if col_name in row and not pd.isna(row[col_name]):
                update_iel(i, row[col_name])

        new_elements.append(el)

    base_parsed_data["elements"] = new_elements
    base_parsed_data["control"]["NUMELT"] = len(new_elements)

    ptr_map = {
        0: "BEND", 1: "RIGID", 2: "EXPJT", 3: "RESTRANT",
        4: "DISPLMNT", 5: "FORCMNT", 6: "UNIFORM", 7: "WIND",
        10: "SIF&TEES", 13: "FLANGES", 14: "REDUCERS"
    }

    max_ptrs = {k: 0 for k in ptr_map.values()}
    for el in new_elements:
        for iel_idx, aux_key in ptr_map.items():
            ptr_val = int(el["IEL"][iel_idx]) if len(el["IEL"]) > iel_idx else 0
            if ptr_val > max_ptrs[aux_key]:
                max_ptrs[aux_key] = ptr_val

    if is_standalone:
        from Logic2_importer import _AUX_TEMPLATES
        for aux_key, max_ptr in max_ptrs.items():
            if aux_key not in base_parsed_data["aux_data"]:
                base_parsed_data["aux_data"][aux_key] = []
            current_len = len(base_parsed_data["aux_data"][aux_key])
            template = _AUX_TEMPLATES.get(aux_key, _AUX_TEMPLATES["_DEFAULT"])
            while current_len < max_ptr:
                base_parsed_data["aux_data"][aux_key].append(list(template))
                current_len += 1

        base_parsed_data["control"]["NUMNOZ"] = 0
        base_parsed_data["control"]["NOHGRS"] = 0
        base_parsed_data["control"]["NONAM"] = 0
        base_parsed_data["control"]["NORED"] = max_ptrs.get("REDUCERS", 0)
        base_parsed_data["control"]["NUMFLG"] = max_ptrs.get("FLANGES", 0)

        base_parsed_data["control"]["aux_counts"] = [
            max_ptrs.get("BEND", 0),
            max_ptrs.get("RIGID", 0),
            max_ptrs.get("EXPJT", 0),
            max_ptrs.get("RESTRANT", 0),
            max_ptrs.get("DISPLMNT", 0),
            max_ptrs.get("FORCMNT", 0),
            max_ptrs.get("UNIFORM", 0),
            max_ptrs.get("WIND", 0),
            0, 0,
            max_ptrs.get("SIF&TEES", 0),
            max_ptrs.get("REDUCERS", 0),
            max_ptrs.get("FLANGES", 0)
        ]
        if "counts_raw" in base_parsed_data["control"]:
            del base_parsed_data["control"]["counts_raw"]

    logger.info(f"[IMPORT] Logic1: Merged {len(new_elements)} elements.")
    return base_parsed_data
