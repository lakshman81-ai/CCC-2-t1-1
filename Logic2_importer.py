import pandas as pd
from typing import Dict, Any, List
import copy
import logging

logger = logging.getLogger("Logic2_importer")

# ── Per-type aux_data record templates (Fix 2.1) ─────────────────────────────
# Each aux_key maps to the correct multi-line record structure for CAESAR II.
_AUX_TEMPLATES: Dict[str, List[str]] = {
    "BEND": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000"
    ],
    "RIGID": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000"
    ],
    "EXPJT": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000"
    ],
    "RESTRANT": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000     0.000000",
        "           0 ",
        "           0 "
    ],
    "SIF&TEES": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000"
    ],
    "FLANGES": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000     0.000000",
        "           0 "
    ],
    "REDUCERS": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000",
        "     0.000000"
    ],
    "_DEFAULT": [
        "     0.000000     0.000000     0.000000     0.000000     0.000000     0.000000"
    ]
}

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

def reconstruct_from_csv(csv_path: str, base_parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an existing parsed .cii dictionary and merges edits from the provided CSV.
    Accepts a DataFrame or a file path string.
    """
    logger.info(f"[IMPORT] Merging elements from CSV table...")

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
                if pd.isna(new_val) or new_val == "":
                    return
                orig_val = float(el["REL"][index]) if len(el["REL"]) > index else 0.0
                new_fval = float(new_val)
                diff = abs(new_fval - orig_val)
                rel_diff = diff / max(abs(orig_val), 1e-9)
                if diff > 1e-4 and rel_diff > 1e-3:
                    while len(el["REL"]) <= index: el["REL"].append(0.0)
                    el["REL"][index] = new_fval
                    line_idx = index // 6
                    if "REL_RAW" in el and len(el["REL_RAW"]) > line_idx:
                        el["REL_RAW"][line_idx] = None
            except Exception:
                pass

        def update_iel(index, new_val):
            try:
                if pd.isna(new_val):
                    return
                orig_val = int(el["IEL"][index]) if len(el["IEL"]) > index else 0
                if int(new_val) != orig_val:
                    while len(el["IEL"]) <= index: el["IEL"].append(0)
                    el["IEL"][index] = int(new_val)
                    line_idx = index // 6
                    if "IEL_RAW" in el and len(el["IEL_RAW"]) > line_idx:
                        el["IEL_RAW"][line_idx] = None
            except Exception:
                pass

        def update_str(index, new_val):
            try:
                if pd.isna(new_val):
                    return
                new_str_val = str(new_val)
                if not new_str_val.strip() and index == 1 and str(row.get("PIPELINE-REFERENCE", "")) == "":
                    return
                orig_val = el["STR"][index] if len(el["STR"]) > index else ""
                if new_str_val != orig_val:
                    while len(el["STR"]) <= index: el["STR"].append("")
                    el["STR"][index] = new_str_val
                    line_idx = index // 6
                    if "STR_RAW" in el and len(el["STR_RAW"]) > line_idx:
                        el["STR_RAW"][line_idx] = None
            except Exception:
                pass

        # FROM_NODE / TO_NODE (ACCDB format)
        from_node_direct = row.get("FROM_NODE")
        to_node_direct = row.get("TO_NODE")
        if from_node_direct is not None and not pd.isna(from_node_direct):
            update_rel(0, float(from_node_direct))
        if to_node_direct is not None and not pd.isna(to_node_direct):
            update_rel(1, float(to_node_direct))

        # Fallback: parse FROM/TO from TEXT column, but only when direct columns
        # are absent. Avoid defaulting to 0-0, which can overwrite valid nodes.
        if (
            (from_node_direct is None or pd.isna(from_node_direct))
            and (to_node_direct is None or pd.isna(to_node_direct))
        ):
            text = str(row.get("TEXT", ""))
            if "-" in text:
                tail = text.strip().split()[-1]
                nodes = tail.split("-")
                if len(nodes) == 2:
                    try:
                        update_rel(0, float(nodes[0]))
                        update_rel(1, float(nodes[1]))
                    except Exception:
                        pass

        update_rel(2, row.get("DELTA_X"))
        update_rel(3, row.get("DELTA_Y"))
        update_rel(4, row.get("DELTA_Z"))
        update_rel(5, row.get("DIAMETER"))
        update_rel(6, row.get("WALL_THICK"))

        # Fix 2.2: extended REL column mappings (confirmed ACCDB column names)
        update_rel(7,  row.get("INSUL_THICK"))
        update_rel(8,  row.get("CORR_ALLOW"))
        for _i, _col in enumerate(["TEMP_EXP_C1","TEMP_EXP_C2","TEMP_EXP_C3",
                                    "TEMP_EXP_C4","TEMP_EXP_C5","TEMP_EXP_C6"]):
            update_rel(9 + _i, row.get(_col))
        for _i, _col in enumerate(["PRESSURE1","PRESSURE2","PRESSURE3"]):
            update_rel(15 + _i, row.get(_col))
        update_rel(18, row.get("MODULUS"))
        update_rel(19, row.get("POISSONS"))
        update_rel(20, row.get("PIPE_DENSITY"))
        update_rel(21, row.get("INSUL_DENSITY"))
        update_rel(22, row.get("FLUID_DENSITY"))

        if "PIPELINE-REFERENCE" in row and not pd.isna(row["PIPELINE-REFERENCE"]):
            update_str(1, row["PIPELINE-REFERENCE"])
        else:
            for accdb_ref_col in ["ELEMENT_NAME", "LINE_NO", "FROM_NODE_NAME"]:
                val = row.get(accdb_ref_col)
                if val is not None and not pd.isna(val) and str(val).strip():
                    update_str(1, str(val))
                    break

        # All confirmed IEL pointer mappings
        accdb_ptr_map = [
            ("BEND_PTR",     0),
            ("RIGID_PTR",    1),
            ("EXPJ_PTR",     2),
            ("REST_PTR",     3),
            ("DISP_PTR",     4),
            ("FORCMNT_PTR",  5),
            ("ULOAD_PTR",    6),
            ("WLOAD_PTR",    7),
            ("EOFF_PTR",     8),   # Fix 2.NEW: element offsets
            ("ALLOW_PTR",    9),
            ("INT_PTR",     10),
            ("FLANGE_PTR",  13),
            ("REDUCER_PTR", 14),
            ("HGR_PTR",     15),   # Fix 2.NEW: hanger pointer
            ("NOZ_PTR",     16),   # Fix 2.NEW: nozzle pointer
        ]
        for accdb_col, iel_idx in accdb_ptr_map:
            val = row.get(accdb_col)
            if val is not None and not pd.isna(val):
                update_iel(iel_idx, val)

        # Fix 2.NEW: MATERIAL_NUM → IEL[11]
        mat_num = row.get("MATERIAL_NUM")
        if mat_num is not None and not pd.isna(mat_num):
            update_iel(11, int(float(mat_num)))

        comp_type = str(row.get("Type", ""))
        if comp_type == "Support":
            update_iel(3, 1)

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
        for aux_key, max_ptr in max_ptrs.items():
            if aux_key not in base_parsed_data["aux_data"]:
                base_parsed_data["aux_data"][aux_key] = []

            # Fix 2.1: use per-type templates (correct line count per record)
            template = _AUX_TEMPLATES.get(aux_key, _AUX_TEMPLATES["_DEFAULT"])
            current_len = len(base_parsed_data["aux_data"][aux_key])
            while current_len < max_ptr:
                base_parsed_data["aux_data"][aux_key].append(list(template))
                current_len += 1

    if is_standalone:
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

    logger.info(f"[IMPORT] Successfully merged {len(new_elements)} elements from CSV.")
    return base_parsed_data
