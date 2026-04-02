const GLOBAL_DEFAULTS = {
    // Basic Pipe Geometry
    "DIAMETER": 114.3,
    "WALL_THICK": 6.0,
    "CORR_ALLOW": 0.0,
    "MILL_TOL_PLUS": -1.0101,  // Unspecified
    "MILL_TOL_MINUS": -1.0101, // Unspecified
    "INSUL_THICK": 0.0,
    "INSUL_DENSITY": 0.0,

    // Material & Code
    "MATERIAL_NUM": 106,       // e.g., A106 B
    "PIPE_DENSITY": -1.0101,   // CAESAR II Material Default
    "MODULUS": -1.0101,        // CAESAR II Material Default
    "POISSONS": -1.0101,       // CAESAR II Material Default

    // Operating Conditions
    "TEMP_EXP_C1": 21.0,       // Ambient T1
    "TEMP_EXP_C2": -1.0101,
    "TEMP_EXP_C3": -1.0101,
    "TEMP_EXP_C4": -1.0101,
    "TEMP_EXP_C5": -1.0101,
    "TEMP_EXP_C6": -1.0101,
    "TEMP_EXP_C7": -1.0101,
    "TEMP_EXP_C8": -1.0101,
    "TEMP_EXP_C9": -1.0101,

    "PRESSURE1": 0.0,          // P1
    "PRESSURE2": -1.0101,
    "PRESSURE3": -1.0101,
    "PRESSURE4": -1.0101,
    "PRESSURE5": -1.0101,
    "PRESSURE6": -1.0101,
    "PRESSURE7": -1.0101,
    "PRESSURE8": -1.0101,
    "PRESSURE9": -1.0101,

    // Support / Rigid / Pointers
    "BEND_PTR": 0,
    "REST_PTR": 0,
    "RIGID_PTR": 0,
    "ALLOW_PTR": 0
};

function getValue(row, key) {
    let val = row[key];
    if (val === undefined || String(val).trim() === "" || String(val).trim().toLowerCase() === "none") {
        return GLOBAL_DEFAULTS[key] !== undefined ? GLOBAL_DEFAULTS[key] : 0.0;
    }
    return parseFloat(val);
}

function ensureFloat(row, key) {
    return getValue(row, key);
}

function fmtCol(val, leadingSpaces, totalWidth) {
    let valStr = String(val).trim();
    if (valStr === "0" || valStr === "0.0" || valStr === "" || valStr === "none" || valStr === "NaN") {
        let dec = totalWidth - leadingSpaces - 2;
        if (dec < 0) dec = 0;
        return " ".repeat(leadingSpaces) + "0." + "0".repeat(dec);
    }

    if (valStr.toLowerCase().includes("e")) {
        let fval = parseFloat(val);
        let s = fval.toFixed(10);
        while (s.endsWith("0")) s = s.slice(0, -1);
        if (s.endsWith(".")) s = s.slice(0, -1);
        if (s.length === 0) s = "0";
        valStr = s;
    }

    if (!valStr.includes(".")) valStr += ".";

    let intPart = valStr.split(".")[0];
    let y = intPart.length + 1;

    let decPlaces = totalWidth - leadingSpaces - y;
    if (decPlaces < 0) decPlaces = 0;

    let fval = parseFloat(val);
    let s = fval.toFixed(decPlaces);
    if (!s.includes(".") && !s.toLowerCase().includes("e")) {
        s += ".";
    }

    let res = " ".repeat(leadingSpaces) + s;
    if (res.length > totalWidth) {
        res = res.slice(0, totalWidth);
    }
    return res;
}

function fmtE(val, width, d) {
    let fval = parseFloat(val);
    if (fval === 0.0 || isNaN(fval)) {
        let s = "0." + "0".repeat(d) + "E+00";
        return s.padStart(width, ' ');
    }
    let sign = fval < 0 ? "-" : "";
    fval = Math.abs(fval);
    let exp = Math.floor(Math.log10(fval)) + 1;
    let frac = fval / Math.pow(10, exp);
    // JS toFixed can round, match python behavior exactly if needed
    // Python frac_str is f"{frac:.{d}f}"[2:]
    let fracStr = frac.toFixed(d).slice(2);
    let expSign = exp >= 0 ? "+" : "-";
    let expVal = Math.abs(exp).toString().padStart(2, '0');
    let s = `${sign}0.${fracStr}E${expSign}${expVal}`;
    if (s[0] !== "-" && (width - s.length) > 0) {
        s = " ".repeat(width - s.length) + s;
    }
    return s.padStart(width, ' '); // ensure width
}

function fmtI(val, width) {
    if (val === undefined || val === "" || String(val).trim().toLowerCase() === "none" || isNaN(val)) val = 0;
    let s = Math.trunc(parseFloat(val)).toString();
    return s.padStart(width, ' ');
}
