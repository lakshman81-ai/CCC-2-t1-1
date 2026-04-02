"""Logic1_config.py — Constants for Logic 1 (copy of P1 config.py)."""

DEFAULT_MATERIAL_ID = 1      # fallback material if MATERIAL_NUM not in row
DEFAULT_TEMPERATURE = 70.0
DEFAULT_PRESSURE = 0.0

def get_sentinel_float():
    try:
        import js
        ui_val = js.document.getElementById('l1-setting-sentinel').value
        if ui_val:
            return float(ui_val)
    except:
        pass
    return -1.0101

def get_sentinel_str():
    val = get_sentinel_float()
    return f" {val}d0"

INDEX_TEMPERATURE_START = 19
INDEX_TEMPERATURE_END   = 27
INDEX_PRESSURE_START    = 28
INDEX_PRESSURE_END      = 36
INDEX_MATERIAL          = 11

MANDATORY_COLUMNS = [
    "FROM_NODE", "TO_NODE", "DX", "DY", "DZ",
    "DIAMETER", "THICKNESS", "CORROSION", "INSULATION", "DENSITY",
    "BEND_PTR", "RESTRAINT_PTR", "VALVE_PTR"
]
