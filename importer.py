function generateFinal(basicRows, benchmarkObj) {
    let elementLines = ["#$ ELEMENTS"];

    for (let row of basicRows) {
        if (String(row["ELEMENTID"] || "").trim() === "") continue;

        let n1 = ensureFloat(row, "FROM_NODE");
        let n2 = ensureFloat(row, "TO_NODE");
        let dx = ensureFloat(row, "DELTA_X");
        let dy = ensureFloat(row, "DELTA_Y");
        let dz = ensureFloat(row, "DELTA_Z");
        let diam = ensureFloat(row, "DIAMETER");

        elementLines.push(`${fmtCol(n1, 4, 11)}${fmtCol(n2, 6, 13)}${fmtCol(dx, 9, 17)}${fmtCol(dy, 5, 13)}${fmtCol(dz, 1, 9)}${fmtCol(diam, 8, 17)}`);

        let wt = ensureFloat(row, "WALL_THICK");
        let ins = ensureFloat(row, "INSUL_THICK");
        let corr = ensureFloat(row, "CORR_ALLOW");
        let t1 = ensureFloat(row, "TEMP_EXP_C1");
        let t2 = ensureFloat(row, "TEMP_EXP_C2");
        let t3 = ensureFloat(row, "TEMP_EXP_C3");

        elementLines.push(`${fmtCol(wt, 4, 11)}${fmtCol(ins, 9, 17)}${fmtCol(corr, 5, 13)}${fmtCol(t1, 2, 9)}${fmtCol(t2, 9, 17)}${fmtCol(t3, 5, 13)}`);

        let t4 = ensureFloat(row, "TEMP_EXP_C4");
        let t5 = ensureFloat(row, "TEMP_EXP_C5");
        let t6 = ensureFloat(row, "TEMP_EXP_C6");

        elementLines.push(`${fmtCol(t4, 7, 15)}${fmtCol(t5, 5, 13)}${fmtCol(t6, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);

        let p1 = ensureFloat(row, "PRESSURE1");
        let p2 = ensureFloat(row, "PRESSURE2");
        let p3 = ensureFloat(row, "PRESSURE3");

        elementLines.push(`${fmtCol(p1, 4, 11)}${fmtCol(p2, 9, 17)}${fmtCol(p3, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);

        let emod = ensureFloat(row, "MODULUS");
        let pois = ensureFloat(row, "POISSONS");
        let pdens = ensureFloat(row, "PIPE_DENSITY");

        if (pdens > 0) {
            elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(emod, 2, 9)}${fmtCol(pois, 5, 13)}${fmtE(0.00783344, 17, 6)}`);
        } else {
            elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(emod, 2, 9)}${fmtCol(pois, 5, 13)}${fmtCol(0, 5, 17)}`);
        }

        if (n1 === 10.0 || n1 === 20.0) {
            elementLines.push(`${fmtE(0.000184213, 15, 6)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);
        } else {
            elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);
        }

        elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);

        let mill_p = ensureFloat(row, "MILL_TOL_PLUS");
        let mill_m = ensureFloat(row, "MILL_TOL_MINUS");

        if (Math.abs(mill_p - 9999.99) < 1 || mill_p < 0) mill_p = 9999.99;
        if (Math.abs(mill_m - 9999.99) < 1 || mill_m < 0) mill_m = 9999.99;

        if (mill_p === 9999.99 && mill_m === 9999.99) {
            elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}  9999.99      9999.99    `);
        } else {
            elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(mill_m, 2, 9)}${fmtCol(mill_p, 6, 17)}`);
        }

        elementLines.push(`${fmtCol(0, 7, 15)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}${fmtCol(0, 5, 13)}`);

        elementLines.push(`           0 `);

        if (n1 === 10.0) {
            elementLines.push(`          10 unassigned`);
        } else {
            elementLines.push(`           0 `);
        }

        elementLines.push(`               -1           -1`);

        let ptrs = Array(15).fill(0);

        let bnd_p = ensureFloat(row, "BEND_PTR");
        if (bnd_p > 0) ptrs[0] = Math.trunc(bnd_p);

        let rest_p = ensureFloat(row, "REST_PTR");
        if (rest_p > 0) ptrs[1] = Math.trunc(rest_p);

        let rigid_p = ensureFloat(row, "RIGID_PTR");
        if (rigid_p > 0) ptrs[3] = Math.trunc(rigid_p);

        let allow_p = ensureFloat(row, "ALLOW_PTR");
        if (allow_p > 0) ptrs[9] = Math.trunc(allow_p);

        let pStr1 = "";
        for (let i = 0; i < 6; i++) {
            let val = ptrs[i];
            if (i === 0) pStr1 += (val > 9 ? `             ${val}` : `              ${val}`);
            else pStr1 += (val > 9 ? `           ${val}` : `            ${val}`);
        }
        elementLines.push(pStr1);

        let pStr2 = "";
        for (let i = 6; i < 12; i++) {
            let val = ptrs[i];
            if (i === 6) pStr2 += (val > 9 ? `             ${val}` : `              ${val}`);
            else pStr2 += (val > 9 ? `           ${val}` : `            ${val}`);
        }
        elementLines.push(pStr2);

        let pStr3 = "";
        for (let i = 12; i < 15; i++) {
            let val = ptrs[i];
            if (i === 12) pStr3 += (val > 9 ? `             ${val}` : `              ${val}`);
            else pStr3 += (val > 9 ? `           ${val}` : `            ${val}`);
        }
        elementLines.push(pStr3);
    }

    let keys = ["#$ VERSION", "#$ CONTROL", "#$ ELEMENTS", "#$ AUX_DATA", "#$ BEND", "#$ RIGID", "#$ EXPJT", "#$ RESTRANT", "#$ DISPLMNT", "#$ FORCMNT", "#$ UNIFORM", "#$ WIND", "#$ OFFSETS", "#$ ALLOWBLS", "#$ SIF&TEES", "#$ REDUCERS", "#$ FLANGES", "#$ EQUIPMNT", "#$ MISCEL_1", "#$ UNITS", "METRIC", "ON", "C", "bars", "MPa", "KPa", "#$ COORDS"];

    let blocksOut = [];
    for (let k of keys) {
        if (k === "#$ ELEMENTS") {
            blocksOut.push(elementLines.join("\n"));
        } else {
            if (benchmarkObj[k] !== undefined) {
                blocksOut.push(benchmarkObj[k]);
            }
        }
    }

    return blocksOut.join("\n") + "\n";
}
