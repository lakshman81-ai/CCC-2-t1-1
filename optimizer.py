import pandas as pd
from typing import Dict, Any, List
import copy
from logger import get_logger

logger = get_logger("importer")

def get_boilerplate_cii_data() -> Dict[str, Any]:
    """Generates a skeleton CAESAR II parsed dictionary if no original file is present."""
    # Build 21 blank 75-character lines for title_lines_raw to match typical C2 header length
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
            # Control section has 19 ints. CAESAR II expects 4 lines (3x6, 1x1)
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
    Takes an existing parsed .cii dictionary and merges edits from the provided 41-column CSV.
    Uses the original `base_parsed_data` as the foundation, preserving `REL_RAW`, `IEL_RAW`,
    and `STR_RAW` strings for unchanged values.
    Only modifies the parsed values and strips the RAW string at that specific index if changed.
    If `base_parsed_data` is None, reconstructs entirely from scratch.
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

    # Check if number of elements matches. For this MVP, we assume a 1:1 row mapping.
    # If the CSV has more/fewer rows, we'd need more complex diffing.

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
                # Compare as float (with slightly wider tolerance for float parsing variations from UI)
                orig_val = float(el["REL"][index]) if len(el["REL"]) > index else 0.0
                new_fval = float(new_val)

                # Check absolute difference and relative difference
                diff = abs(new_fval - orig_val)
                # Use a larger tolerance like 1e-4 because CAESAR prints floats like 0.499901E-04
                # which another tool might truncate to 0.00005.
                # We only want to overwrite the exact raw string if it's a REAL edit.
                rel_diff = diff / max(abs(orig_val), 1e-9)
                if diff > 1e-4 and rel_diff > 1e-3:
                    # Value changed! Update it.
                    while len(el["REL"]) <= index: el["REL"].append(0.0)
                    el["REL"][index] = new_fval

                    # We need to invalidate the RAW string for the line containing this value.
                    # REL values are printed 6 per line.
                    line_idx = index // 6
                    if "REL_RAW" in el and len(el["REL_RAW"]) > line_idx:
                        el["REL_RAW"][line_idx] = None  # None signals the serializer to re-format this line
            except Exception as e:
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
            except Exception as e:
                pass

        def update_str(index, new_val):
            try:
                if pd.isna(new_val):
                    return
                new_str_val = str(new_val)
                # Ignore empty strings during merge if they weren't explicitly edited to be empty
                if not new_str_val.strip() and index == 1 and str(row.get("PIPELINE-REFERENCE", "")) == "":
                    return

                orig_val = el["STR"][index] if len(el["STR"]) > index else ""
                if new_str_val != orig_val:
                    while len(el["STR"]) <= index: el["STR"].append("")
                    el["STR"][index] = new_str_val
                    line_idx = index // 6
                    if "STR_RAW" in el and len(el["STR_RAW"]) > line_idx:
                        el["STR_RAW"][line_idx] = None
            except Exception as e:
                pass

        # Parse CSV values
        text = str(row.get("TEXT", ""))
        nodes = text.split(" ")[-1].split("-") if " " in text and "-" in text else ["0", "0"]
        try:
            update_rel(0, float(nodes[0]))
            update_rel(1, float(nodes[1]))
        except:
            pass

        update_rel(2, row.get("DELTA_X"))
        update_rel(3, row.get("DELTA_Y"))
        update_rel(4, row.get("DELTA_Z"))

        update_rel(5, row.get("DIAMETER"))
        update_rel(6, row.get("WALL_THICK"))

        if "PIPELINE-REFERENCE" in row and not pd.isna(row["PIPELINE-REFERENCE"]):
            update_str(1, row["PIPELINE-REFERENCE"])

        for ptr_name, idx_iel in [("BEND_PTR", 0), ("RIGID_PTR", 1), ("INT_PTR", 10)]:
            val = row.get(ptr_name)
            update_iel(idx_iel, val)

        comp_type = str(row.get("Type", ""))
        if comp_type == "Support":
            update_iel(3, 1) # Restraint pointer generic fallback

        # Parse robust generic backup columns if present
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

    # --- STANDALONE FALLBACK FIX ---
    # If the original file was not provided, we need to ensure the aux_data tables
    # have at least as many dummy records as the maximum pointer found in the elements,
    # otherwise CAESAR II will crash (Error processing CONTROL section).
    # Typical IEL pointer mapping:
    ptr_map = {
        0: "BEND", 1: "RIGID", 2: "EXPJT", 3: "RESTRANT",
        4: "DISPLMNT", 5: "FORCMNT", 6: "UNIFORM", 7: "WIND",
        10: "SIF&TEES", 13: "FLANGES", 14: "REDUCERS"
        # Others can be added if needed
    }

    # Find max pointers
    max_ptrs = {k: 0 for k in ptr_map.values()}
    for el in new_elements:
        for iel_idx, aux_key in ptr_map.items():
            ptr_val = int(el["IEL"][iel_idx]) if len(el["IEL"]) > iel_idx else 0
            if ptr_val > max_ptrs[aux_key]:
                max_ptrs[aux_key] = ptr_val

    # Create dummy records if missing
    if is_standalone:
        for aux_key, max_ptr in max_ptrs.items():
            if aux_key not in base_parsed_data["aux_data"]:
                base_parsed_data["aux_data"][aux_key] = []

            # Since standlone data starts empty, we just append enough dummy lines
            current_len = len(base_parsed_data["aux_data"][aux_key])
            while current_len < max_ptr:
                # We just append a blank dummy line block or a generic formatted string
                # CAESAR II requires specific formatting per aux type. The safest fallback
                # for a purely standalone generated file is to let the user know it's missing,
                # but to prevent a total crash, we write an empty line or generic float line.
                base_parsed_data["aux_data"][aux_key].append(["       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000"])
                current_len += 1

    # Update control array counts for these dummy generations
    # CAESAR II counts_raw is typically 19 integers.
    # We will let the serializer format them dynamically if counts_raw is missing,
    # or we can patch the specific indexes if we're using boilerplate.
    if is_standalone:
        # We need to construct a proper integer array for `aux_counts`
        # 0:NUMNOZ, 1:NOHGRS, 2:NONAM, 3:NORED, 4:NUMFLG, 5:NUMBND, 6:NUMRIG, 7:NUMEXP, 8:NUMRES, 9:NUMDIS, 10:NUMFOR, 11:NUMUNI, 12:NUMWIN
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
            0, 0, # OFFSETS, ALLOWBLS (no direct pointer usually in this array context, but let's pad)
            max_ptrs.get("SIF&TEES", 0),
            max_ptrs.get("REDUCERS", 0),
            max_ptrs.get("FLANGES", 0)
        ]
        # Force serializer to use the dynamic array instead of boilerplate counts_raw
        if "counts_raw" in base_parsed_data["control"]:
            del base_parsed_data["control"]["counts_raw"]

    logger.info(f"[IMPORT] Successfully merged {len(new_elements)} elements from CSV.")
    return base_parsed_data
