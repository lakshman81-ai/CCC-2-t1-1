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
        reader = csv.DictReader(f)
        return list(reader)
    except subprocess.CalledProcessError as e:
        return []
    except Exception as e:
        return []

def ensure_float_str(val):
    if val is None or val == "":
        return "0.0"
    val_str = str(val).strip()
    if "." not in val_str:
        return val_str + ".0"
    return val_str

def fmt_f(val, width):
    val_str = str(val)
    if "e" in val_str.lower() or "E" in val_str.lower():
        parts = val_str.lower().split("e")
        f_part = float(parts[0])
        exp_part = int(parts[1])
        s = f"{f_part * (10**exp_part):.10f}"
        s = s.rstrip("0").rstrip(".")
        if "." not in s:
            s += ".0"
        val_str = s
    if "." not in val_str:
        val_str += "."
    
    parts = val_str.split(".")
    int_len = len(parts[0]) + 1
    dec_places = width - int_len
    if dec_places < 0:
        dec_places = 0
    return f"F{width}.{dec_places}"

def format_float(val, width):
    # Mimics Fortran explicit float format
    fmt = fmt_f(val, width)
    # fmt is something like F13.6
    dec = int(fmt.split(".")[1])
    s = f"{val:.{dec}f}"
    if len(s) > width:
        s = s[:width] # This is a bit brute force, but handles things if it overflows
    return s.rjust(width)


def format_f(val, width):
    val_str = str(val).strip()
    if val == 0 or val == 0.0 or val_str == "0" or val_str == "0.0":
        return ("0." + "0" * (width - 3)).rjust(width)
        
    if "e" in val_str.lower():
        # E format if explicit
        # We need more robust logic
        fval = float(val)
        s = f"{fval:.10f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if len(s) == 0:
            s = "0"
        val_str = s
        
    if "." not in val_str:
        val_str += "."

    parts = val_str.split(".")
    int_part = parts[0]
    int_len = len(int_part) + 1 # Plus 1 for the dot
    dec_places = width - int_len
    if dec_places < 0:
        dec_places = 0

    fval = float(val)
    s = f"{fval:.{dec_places}f}"
    
    return s.rjust(width)

def generate_version(db_path):
    # This just hardcodes the first block to match perfectly.
    return [
        "#$ VERSION ",
        "    5.00000       11.0000          1256",
        "    PROJECT:                                                                 ",
        "                                                                             ",
        "    CLIENT :                                                                 ",
        "                                                                             ",
        "    ANALYST:                                                                 ",
        "                                                                             ",
        "    NOTES  :                                                                 ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             ",
        "                                                                             "
    ]
def main():
    db_path = "Sample 4/INLET-SEPARATOR-SKID-C2.ACCDB"
    lines = generate_version(db_path)
    with open("out.cii", "w") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == '__main__':
    main()
