import pydantic
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger("Logic2_parser")

class ParserSettings(pydantic.BaseModel):
    n1_base: int = 2000
    is_data_matrix: bool = False

@dataclass
class ParseContext:
    lines: List[str]
    idx: int = 0

    def has_more(self) -> bool:
        return self.idx < len(self.lines)

    def peek(self) -> str:
        if self.idx < len(self.lines):
            return self.lines[self.idx]
        return ""

    def consume(self) -> str:
        line = self.peek()
        self.idx += 1
        return line

def parse_fortran_real_line(line: str) -> Tuple[List[float], List[str]]:
    """Parse a line with format (2X, 6G13.6). Returns (values, raw_strings)"""
    if len(line) < 2:
        return [], []
    data_str = line[2:]
    chunks = [data_str[i:i+13] for i in range(0, len(data_str), 13)]
    res = []
    for c in chunks:
        if not c.strip():
            res.append(0.0)
        else:
            try:
                res.append(float(c.strip()))
            except ValueError:
                res.append(0.0)
    return res, chunks

def parse_fortran_int_line(line: str) -> Tuple[List[int], List[str]]:
    """Parse a line with format (2X, 6I13). Returns (values, raw_strings)"""
    if len(line) < 2:
        return [], []
    data_str = line[2:]
    chunks = [data_str[i:i+13] for i in range(0, len(data_str), 13)]
    res = []
    for c in chunks:
        if not c.strip():
            res.append(0)
        else:
            try:
                res.append(int(c.strip()))
            except ValueError:
                res.append(0)
    return res, chunks

def parse_fortran_string_line(line: str, length_format_len: int = 5) -> Tuple[int, str]:
    """Parse format (7X, I5, 1X, A<len>)"""
    if len(line) < 7 + length_format_len:
        return 0, ""

    length_str = line[7:7+length_format_len]
    try:
        str_len = int(length_str.strip())
    except ValueError:
        str_len = 0

    if len(line) > 7 + length_format_len + 1:
        text = line[7+length_format_len+1 : 7+length_format_len+1+str_len]
    else:
        text = ""
    return str_len, text

class CIIParser:
    def __init__(self, settings: ParserSettings):
        self.settings = settings

        self.n1 = settings.n1_base
        self.n2 = self.n1 // 2
        self.n3 = self.n1 // 3
        self.n4 = self.n1 // 4
        self.n5 = self.n1 // 5
        self.n6 = int(self.n1 / 13.33)

        self.parsed_data = {
            "version": {},
            "control": {},
            "elements": [],
            "aux_data": {},
            "miscel_1": {},
            "units": {},
            "coords": []
        }
        logger.info(f"Initialized CIIParser with N1={self.n1}, N2={self.n2}, N3={self.n3}, N4={self.n4}, N5={self.n5}, N6={self.n6}")

    def parse(self, filepath: str):
        logger.info(f"[EVENT] File Opened: {filepath}")

        with open(filepath, 'r', encoding='latin-1') as f:
            lines = [line.rstrip('\r\n') for line in f]

        ctx = ParseContext(lines)

        if self.settings.is_data_matrix:
            self._parse_data_matrix(ctx)
            return self.parsed_data

        while ctx.has_more():
            line = ctx.peek()
            if line.startswith("#$"):
                section = line.strip().split()[1] if len(line.strip().split()) > 1 else ""
                logger.info(f"[PARSE] Reached #$ {section}")

                if section == "VERSION":
                    self._parse_version(ctx)
                elif section == "CONTROL":
                    self._parse_control(ctx)
                elif section == "ELEMENTS":
                    self._parse_elements(ctx)
                elif section == "AUX_DATA":
                    self._parse_aux_data(ctx)
                elif section == "MISCEL_1":
                    self._parse_miscel_1(ctx)
                elif section == "UNITS":
                    self._parse_units(ctx)
                elif section == "COORDS":
                    self._parse_coords(ctx)
                else:
                    ctx.consume()
            else:
                ctx.consume()

        return self.parsed_data

    def parse_lines(self, lines: List[str]):
        """Parse from a list of strings (no file I/O)."""
        ctx = ParseContext(lines)

        if self.settings.is_data_matrix:
            self._parse_data_matrix(ctx)
            return self.parsed_data

        while ctx.has_more():
            line = ctx.peek()
            if line.startswith("#$"):
                section = line.strip().split()[1] if len(line.strip().split()) > 1 else ""
                if section == "VERSION":
                    self._parse_version(ctx)
                elif section == "CONTROL":
                    self._parse_control(ctx)
                elif section == "ELEMENTS":
                    self._parse_elements(ctx)
                elif section == "AUX_DATA":
                    self._parse_aux_data(ctx)
                elif section == "MISCEL_1":
                    self._parse_miscel_1(ctx)
                elif section == "UNITS":
                    self._parse_units(ctx)
                elif section == "COORDS":
                    self._parse_coords(ctx)
                else:
                    ctx.consume()
            else:
                ctx.consume()

        return self.parsed_data

    def _parse_version(self, ctx: ParseContext):
        header = ctx.consume()
        self.parsed_data["version"] = {"version_header_raw": header}
        if not ctx.has_more(): return

        line1 = ctx.consume()
        gversion_str = line1[2:15]
        rversion_str = line1[15:28]
        icodepage_str = line1[28:36]

        self.parsed_data["version"] = {
            "GVERSION": float(gversion_str.strip()) if gversion_str.strip() else 0.0,
            "RVERSION": float(rversion_str.strip()) if rversion_str.strip() else 0.0,
            "ICODEPAGE": int(icodepage_str.strip()) if icodepage_str.strip() else 0,
            "GVERSION_RAW": gversion_str,
            "RVERSION_RAW": rversion_str,
            "ICODEPAGE_RAW": icodepage_str,
            "title_lines": [],
            "title_lines_raw": []
        }

        for _ in range(60):
            if not ctx.has_more() or ctx.peek().startswith("#$"):
                break
            title_line = ctx.consume()
            self.parsed_data["version"]["title_lines"].append(title_line[2:77])
            self.parsed_data["version"]["title_lines_raw"].append(title_line)

        logger.info(f"Parsed version: {self.parsed_data['version']['GVERSION']}, {self.parsed_data['version']['RVERSION']}")

    def _parse_control(self, ctx: ParseContext):
        header = ctx.consume()
        if "control" not in self.parsed_data:
            self.parsed_data["control"] = {}
        self.parsed_data["control"]["control_header_raw"] = header
        if not ctx.has_more(): return

        line1 = ctx.consume()
        counts, counts_raw = parse_fortran_int_line(line1)
        while len(counts) < 6:
            counts.append(0)
            counts_raw.append("             ")

        self.parsed_data["control"] = {
            "NUMELT": counts[0],
            "NUMNOZ": counts[1],
            "NOHGRS": counts[2],
            "NONAM": counts[3],
            "NORED": counts[4],
            "NUMFLG": counts[5],
            "counts_raw": counts_raw[:6],
            "aux_counts": [],
            "aux_counts_raw": []
        }

        logger.info(f"[PARSE] #$ CONTROL parsed NUMELT={counts[0]}")

        aux_counts = []
        aux_counts_raw = []
        for _ in range(3):
            if not ctx.has_more() or ctx.peek().startswith("#$"): break
            aux_line = ctx.consume()
            vals, raws = parse_fortran_int_line(aux_line)
            aux_counts.extend(vals)
            aux_counts_raw.extend(raws)

        self.parsed_data["control"]["aux_counts"] = aux_counts
        self.parsed_data["control"]["aux_counts_raw"] = aux_counts_raw

    def _parse_elements(self, ctx: ParseContext):
        header = ctx.consume()
        numelt = self.parsed_data.get("control", {}).get("NUMELT", 0)

        logger.info(f"[PARSE] Reading {numelt} elements.")

        elements = []
        for i in range(numelt):
            el = {
                "REL": [], "REL_RAW": [],
                "IEL": [], "IEL_RAW": [],
                "STR": [], "STR_RAW": [],
                "COLOR": [], "COLOR_RAW": []
            }

            for _ in range(9):
                if not ctx.has_more(): break
                raw_line = ctx.consume()
                vals, raws = parse_fortran_real_line(raw_line)
                el["REL"].extend(vals)
                el["REL_RAW"].append(raw_line)

            for _ in range(2):
                if not ctx.has_more(): break
                raw_str_line = ctx.consume()
                slen, text = parse_fortran_string_line(raw_str_line)
                el["STR"].append(text)
                el["STR_RAW"].append(raw_str_line)

            lines_left = []
            while ctx.has_more() and not ctx.peek().startswith("#$"):
                peek_line = ctx.peek()
                if "." in peek_line[2:15] and "E" not in peek_line[2:15]:
                    break
                lines_left.append(ctx.consume())

            if len(lines_left) > 3:
                el["COLOR_RAW"].append(lines_left[0])
                lines_left = lines_left[1:]

            for raw_int_line in lines_left:
                vals, raws = parse_fortran_int_line(raw_int_line)
                el["IEL"].extend(vals)
                el["IEL_RAW"].append(raw_int_line)

            while len(el["REL"]) < 98: el["REL"].append(0.0)
            while len(el["IEL"]) < 18: el["IEL"].append(0)

            from_node = el["REL"][0]
            to_node = el["REL"][1]
            logger.info(f"[VARIABLE STATE] Element {i+1} -> From Node: {from_node}, To Node: {to_node}")

            elements.append(el)

        self.parsed_data["elements"] = elements

    def _parse_aux_data(self, ctx: ParseContext):
        header = ctx.consume()

        while ctx.has_more() and ctx.peek().startswith("#$ ") and not ctx.peek().strip() in ["#$ MISCEL_1", "#$ UNITS", "#$ COORDS"]:
            raw_sub_header = ctx.consume()
            sub_header = raw_sub_header.strip().split()
            if len(sub_header) < 2: continue

            sub_name = sub_header[1]

            if "headers_raw" not in self.parsed_data["aux_data"]:
                self.parsed_data["aux_data"]["headers_raw"] = {}
            self.parsed_data["aux_data"]["headers_raw"][sub_name] = raw_sub_header
            logger.info(f"[PARSE] Parsing AUX_DATA subsection: {sub_name}")

            if sub_name not in self.parsed_data["aux_data"]:
                self.parsed_data["aux_data"][sub_name] = []

            records = []
            while ctx.has_more() and not ctx.peek().startswith("#$"):
                line = ctx.consume()
                records.append(line)

            self.parsed_data["aux_data"][sub_name].append(records)

    def _parse_miscel_1(self, ctx: ParseContext):
        header = ctx.consume()
        records = []
        while ctx.has_more() and not ctx.peek().startswith("#$"):
            records.append(ctx.consume())
        self.parsed_data["miscel_1"] = records

    def _parse_units(self, ctx: ParseContext):
        header = ctx.consume()
        self.parsed_data["units_header_raw"] = header
        records = []
        while ctx.has_more() and not ctx.peek().startswith("#$"):
            records.append(ctx.consume())
        self.parsed_data["units"] = records

    def _parse_coords(self, ctx: ParseContext):
        header = ctx.consume()
        self.parsed_data["coords_header_raw"] = header
        if not ctx.has_more(): return

        line1 = ctx.consume()
        if len(line1) < 2: return
        nxyz_str = line1[2:15]
        try:
            nxyz = int(nxyz_str.strip())
        except ValueError:
            nxyz = 0

        coords = []
        self.parsed_data["coords_raw_count"] = line1
        for _ in range(nxyz):
            if not ctx.has_more(): break
            line = ctx.consume()
            if len(line) >= 2 + 13:
                inode_str = line[2:15]
                xc_str = line[15:28]
                yc_str = line[28:41]
                zc_str = line[41:54]
                try:
                    coords.append({
                        "node": int(inode_str.strip()) if inode_str.strip() else 0,
                        "x": float(xc_str.strip()) if xc_str.strip() else 0.0,
                        "y": float(yc_str.strip()) if yc_str.strip() else 0.0,
                        "z": float(zc_str.strip()) if zc_str.strip() else 0.0,
                        "raw_line": line
                    })
                except ValueError:
                    pass

        self.parsed_data["coords"] = coords

    def _parse_data_matrix(self, ctx: ParseContext):
        logger.info("[PARSE] Parsing Alternative Data Matrix")
        elements = []
        while ctx.has_more():
            line = ctx.consume().strip()
            if not line: continue
            parts = line.split()
            if len(parts) >= 8:
                try:
                    elements.append({
                        "ELMT": int(parts[0]),
                        "N1": float(parts[1]),
                        "N2": float(parts[2]),
                        "DX": float(parts[3]),
                        "DY": float(parts[4]),
                        "DZ": float(parts[5]),
                        "DIAM": float(parts[6]),
                        "THK": float(parts[7])
                    })
                except ValueError:
                    logger.warning(f"[ERROR/WARN] Failed to parse Data Matrix line: {line}")

        self.parsed_data["data_matrix"] = elements
