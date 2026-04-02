# CAESAR II Neutral File Configuration Defaults
# Logic 2 copy of P2 config.py

CAESAR_CALCULATED_FLAG = -1.01010000705719

def get_sentinel():
    try:
        import js
        # Check if the UI has provided an explicit sentinel configuration
        # For simplicity, if we add an l2-setting-sentinel, we read it, else use default.
        ui_val = js.document.getElementById('l2-setting-sentinel').value
        if ui_val:
            return float(ui_val)
    except:
        pass
    return CAESAR_CALCULATED_FLAG

GLOBAL_PROJECT_PARAMS = {
    "JOBNAME": "INLET-SEPARATOR-SKID-C2",
    "ISSUE_NO": "",
    "UPDATE_TIME": "20260307 123322",
    "MODULUS": 203390.703125,
    "HOT_MOD1": 178960.625,
    "HOT_MOD2": 203390.703125,
    "HOT_MOD3": 203390.703125,
    "HOT_MOD4": 203390.703125,
    "HOT_MOD5": 203390.703125,
    "HOT_MOD6": 203390.703125,
    "HOT_MOD7": 203390.703125,
    "HOT_MOD8": 203390.703125,
    "HOT_MOD9": 203390.703125,
    "POISSONS": 0.2919999957084656,
    "PIPE_DENSITY": 0.0078334398567676,
    "MATERIAL_NUM": 106,
    "MATERIAL_NAME": "A106 B",
    "TEMP_EXP_C1": 350.0,
    "TEMP_EXP_C2": 0.0,
    "TEMP_EXP_C3": 0.0,
    "TEMP_EXP_C4": 0.0,
    "TEMP_EXP_C5": 0.0,
    "TEMP_EXP_C6": 0.0,
    "TEMP_EXP_C7": 0.0,
    "TEMP_EXP_C8": 0.0,
    "TEMP_EXP_C9": 0.0,
    "PRESSURE1": 2.0,
    "PRESSURE2": 0.0,
    "PRESSURE3": 0.0,
    "PRESSURE4": 0.0,
    "PRESSURE5": 0.0,
    "PRESSURE6": 0.0,
    "PRESSURE7": 0.0,
    "PRESSURE8": 0.0,
    "PRESSURE9": 0.0,
    "HYDRO_PRESSURE": 0.0,
    "INSUL_THICK": 0.0,
    "INSUL_DENSITY": 0.0,
    "FLUID_DENSITY": 0.0,
    "CORR_ALLOW": 0.0,
    "REFRACT_THK": 0.0,
    "REFRACT_DENSITY": 0.0,
    "CLAD_THK": 0.0,
    "CLAD_DENSITY": 0.0,
    "INSUL_CLAD_UNIT_WEIGHT": 0.0,
    "MILL_TOL_PLUS": 0.0,
    "MILL_TOL_MINUS": 0.0,
    "SEAM_WELD": 0.0,
    "LINE_NO": "unassigned"
}

MANDATORY_FIELDS = {
    "INPUT_BASIC_ELEMENT_DATA": [
        "ELEMENTID", "FROM_NODE", "TO_NODE", "DELTA_X", "DELTA_Y", "DELTA_Z",
        "DIAMETER", "WALL_THICK", "BEND_PTR", "RIGID_PTR", "REST_PTR",
        "ALLOW_PTR", "INT_PTR"
    ],
    "INPUT_RESTRAINTS": [
        "REST_PTR", "NODE_NUM", "RES_TYPEID", "XCOSINE", "YCOSINE", "ZCOSINE"
    ],
    "INPUT_BENDS": [
        "BEND_PTR", "RADIUS", "ANGLE1", "NODE1", "ANGLE2", "NODE2"
    ],
    "INPUT_SIFTEES": [
        "SIF_PTR", "SIF_NUM", "NODE", "TYPE"
    ],
    "INPUT_ALLOWABLES": [
        "CASE_NUM"
    ]
}

CALCULATED_FIELDS = {
    "INPUT_RESTRAINTS": [
        "STIFFNESS", "GAP", "FRIC_COEF", "CNODE"
    ],
    "INPUT_BENDS": [
        "ANGLE3", "NODE3", "NUM_MITER", "FIT_THICK", "KFACTOR"
    ],
    "INPUT_SIFTEES": [
        "SIF_IN", "SIF_OUT", "SIF_TORSION", "SIF_AXIAL", "SIF_PRESSURE",
        "STRESSINDEX_Iin", "STRESSINDEX_Iout", "STRESSINDEX_It", "STRESSINDEX_Ia", "STRESSINDEX_Ipr",
        "WELD_d", "FILLET", "PAD_THK", "FTG_RO", "CROTCH", "WELD_ID", "B1", "B2"
    ],
    "INPUT_ALLOWABLES": [
        "COLD_ALLOW", "HOT_ALLOW", "CYC_RED_FACTOR", "EFF", "SY", "HOT_SY", "SU", "HOT_SU", "FAC",
        "PMAX", "PIPING_CODE", "BUTTWELDCYCLES", "BUTTWELDSTRESS", "FILLETWELDCYCLES", "FILLETWELDSTRESS",
        "ALPHA_H", "ALPHA_FAB", "GAMMA_C", "R", "ALPHA_GW", "DESIGN_LT", "CHEMICAL_RES", "CURVE_RADIUS", "EHB", "DF", "YD"
    ]
}

EMPTY_FIELDS = {
    "INPUT_BASIC_ELEMENT_DATA": {
        "FROM_NODE_NAME": "",
        "TO_NODE_NAME": "",
        "ELEMENT_NAME": "",
        "EXPJ_PTR": 0,
        "DISP_PTR": 0,
        "FORCMNT_PTR": 0,
        "ULOAD_PTR": 0,
        "WLOAD_PTR": 0,
        "EOFF_PTR": 0,
        "HGR_PTR": 0,
        "NOZ_PTR": 0,
        "REDUCER_PTR": 0,
        "FLANGE_PTR": 0
    },
    "INPUT_RESTRAINTS": {
        "NODE_NAME": "",
        "RES_TAG": "",
        "RES_GUID": ""
    },
    "INPUT_BENDS": {
        "TYPE": 0,
        "SEAM_WELD": 0,
        "WI_FACTOR": -1
    },
    "INPUT_ALLOWABLES": {
        "ALLOWBL_PTR": 1,
        "APP_P_OPE_ALL_REDUCTION": -1,
        "ALLOWBL_STRESS_INDICATOR": "",
        "DESIGN_FACTOR": "",
        "HOOP_STRESS_FACTOR": 0,
        "SUPP_RQR": -1,
        "MAT_LP": -1,
        "BURST_OPE": -1,
        "BURST_TEST": -1,
        "COLLAPSE": -1,
        "PROPBUCK": -1,
        "LCC": -1,
        "DCC": -1,
        "BURIED": -1
    }
}
