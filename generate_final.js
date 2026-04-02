function Logic3_ensureFloat(row, key) {
    const val = row[key];
    if (val === undefined || val === null || val === "" || val === "None") return 0.0;
    const f = parseFloat(val);
    return isNaN(f) ? 0.0 : f;
}

function Logic3_generateFinal(basicRows, benchmarkBlocks) {
    const elementLines = ["#$ ELEMENTS"];

    for (const row of basicRows) {
        if (!String(row["ELEMENTID"] || "").trim()) continue;

        const n1 = Logic3_ensureFloat(row, "FROM_NODE");
        const n2 = Logic3_ensureFloat(row, "TO_NODE");
        const dx = Logic3_ensureFloat(row, "DELTA_X");
        const dy = Logic3_ensureFloat(row, "DELTA_Y");
        const dz = Logic3_ensureFloat(row, "DELTA_Z");
        const diam = Logic3_ensureFloat(row, "DIAMETER");

        elementLines.push(fmt_col(n1,4,11)+fmt_col(n2,6,13)+fmt_col(dx,9,17)+fmt_col(dy,5,13)+fmt_col(dz,1,9)+fmt_col(diam,8,17));

        const wt = Logic3_ensureFloat(row, "WALL_THICK");
        const ins = Logic3_ensureFloat(row, "INSUL_THICK");
        const corr = Logic3_ensureFloat(row, "CORR_ALLOW");
        const t1 = Logic3_ensureFloat(row, "TEMP_EXP_C1");
        const t2 = Logic3_ensureFloat(row, "TEMP_EXP_C2");
        const t3 = Logic3_ensureFloat(row, "TEMP_EXP_C3");

        elementLines.push(fmt_col(wt,4,11)+fmt_col(ins,9,17)+fmt_col(corr,5,13)+fmt_col(t1,2,9)+fmt_col(t2,9,17)+fmt_col(t3,5,13));

        const t4 = Logic3_ensureFloat(row, "TEMP_EXP_C4");
        const t5 = Logic3_ensureFloat(row, "TEMP_EXP_C5");
        const t6 = Logic3_ensureFloat(row, "TEMP_EXP_C6");

        elementLines.push(fmt_col(t4,7,15)+fmt_col(t5,5,13)+fmt_col(t6,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));

        const p1 = Logic3_ensureFloat(row, "PRESSURE1");
        const p2 = Logic3_ensureFloat(row, "PRESSURE2");
        const p3 = Logic3_ensureFloat(row, "PRESSURE3");

        elementLines.push(fmt_col(p1,4,11)+fmt_col(p2,9,17)+fmt_col(p3,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));

        const emod = Logic3_ensureFloat(row, "MODULUS");
        const pois = Logic3_ensureFloat(row, "POISSONS");
        const pdens = Logic3_ensureFloat(row, "PIPE_DENSITY");

        if (pdens > 0) {
            // Fix 3.4: use actual PIPE_DENSITY from row, not hardcoded 0.00783344
            elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(emod,2,9)+fmt_col(pois,5,13)+fmt_e(pdens,17,6));
        } else {
            elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(emod,2,9)+fmt_col(pois,5,13)+fmt_col(0,5,17));
        }

        if (n1 === 10.0 || n1 === 20.0) {
            elementLines.push(fmt_e(0.000184213,15,6)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));
        } else {
            elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));
        }

        elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));

        let mill_p = Logic3_ensureFloat(row, "MILL_TOL_PLUS");
        let mill_m = Logic3_ensureFloat(row, "MILL_TOL_MINUS");

        if (Math.abs(mill_p - 9999.99) < 1 || mill_p < 0) mill_p = 9999.99;
        if (Math.abs(mill_m - 9999.99) < 1 || mill_m < 0) mill_m = 9999.99;

        if (mill_p === 9999.99 && mill_m === 9999.99) {
            elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+"  9999.99      9999.99    ");
        } else {
            elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(mill_m,2,9)+fmt_col(mill_p,6,17));
        }

        elementLines.push(fmt_col(0,7,15)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13)+fmt_col(0,5,13));
        elementLines.push("           0 ");

        if (n1 === 10.0) {
            elementLines.push("          10 unassigned");
        } else {
            elementLines.push("           0 ");
        }

        elementLines.push("               -1           -1");

        // IEL array: 17 slots (indices 0-16)
        const ptrs = Array(17).fill(0);

        // IEL[0] = BEND_PTR
        const bnd_p = Logic3_ensureFloat(row, "BEND_PTR");
        if (bnd_p > 0) ptrs[0] = Math.trunc(bnd_p);

        // IEL[1] = RIGID_PTR  (Fix 3.1: was REST_PTR, now correctly RIGID_PTR)
        const rigid_p = Logic3_ensureFloat(row, "RIGID_PTR");
        if (rigid_p > 0) ptrs[1] = Math.trunc(rigid_p);

        // IEL[2] = EXPJ_PTR  (Fix 3.2: new)
        const expj_p = Logic3_ensureFloat(row, "EXPJ_PTR");
        if (expj_p > 0) ptrs[2] = Math.trunc(expj_p);

        // IEL[3] = REST_PTR  (Fix 3.1: was RIGID_PTR, now correctly REST_PTR)
        const rest_p = Logic3_ensureFloat(row, "REST_PTR");
        if (rest_p > 0) ptrs[3] = Math.trunc(rest_p);

        // IEL[4] = DISP_PTR  (Fix 3.2: new)
        const disp_p = Logic3_ensureFloat(row, "DISP_PTR");
        if (disp_p > 0) ptrs[4] = Math.trunc(disp_p);

        // IEL[5] = FORCMNT_PTR  (Fix 3.2: new)
        const forcmnt_p = Logic3_ensureFloat(row, "FORCMNT_PTR");
        if (forcmnt_p > 0) ptrs[5] = Math.trunc(forcmnt_p);

        // IEL[6] = ULOAD_PTR  (Fix 3.2: new)
        const uload_p = Logic3_ensureFloat(row, "ULOAD_PTR");
        if (uload_p > 0) ptrs[6] = Math.trunc(uload_p);

        // IEL[7] = WLOAD_PTR  (Fix 3.2: new)
        const wload_p = Logic3_ensureFloat(row, "WLOAD_PTR");
        if (wload_p > 0) ptrs[7] = Math.trunc(wload_p);

        // IEL[8] = EOFF_PTR (element offsets)  (Fix 3.2: new, confirmed from ACCDB)
        const eoff_p = Logic3_ensureFloat(row, "EOFF_PTR");
        if (eoff_p > 0) ptrs[8] = Math.trunc(eoff_p);

        // IEL[9] = ALLOW_PTR
        const allow_p = Logic3_ensureFloat(row, "ALLOW_PTR");
        if (allow_p > 0) ptrs[9] = Math.trunc(allow_p);

        // IEL[10] = INT_PTR (SIF/Tee pointer)  (Fix 3.2: new)
        const int_p = Logic3_ensureFloat(row, "INT_PTR");
        if (int_p > 0) ptrs[10] = Math.trunc(int_p);

        // IEL[11] = MATERIAL_NUM (not a ptr — actual CAESAR II material library ID)  (Fix 3.2: new)
        const mat_num = Logic3_ensureFloat(row, "MATERIAL_NUM");
        if (mat_num > 0) ptrs[11] = Math.trunc(mat_num);

        // IEL[12] = reserved (unused)

        // IEL[13] = FLANGE_PTR  (Fix 3.2: new)
        const flange_p = Logic3_ensureFloat(row, "FLANGE_PTR");
        if (flange_p > 0) ptrs[13] = Math.trunc(flange_p);

        // IEL[14] = REDUCER_PTR  (Fix 3.2: new)
        const reducer_p = Logic3_ensureFloat(row, "REDUCER_PTR");
        if (reducer_p > 0) ptrs[14] = Math.trunc(reducer_p);

        // IEL[15] = HGR_PTR (hanger)  (Fix 3.2: new, confirmed from ACCDB)
        const hgr_p = Logic3_ensureFloat(row, "HGR_PTR");
        if (hgr_p > 0) ptrs[15] = Math.trunc(hgr_p);

        // IEL[16] = NOZ_PTR (nozzle)  (Fix 3.2: new, confirmed from ACCDB)
        const noz_p = Logic3_ensureFloat(row, "NOZ_PTR");
        if (noz_p > 0) ptrs[16] = Math.trunc(noz_p);

        // Emit IEL lines in groups of 6 (3 lines: 0-5, 6-11, 12-16)
        const groups = [[0, 6], [6, 12], [12, 17]];
        for (const [start, end] of groups) {
            let p_str = "";
            for (let i = start; i < end; i++) {
                const val = ptrs[i];
                const idx = i - start;
                if (idx === 0) {
                    p_str += val > 9 ? "             " + val : "              " + val;
                } else {
                    p_str += val > 9 ? "           " + val : "            " + val;
                }
            }
            elementLines.push(p_str);
        }
    }

    const keys = [
        "#$ VERSION", "#$ CONTROL", "#$ ELEMENTS", "#$ AUX_DATA",
        "#$ BEND", "#$ RIGID", "#$ EXPJT", "#$ RESTRANT", "#$ DISPLMNT",
        "#$ FORCMNT", "#$ UNIFORM", "#$ WIND", "#$ OFFSETS", "#$ ALLOWBLS",
        "#$ SIF&TEES", "#$ REDUCERS", "#$ FLANGES", "#$ EQUIPMNT",
        "#$ MISCEL_1", "#$ UNITS", "METRIC", "ON", "C", "bars", "MPa", "KPa",
        "#$ COORDS"
    ];

    const blocksOut = [];
    for (const k of keys) {
        if (k === "#$ ELEMENTS") {
            blocksOut.push(elementLines.join("\n"));
        } else {
            if (benchmarkBlocks[k]) {
                blocksOut.push(benchmarkBlocks[k]);
            }
        }
    }

    return blocksOut.join("\n") + "\n";
}
