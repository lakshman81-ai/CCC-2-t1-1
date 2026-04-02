"""
Logic4_pipeline.py — Hybrid CII Generator (Logic 4).

Combines:
  - Logic 2: Full element pipeline (15-pointer IEL, RAW string preservation,
              smart diff merge, Logic2_serializer)
  - Logic 1: Real aux_data generation from all 4 ACCDB tables (BEND, RESTRANT,
              RIGID, SIF&TEES), ALLOWBLS defaults
  - Logic 3: Browser mdb-reader extraction (handled in JS; Python receives dicts)

Universal CSV:
  - build_universal_csv() exports a ~130-column element-centric CSV with all
    ACCDB columns + BND_/RST_/RGD_/SIF_ prefixed joined columns.
  - That CSV can be re-fed to build_hybrid_cii() directly (no ACCDB needed).
"""

import pandas as pd
from typing import Dict, Any, List, Optional

# Reuse Logic 2 pipeline
from Logic2_importer import reconstruct_from_csv, get_boilerplate_cii_data
from Logic2_serializer import CIISerializer, SerializerSettings
from Logic2_parser import CIIParser, ParserSettings

import logging
logger = logging.getLogger("Logic4_pipeline")


# ─── Public API ───────────────────────────────────────────────────────────────

def build_hybrid_cii(
    elem_df: pd.DataFrame,
    bend_rows: Optional[List[Dict]] = None,
    rest_rows: Optional[List[Dict]] = None,
    rigid_rows: Optional[List[Dict]] = None,
    sif_rows: Optional[List[Dict]] = None,
    base_parsed_data: Optional[Dict] = None,
    use_dos_newlines: bool = True
) -> str:
    try:
        import js
        sentinel_val = float(js.document.getElementById('l4-setting-sentinel').value)
    except:
        sentinel_val = -1.0101
    """
    Hybrid CII generation.

    Args:
        elem_df: DataFrame from INPUT_BASIC_ELEMENT_DATA (or universal CSV)
        bend_rows:  list of dicts from INPUT_BENDS (optional)
        rest_rows:  list of dicts from INPUT_RESTRAINTS (optional)
        rigid_rows: list of dicts from INPUT_RIGIDS (optional)
        sif_rows:   list of dicts from INPUT_SIFTEES (optional)
        base_parsed_data: parsed .CII dict for merge mode (optional)
        use_dos_newlines: CRLF (True) or LF (False)

    Returns:
        CII file content as string
    """
    logger.info(f"[L4] build_hybrid_cii: {len(elem_df)} elements, "
                f"bends={len(bend_rows or [])}, rests={len(rest_rows or [])}, "
                f"rigids={len(rigid_rows or [])}, sifs={len(sif_rows or [])}")

    # ── STEP 1: Build elements via Logic 2 pipeline ───────────────────────────
    parsed_data = reconstruct_from_csv(elem_df, base_parsed_data)

    # ── STEP 2: Build real aux_data from ACCDB table rows ─────────────────────
    aux_data = parsed_data.get("aux_data", {})

    if bend_rows:
        aux_data["BEND"] = [format_bend_records(bend_rows, sentinel_val=sentinel_val)]

    if rigid_rows:
        aux_data["RIGID"] = [format_rigid_records(rigid_rows, sentinel_val=sentinel_val)]

    aux_data["EXPJT"] = aux_data.get("EXPJT", [[]])

    if rest_rows:
        aux_data["RESTRANT"] = [format_restrant_records(rest_rows, sentinel_val=sentinel_val)]

    # Always write ALLOWBLS standard defaults
    if not aux_data.get("ALLOWBLS"):
        aux_data["ALLOWBLS"] = [get_default_allowbls_block()]

    if sif_rows:
        aux_data["SIF&TEES"] = [format_sif_records(sif_rows, sentinel_val=sentinel_val)]

    parsed_data["aux_data"] = aux_data

    # ── STEP 3: Patch CONTROL counts with real record counts ──────────────────
    # Prefer pointer-derived maxima from generated elements so counts track
    # the actual model and don't inherit benchmark/base-file coupling.
    ctrl = parsed_data.get("control", {})
    nb = _max_iel_ptr(parsed_data, 0) or _count_from_aux(aux_data, "BEND", 3)
    nrg = _max_iel_ptr(parsed_data, 1) or _count_from_aux(aux_data, "RIGID", 3)
    nexp = _max_iel_ptr(parsed_data, 2) or _count_from_aux(aux_data, "EXPJT", 2)
    nr = _max_iel_ptr(parsed_data, 3) or _count_from_aux(aux_data, "RESTRANT", 4)
    ndisp = _max_iel_ptr(parsed_data, 4) or _count_from_aux(aux_data, "DISPLMNT", 1)
    nfor = _max_iel_ptr(parsed_data, 5) or _count_from_aux(aux_data, "FORCMNT", 1)
    nuniform = _max_iel_ptr(parsed_data, 6) or _count_from_aux(aux_data, "UNIFORM", 1)
    nwind = _max_iel_ptr(parsed_data, 7) or _count_from_aux(aux_data, "WIND", 1)
    noff = _max_iel_ptr(parsed_data, 8) or _count_from_aux(aux_data, "OFFSETS", 1)
    nallow = _max_iel_ptr(parsed_data, 9) or _count_from_aux(aux_data, "ALLOWBLS", 1)
    ns = _max_iel_ptr(parsed_data, 10) or _count_from_aux(aux_data, "SIF&TEES", 2)
    nred = _max_iel_ptr(parsed_data, 14) or _count_from_aux(aux_data, "REDUCERS", 2)
    nflg = _max_iel_ptr(parsed_data, 13) or _count_from_aux(aux_data, "FLANGES", 3)

    ctrl["aux_counts"] = [
        nb,   # NUMBND
        nrg,  # NUMRIG
        nexp, # NUMEXP
        nr,   # NUMRES
        ndisp, nfor, nuniform, nwind, noff, nallow,  # DISP,FORC,UNI,WIND,OFF,ALLOW
        ns,   # NUMSIF
        nred, nflg  # REDUCERS, FLANGES
    ]
    # Force dynamic formatting (remove raw caches)
    ctrl.pop("counts_raw", None)
    ctrl.pop("aux_counts_raw", None)
    parsed_data["control"] = ctrl

    # ── STEP 4: Serialize ─────────────────────────────────────────────────────
    s_settings = SerializerSettings(use_dos_newlines=use_dos_newlines)
    serializer = CIISerializer(s_settings)
    result = serializer.serialize(parsed_data)
    logger.info(f"[L4] CII serialized: {len(result)} bytes")
    return result


def build_universal_csv(
    elem_df: pd.DataFrame,
    bend_rows: Optional[List[Dict]] = None,
    rest_rows: Optional[List[Dict]] = None,
    rigid_rows: Optional[List[Dict]] = None,
    sif_rows: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    """
    Build the universal ~130-column intermediate CSV.

    Element-centric: one row per element.
    Aux data is joined via pointer and denormalized with prefixes:
      BND_ → INPUT_BENDS
      RST_ → INPUT_RESTRAINTS
      RGD_ → INPUT_RIGIDS
      SIF_ → INPUT_SIFTEES (joined via INT_PTR = SIF_PTR)
    """

    # Index aux rows by their pointer column for O(1) lookup
    bend_idx  = {int(float(r.get("BEND_PTR",  0))): r for r in (bend_rows  or [])}
    rest_idx  = {int(float(r.get("REST_PTR",  0))): r for r in (rest_rows  or [])}
    rigid_idx = {int(float(r.get("RIGID_PTR", 0))): r for r in (rigid_rows or [])}
    sif_idx   = {int(float(r.get("SIF_PTR",   0))): r for r in (sif_rows   or [])}

    rows_out = []

    for _, elem in elem_df.iterrows():
        row = {}

        # ── SECTION 1: Element identity ───────────────────────────────────────
        for col in ["ELEMENTID","FROM_NODE","TO_NODE","FROM_NODE_NAME",
                    "TO_NODE_NAME","LINE_NO","ELEMENT_NAME"]:
            row[col] = _safe(elem.get(col))

        # ── SECTION 2: Geometry ───────────────────────────────────────────────
        for col in ["DELTA_X","DELTA_Y","DELTA_Z","DIAMETER","WALL_THICK",
                    "INSUL_THICK","CORR_ALLOW"]:
            row[col] = _safe(elem.get(col))

        # ── SECTION 3: Thermal (9 cases) ──────────────────────────────────────
        for i in range(1, 10):
            row[f"TEMP_EXP_C{i}"] = _safe(elem.get(f"TEMP_EXP_C{i}"))

        # ── SECTION 4: Pressure (9 + hydro) ──────────────────────────────────
        for i in range(1, 10):
            row[f"PRESSURE{i}"] = _safe(elem.get(f"PRESSURE{i}"))
        row["HYDRO_PRESSURE"] = _safe(elem.get("HYDRO_PRESSURE"))

        # ── SECTION 5: Material properties ───────────────────────────────────
        row["MODULUS"]   = _safe(elem.get("MODULUS"))
        for i in range(1, 10):
            row[f"HOT_MOD{i}"] = _safe(elem.get(f"HOT_MOD{i}"))
        row["POISSONS"]      = _safe(elem.get("POISSONS"))
        row["PIPE_DENSITY"]  = _safe(elem.get("PIPE_DENSITY"))
        row["INSUL_DENSITY"] = _safe(elem.get("INSUL_DENSITY"))
        row["FLUID_DENSITY"] = _safe(elem.get("FLUID_DENSITY"))

        # ── SECTION 6: Cladding / refractory ─────────────────────────────────
        for col in ["REFRACT_THK","REFRACT_DENSITY","CLAD_THK","CLAD_DENSITY",
                    "INSUL_CLAD_UNIT_WEIGHT"]:
            row[col] = _safe(elem.get(col))

        # ── SECTION 7: Material ID ────────────────────────────────────────────
        for col in ["MATERIAL_NUM","MATERIAL_NAME","MILL_TOL_PLUS",
                    "MILL_TOL_MINUS","SEAM_WELD"]:
            row[col] = _safe(elem.get(col))

        # ── SECTION 8: All IEL pointer columns ────────────────────────────────
        for col in ["BEND_PTR","RIGID_PTR","EXPJ_PTR","REST_PTR","DISP_PTR",
                    "FORCMNT_PTR","ULOAD_PTR","WLOAD_PTR","EOFF_PTR","ALLOW_PTR",
                    "INT_PTR","HGR_PTR","NOZ_PTR","REDUCER_PTR","FLANGE_PTR"]:
            row[col] = _safe(elem.get(col))

        # ── SECTION 9: BND_ — joined INPUT_BENDS ─────────────────────────────
        bp = _iptr(elem.get("BEND_PTR"))
        b  = bend_idx.get(bp, {})
        for col in ["RADIUS","TYPE","ANGLE1","NODE1","ANGLE2","NODE2",
                    "ANGLE3","NODE3","NUM_MITER","FIT_THICK","KFACTOR",
                    "SEAM_WELD","WI_FACTOR"]:
            row[f"BND_{col}"] = _safe(b.get(col))

        # ── SECTION 10: RST_ — joined INPUT_RESTRAINTS ────────────────────────
        rp = _iptr(elem.get("REST_PTR"))
        r  = rest_idx.get(rp, {})
        for col in ["NODE_NUM","NODE_NAME","RES_TYPEID","STIFFNESS","GAP",
                    "FRIC_COEF","CNODE","XCOSINE","YCOSINE","ZCOSINE",
                    "RES_TAG","RES_GUID"]:
            row[f"RST_{col}"] = _safe(r.get(col))

        # ── SECTION 11: RGD_ — joined INPUT_RIGIDS ───────────────────────────
        rgp = _iptr(elem.get("RIGID_PTR"))
        rg  = rigid_idx.get(rgp, {})
        row["RGD_RIGID_WGT"]  = _safe(rg.get("RIGID_WGT"))
        row["RGD_RIGID_TYPE"] = _safe(rg.get("RIGID_TYPE"))

        # ── SECTION 12: SIF_ — joined INPUT_SIFTEES via INT_PTR ──────────────
        sp  = _iptr(elem.get("INT_PTR"))
        s   = sif_idx.get(sp, {})
        for col in ["SIF_NUM","NODE","TYPE","SIF_IN","SIF_OUT","SIF_TORSION",
                    "SIF_AXIAL","SIF_PRESSURE","STRESSINDEX_Iin","STRESSINDEX_Iout",
                    "STRESSINDEX_It","STRESSINDEX_Ia","STRESSINDEX_Ipr",
                    "WELD_d","FILLET","PAD_THK","FTG_RO","CROTCH","WELD_ID","B1","B2"]:
            row[f"SIF_{col}"] = _safe(s.get(col))

        rows_out.append(row)

    df_out = pd.DataFrame(rows_out)
    logger.info(f"[L4] Universal CSV: {len(df_out)} rows × {len(df_out.columns)} columns")
    return df_out


def load_universal_csv(csv_path_or_df) -> Dict[str, Any]:
    """
    Load a universal CSV exported by build_universal_csv() and reconstruct
    the 4 table lists that build_hybrid_cii() expects.

    Returns dict with keys: elem_df, bend_rows, rest_rows, rigid_rows, sif_rows
    """
    if isinstance(csv_path_or_df, pd.DataFrame):
        df = csv_path_or_df
    else:
        df = pd.read_csv(csv_path_or_df)

    bend_rows  = []
    rest_rows  = []
    rigid_rows = []
    sif_rows   = []

    for _, row in df.iterrows():
        # Reconstruct bend row if BND_ columns present
        if _has_val(row.get("BND_RADIUS")):
            bend_rows.append({
                "BEND_PTR":  _safe(row.get("BEND_PTR")),
                "RADIUS":    _safe(row.get("BND_RADIUS")),
                "ANGLE1":    _safe(row.get("BND_ANGLE1")),
                "NODE1":     _safe(row.get("BND_NODE1")),
                "ANGLE2":    _safe(row.get("BND_ANGLE2")),
                "NODE2":     _safe(row.get("BND_NODE2")),
                "ANGLE3":    _safe(row.get("BND_ANGLE3")),
                "NODE3":     _safe(row.get("BND_NODE3")),
                "NUM_MITER": _safe(row.get("BND_NUM_MITER")),
                "FIT_THICK": _safe(row.get("BND_FIT_THICK")),
                "KFACTOR":   _safe(row.get("BND_KFACTOR")),
                "WI_FACTOR": _safe(row.get("BND_WI_FACTOR")),
            })
        # Reconstruct restraint row
        if _has_val(row.get("RST_NODE_NUM")):
            rest_rows.append({
                "REST_PTR":   _safe(row.get("REST_PTR")),
                "NODE_NUM":   _safe(row.get("RST_NODE_NUM")),
                "RES_TYPEID": _safe(row.get("RST_RES_TYPEID")),
                "STIFFNESS":  _safe(row.get("RST_STIFFNESS")),
                "GAP":        _safe(row.get("RST_GAP")),
                "FRIC_COEF":  _safe(row.get("RST_FRIC_COEF")),
                "CNODE":      _safe(row.get("RST_CNODE")),
                "XCOSINE":    _safe(row.get("RST_XCOSINE")),
                "YCOSINE":    _safe(row.get("RST_YCOSINE")),
                "ZCOSINE":    _safe(row.get("RST_ZCOSINE")),
                "RES_TAG":    _safe(row.get("RST_RES_TAG")),
                "RES_GUID":   _safe(row.get("RST_RES_GUID")),
            })
        # Reconstruct rigid row
        if _has_val(row.get("RGD_RIGID_WGT")):
            rigid_rows.append({
                "RIGID_PTR":  _safe(row.get("RIGID_PTR")),
                "RIGID_WGT":  _safe(row.get("RGD_RIGID_WGT")),
                "RIGID_TYPE": _safe(row.get("RGD_RIGID_TYPE")),
            })
        # Reconstruct SIF row
        if _has_val(row.get("SIF_SIF_NUM")):
            sif_rows.append({
                "SIF_PTR":  _safe(row.get("INT_PTR")),
                "SIF_NUM":  _safe(row.get("SIF_SIF_NUM")),
                "NODE":     _safe(row.get("SIF_NODE")),
                "TYPE":     _safe(row.get("SIF_TYPE")),
                **{c: _safe(row.get(f"SIF_{c}")) for c in [
                    "SIF_IN","SIF_OUT","SIF_TORSION","SIF_AXIAL","SIF_PRESSURE",
                    "STRESSINDEX_Iin","STRESSINDEX_Iout","STRESSINDEX_It",
                    "STRESSINDEX_Ia","STRESSINDEX_Ipr","WELD_d","FILLET",
                    "PAD_THK","FTG_RO","CROTCH","WELD_ID","B1","B2"
                ]}
            })

    return {
        "elem_df":    df,
        "bend_rows":  bend_rows,
        "rest_rows":  rest_rows,
        "rigid_rows": rigid_rows,
        "sif_rows":   sif_rows,
    }


# ─── Aux-data record formatters ───────────────────────────────────────────────

def format_bend_records(bend_rows: List[Dict], sentinel_val: float = -1.0101) -> List[str]:
    """3 lines per BEND record. Confirmed ACCDB columns."""
    lines = []
    z = "     0.000000"
    for row in bend_rows:
        g = lambda col: _fv(row.get(col, 0), sentinel_val=sentinel_val)
        lines.append(f"  {g('RADIUS')}{g('ANGLE1')}{g('NODE1')}{g('ANGLE2')}{g('NODE2')}{g('ANGLE3')}")
        lines.append(f"  {g('NODE3')}{g('NUM_MITER')}{g('FIT_THICK')}{g('KFACTOR')}{g('WI_FACTOR')}{z}")
        lines.append(f"  {z}{z}")
    return lines


def format_restrant_records(rest_rows: List[Dict], sentinel_val: float = -1.0101) -> List[str]:
    """4 lines per RESTRANT record. Confirmed ACCDB columns."""
    lines = []
    z = "     0.000000"
    for row in rest_rows:
        g = lambda col: _fv(row.get(col, 0), sentinel_val=sentinel_val)
        lines.append(f"  {g('NODE_NUM')}{g('RES_TYPEID')}{g('STIFFNESS')}{g('GAP')}{g('FRIC_COEF')}{g('CNODE')}")
        lines.append(f"  {g('XCOSINE')}{g('YCOSINE')}{g('ZCOSINE')}")
        tag  = str(row.get("RES_TAG",  "") or "").strip()
        guid = str(row.get("RES_GUID", "") or "").strip()
        if tag and tag not in ("None", "nan"):
            lines.append(f"       {len(tag):5d} {tag}")
        else:
            lines.append("           0 ")
        if guid and guid not in ("None", "nan"):
            lines.append(f"       {len(guid):5d} {guid}")
        else:
            lines.append("           0 ")
    return lines


def format_rigid_records(rigid_rows: List[Dict], sentinel_val: float = -1.0101) -> List[str]:
    """3 lines per RIGID record. Confirmed ACCDB columns."""
    lines = []
    z = "     0.000000"
    for row in rigid_rows:
        wgt = _fv(row.get("RIGID_WGT", 0), sentinel_val=sentinel_val)
        lines.append(f"  {wgt}{z}{z}{z}{z}{z}")  # line 1: weight + 5 zeros
        lines.append(f"  {z}{z}{z}{z}{z}{z}")     # line 2
        lines.append(f"  {z}")                     # line 3
    return lines


def format_sif_records(sif_rows: List[Dict], sentinel_val: float = -1.0101) -> List[str]:
    """2 lines per SIF&TEES record. Confirmed ACCDB columns."""
    lines = []
    z = "     0.000000"
    for row in sif_rows:
        g = lambda col: _fv(row.get(col, 0), sentinel_val=sentinel_val)
        lines.append(f"  {g('SIF_NUM')}{g('NODE')}{g('TYPE')}{g('SIF_IN')}{g('SIF_OUT')}{g('SIF_TORSION')}")
        lines.append(f"  {g('SIF_AXIAL')}{g('SIF_PRESSURE')}{g('WELD_d')}{g('FILLET')}{g('PAD_THK')}{g('FTG_RO')}")
    return lines


def get_default_allowbls_block() -> List[str]:
    """Standard CAESAR II ALLOWBLS 25-line defaults."""
    lines = [
        "       0.000000     0.000000     0.000000     0.000000  1.00000      1.00000    ",
        "    1.00000         0.000000     0.000000  9999.99         0.000000  3.00000    ",
    ]
    for _ in range(22):
        lines.append("       0.000000     0.000000     0.000000     0.000000     0.000000     0.000000")
    lines.append("    1.00000      1.00000      1.00000      1.00000      1.00000      1.00000    ")
    return lines


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fv(val, width: int = 13, sentinel_val: float = -1.0101) -> str:
    """Format a value as 13-char Fortran-style float."""
    try:
        f = float(val)
        # Treat CAESAR II auto-calc sentinel as zero for aux records
        if abs(f - (-1.0101)) < 0.001 or abs(f - (-1.01010000705719)) < 0.001 or abs(f - sentinel_val) < 0.001:
            return "     0.000000"
        if f == 0.0:
            return "     0.000000"
        return f"{f:13.6G}".rjust(width)
    except (ValueError, TypeError):
        return "     0.000000"


def _safe(val) -> Any:
    """Return None-safe scalar for DataFrame building."""
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except Exception:
        pass
    return val


def _iptr(val) -> int:
    """Convert ptr value to int, return 0 on failure."""
    try:
        v = int(float(val))
        return v if v > 0 else 0
    except Exception:
        return 0


def _has_val(val) -> bool:
    """True if val is a usable (non-null, non-empty) value."""
    if val is None:
        return False
    try:
        if pd.isna(val):
            return False
    except Exception:
        pass
    s = str(val).strip()
    return s not in ("", "None", "nan", "0", "0.0")


def _count_from_aux(aux_data: Dict, key: str, lines_per_record: int) -> int:
    """Estimate record count from aux_data (fallback when rows list not available)."""
    records = aux_data.get(key, [])
    if not records:
        return 0
    total_lines = sum(len(r) for r in records)
    return total_lines // lines_per_record if lines_per_record > 0 else 0


def _max_iel_ptr(parsed_data: Dict[str, Any], iel_index: int) -> int:
    """Return the max positive IEL pointer value for a given IEL slot."""
    max_ptr = 0
    for el in parsed_data.get("elements", []):
        iel = el.get("IEL", [])
        if len(iel) <= iel_index:
            continue
        try:
            ptr = int(float(iel[iel_index]))
        except Exception:
            continue
        if ptr > max_ptr:
            max_ptr = ptr
    return max_ptr
