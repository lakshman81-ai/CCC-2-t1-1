function fmt_col(val, leading_spaces, total_width) {
    let val_str = String(val).trim();
    if (val_str === "0" || val_str === "0.0" || val_str === "" || val_str === "None" || val_str === "undefined") {
        let dec = total_width - leading_spaces - 2;
        if (dec < 0) dec = 0;
        return " ".repeat(leading_spaces) + "0." + "0".repeat(dec);
    }

    if (val_str.toLowerCase().includes("e")) {
        let fval = parseFloat(val);
        let s = fval.toFixed(10);
        s = s.replace(/0+$/, '').replace(/\.$/, '');
        if (s.length === 0) s = "0";
        val_str = s;
    }

    if (!val_str.includes(".")) val_str += ".";

    let int_part = val_str.split(".")[0];
    let Y = int_part.length + 1;

    let dec_places = total_width - leading_spaces - Y;
    if (dec_places < 0) dec_places = 0;

    let fval = parseFloat(val);
    let s = fval.toFixed(dec_places);
    if (!s.includes(".") && !s.includes("E") && !s.includes("e")) {
        s += ".";
    }

    let res = " ".repeat(leading_spaces) + s;
    if (res.length > total_width) {
        res = res.slice(0, total_width);
    }
    return res;
}

function fmt_e(val, width, d) {
    let fval = parseFloat(val);
    if (fval === 0.0) {
        let s = "0." + "0".repeat(d) + "E+00";
        return s.padStart(width);
    }
    let sign = fval < 0 ? "-" : "";
    fval = Math.abs(fval);
    let exp = Math.floor(Math.log10(fval)) + 1;
    let frac = fval / Math.pow(10, exp);
    let frac_str = frac.toFixed(d).slice(2);
    let exp_sign = exp >= 0 ? "+" : "-";
    let exp_val = Math.abs(exp);
    let s = sign + "0." + frac_str + "E" + exp_sign + String(exp_val).padStart(2, '0');
    if (s[0] !== "-" && width - s.length > 0) {
        s = " ".repeat(width - s.length) + s;
    }
    return s;
}

function fmt_i(val, width) {
    if (val === null || val === "" || val === "None" || val === undefined) val = 0;
    let s = String(Math.trunc(parseFloat(val)));
    return s.padStart(width);
}

function get_blocks(text) {
    const lines = text.split("\n");
    const blocks = {};
    let current_block = [];
    let current_name = null;

    for (const line of lines) {
        if (line.startsWith("#$") || line.startsWith("  bars") || line.startsWith("  METRIC") ||
            line.startsWith("  MPa") || line.startsWith("     KPa") || line.startsWith("  C") ||
            line.startsWith("  ON")) {
            if (current_name) {
                blocks[current_name] = current_block.join("\n");
            }
            current_name = line.trim();
            if (current_name.startsWith("Data generated")) continue;
            current_block = [line];
        } else {
            if (current_name) {
                current_block.push(line);
            }
        }
    }
    if (current_name) {
        blocks[current_name] = current_block.join("\n");
    }
    return blocks;
}
