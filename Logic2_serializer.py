import pydantic
import math
from typing import List, Dict, Any

class SerializerSettings(pydantic.BaseModel):
    is_data_matrix: bool = False
    real_format: str = "{:13.6G}"
    int_format: str = "{:13d}"
    use_dos_newlines: bool = True

class CIISerializer:
    def __init__(self, settings: SerializerSettings):
        self.settings = settings
        self.lines = []

    def _add_line(self, s: str):
        self.lines.append(s)

    def _format_real(self, val: float) -> str:
        if val == 0.0:
            return "     0.000000"

        s = f"{val:13.6G}"

        if len(s) > 13:
            s = s[:13]
        return s.rjust(13)

    def _format_int(self, val: int) -> str:
        return f"{val:13d}"

    def serialize(self, data: Dict[str, Any]) -> str:
        self.lines = []

        if self.settings.is_data_matrix:
            return self._serialize_data_matrix(data.get("data_matrix", []))

        # #$ VERSION
        if "version" in data:
            self._add_line("#$ VERSION ")
            v = data["version"]
            if "GVERSION_RAW" in v and "RVERSION_RAW" in v and "ICODEPAGE_RAW" in v:
                self._add_line(f"  {v['GVERSION_RAW']}{v['RVERSION_RAW']}{v['ICODEPAGE_RAW']}")
            elif "GVERSION_RAW" in v and "RVERSION_RAW" not in v:
                self._add_line(v["GVERSION_RAW"])
            else:
                gver = self._format_real(v.get("GVERSION", 5.0))
                rver = self._format_real(v.get("RVERSION", 11.0))
                icode = f"{v.get('ICODEPAGE', 1256):8d}"
                self._add_line(f"  {gver}{rver}{icode}")

            if "title_lines_raw" in v and v["title_lines_raw"]:
                for t in v["title_lines_raw"]:
                    self._add_line(t)
            else:
                for t in v.get("title_lines", []):
                    self._add_line(f"  {t.ljust(75)}")

        # #$ CONTROL
        if "control" in data:
            self._add_line("#$ CONTROL ")
            c = data["control"]

            if "counts_raw" in c and c["counts_raw"]:
                if isinstance(c["counts_raw"], list) and len(c["counts_raw"]) > 0:
                    if len(c["counts_raw"]) == 4 and "  0" in c["counts_raw"][1]:
                        numelt_str = f"{c.get('NUMELT', 0):12d}"
                        self._add_line("  " + numelt_str + c["counts_raw"][0][12:])
                        for line in c["counts_raw"][1:]:
                            self._add_line("  " + line)
                    else:
                        c["counts_raw"][0] = f"{c.get('NUMELT', 0):13d}"
                        self._add_line("  " + "".join(c["counts_raw"]))
                else:
                    self._add_line("  " + "".join(c["counts_raw"]))
            else:
                counts = [
                    c.get("NUMELT", 0), c.get("NUMNOZ", 0), c.get("NOHGRS", 0),
                    c.get("NONAM", 0), c.get("NORED", 0), c.get("NUMFLG", 0)
                ]
                self._add_line("  " + "".join(self._format_int(x) for x in counts))

            aux = c.get("aux_counts", [])
            aux_raw = c.get("aux_counts_raw", [])

            if aux_raw and len(aux_raw) >= len(aux):
                idx = 0
                while idx < len(aux_raw):
                    chunk = aux_raw[idx:idx+6]
                    if any(x.strip() for x in chunk) or idx == 0:
                        self._add_line("  " + "".join(chunk))
                    idx += 6
            elif len(aux) > 0:
                while len(aux) < 13 + 1: aux.append(0)
                idx = 0
                while idx < len(aux):
                    chunk = aux[idx:idx+6]
                    self._add_line("  " + "".join(self._format_int(x) for x in chunk))
                    idx += 6

        # #$ ELEMENTS
        if "elements" in data:
            self._add_line("#$ ELEMENTS")
            for el in data["elements"]:
                rel = el.get("REL", [])
                while len(rel) < 98: rel.append(0.0)
                rel_raw = el.get("REL_RAW", [])

                if rel_raw and all(isinstance(x, str) for x in rel_raw):
                    for line in rel_raw:
                        self._add_line(line)
                elif len(rel_raw) == 98:
                    for i in range(0, 54, 6):
                        chunk = rel_raw[i:i+6]
                        self._add_line("  " + "".join(chunk))
                else:
                    for i in range(0, 54, 6):
                        line_idx = i // 6
                        raw_line = rel_raw[line_idx] if line_idx < len(rel_raw) else None
                        if raw_line and isinstance(raw_line, str):
                            self._add_line(raw_line)
                        else:
                            chunk = rel[i:i+6]
                            self._add_line("  " + "".join(self._format_real(x) for x in chunk))

                strs = el.get("STR", ["", ""])
                while len(strs) < 2: strs.append("")
                str_raw = el.get("STR_RAW", [])
                for i in range(2):
                    raw_line = str_raw[i] if len(str_raw) > i else None
                    if raw_line and isinstance(raw_line, str):
                        self._add_line(raw_line)
                    else:
                        s = strs[i]
                        s_len = len(s)
                        self._add_line(f"       {s_len:5d} {s}")

                color_raw = el.get("COLOR_RAW", [])
                if color_raw and isinstance(color_raw, list) and len(color_raw) > 0 and color_raw[0]:
                    self._add_line(color_raw[0])

                iel = el.get("IEL", [])
                while len(iel) < 18: iel.append(0)
                iel_raw = el.get("IEL_RAW", [])

                if iel_raw and all(isinstance(x, str) for x in iel_raw):
                    for line in iel_raw:
                        self._add_line(line)
                elif len(iel_raw) >= 18:
                    for i in range(0, 18, 6):
                        chunk = iel_raw[i:i+6]
                        self._add_line("  " + "".join(chunk))
                else:
                    for i in range(0, 18, 6):
                        line_idx = i // 6
                        raw_line = iel_raw[line_idx] if line_idx < len(iel_raw) else None
                        if raw_line and isinstance(raw_line, str):
                            self._add_line(raw_line)
                        else:
                            chunk = iel[i:i+6]
                            self._add_line("  " + "".join(self._format_int(x) for x in chunk))

        # #$ AUX_DATA
        if "aux_data" in data:
            self._add_line("#$ AUX_DATA")
            headers_raw = data["aux_data"].get("headers_raw", {})
            for sub_name, records in data["aux_data"].items():
                if sub_name == "headers_raw": continue
                if sub_name in headers_raw:
                    self._add_line(headers_raw[sub_name])
                else:
                    self._add_line(f"#$ {sub_name}".ljust(11))
                for record in records:
                    for line in record:
                        self._add_line(line)

        # #$ MISCEL_1
        if "miscel_1" in data:
            self._add_line("#$ MISCEL_1")
            for line in data["miscel_1"]:
                self._add_line(line)

        # #$ UNITS
        if "units" in data:
            self._add_line("#$ UNITS   ")
            for line in data["units"]:
                self._add_line(line)

        # #$ COORDS
        if "coords" in data and len(data["coords"]) > 0:
            self._add_line("#$ COORDS  ")

            if "coords_raw_count" in data:
                self._add_line(data["coords_raw_count"])
            else:
                self._add_line("  " + self._format_int(len(data["coords"])))

            for c in data["coords"]:
                if "raw_line" in c:
                    self._add_line(c["raw_line"])
                else:
                    node = f"{c['node']:13d}"
                    xs = f"{c['x']:13.4f}"
                    ys = f"{c['y']:13.4f}"
                    zs = f"{c['z']:13.4f}"
                    self._add_line(f"  {node}{xs}{ys}{zs}")

        nl = "\r\n" if self.settings.use_dos_newlines else "\n"
        return nl.join(self.lines) + nl

    def _serialize_data_matrix(self, elements: List[Dict]) -> str:
        lines = []
        for el in elements:
            lines.append(f"{el['ELMT']:5d} {el['N1']:10.2f} {el['N2']:10.2f} "
                         f"{el['DX']:10.2f} {el['DY']:10.2f} {el['DZ']:10.2f} "
                         f"{el['DIAM']:10.2f} {el['THK']:10.2f}")
        nl = "\r\n" if self.settings.use_dos_newlines else "\n"
        return nl.join(lines) + nl
