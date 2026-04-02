import argparse
import sys
import os
from parser import CIIParser, ParserSettings
from serializer import CIISerializer, SerializerSettings
from exporter import generate_custom_csv
from logger import get_logger

logger = get_logger("cli")

APP_VERSION = "0.1.0"
DATE_STR = "dd-mm-yy" # Placeholder for dynamic build if needed
TIME_STR = "xx.xx"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header():
    print("=" * 80)
    print("                      CAESAR II .cii BI-DIRECTIONAL PARSER                      ".center(80))
    print("=" * 80)
    print(" [ CONFIGURATION ]  [ VERSION & CONTROL ]  [ ELEMENTS PREVIEW ]  [ UNITS & AUX ]".center(80))
    print("=" * 80)

def display_menu(settings: ParserSettings, input_file: str, output_file: str):
    clear_screen()
    draw_header()

    print("  [ FILE SETTINGS & MEMORY ]")
    print(f"  Neutral File Name to Be Converted : {input_file if input_file else '[ None ]'}")
    print(f"  File Name to Be Created           : {output_file if output_file else '[ None ]'} (Defaults to input dir)")
    print(f"  Output Format                     : [ Custom 41-Col CSV ]")
    print("")
    print("  [ PARSER SETTINGS ]")
    mode_str = "Data Matrix" if settings.is_data_matrix else "Standard Neutral File"
    print(f"  Parsing Mode             : [ {mode_str} ]")
    print(f"  N1 Base Allocation       : {settings.n1_base} (Sets arrays: N2={settings.n1_base//2}, N3={settings.n1_base//3}, N4={settings.n1_base//4}, N5={settings.n1_base//5})")
    print("")
    print("  [ ACTIONS ]")
    print("  (L) Load & Parse File      (P) Generate Preview      (E) Export/Save Data")
    print(f"  (S) Serialize & Compare    (Q) Quit                  ver.{DATE_STR} time {TIME_STR}")
    print("=" * 80)
    print("  DEBUG & CONSOLE LOGGING")
    print("-" * 80)

def main():
    parser_arg = argparse.ArgumentParser(description="CAESAR II Neutral File Roundtrip CLI")
    parser_arg.add_argument("--input", default="SAMPLE 2/BENCHMARK.CII", help="Input .cii file")
    parser_arg.add_argument("--out", default="output.csv", help="Output file")
    parser_arg.add_argument("--n1", type=int, default=2000, help="N1 base allocation")
    parser_arg.add_argument("--matrix", action="store_true", help="Use Data Matrix mode")
    parser_arg.add_argument("--cli-only", action="store_true", help="Run command line only (no TUI)")
    parser_arg.add_argument("command", nargs="?", default="", help="Command to run (e.g. reconstruct)")
    parser_arg.add_argument("--table", default="", help="CSV table to reconstruct from")
    parser_arg.add_argument("--optimize", action="store_true", help="Run serialization optimizer")

    args = parser_arg.parse_args()

    settings = ParserSettings(n1_base=args.n1, is_data_matrix=args.matrix)
    input_file = args.input
    output_file = args.out

    parsed_data = None

    if args.cli_only or args.command == "reconstruct":
        p = CIIParser(settings)
        parsed_data = p.parse(input_file)

        if args.table:
            from importer import reconstruct_from_csv
            parsed_data = reconstruct_from_csv(args.table, parsed_data)

        if args.optimize:
            from optimizer import SerializationOptimizer
            from optimizer_settings import OptimizationSettings
            opt = SerializationOptimizer(input_file, parsed_data, OptimizationSettings())
            result = opt.optimize()
            print("Optimization result:", result)

            from serializer import CIISerializer, SerializerSettings
            s_settings = SerializerSettings(real_format=result["best_format"])
            serializer = CIISerializer(s_settings)
            gen_str = serializer.serialize(parsed_data)
            with open(output_file, 'wb') as f:
                f.write(gen_str.encode("latin-1"))

        elif args.command == "reconstruct":
            from serializer import CIISerializer, SerializerSettings
            s_settings = SerializerSettings()
            serializer = CIISerializer(s_settings)
            gen_str = serializer.serialize(parsed_data)
            with open(output_file, 'wb') as f:
                f.write(gen_str.encode("latin-1"))

        else:
            generate_custom_csv(parsed_data, output_file)

        return

    # Basic TUI Loop
    while True:
        display_menu(settings, input_file, output_file)
        try:
            choice = input("Select an action: ").strip().lower()
        except EOFError:
            break

        if choice == 'q':
            break
        elif choice == 'l':
            if not input_file:
                input_file = input("Enter input file path: ").strip()
            p = CIIParser(settings)
            parsed_data = p.parse(input_file)
            input("Press Enter to continue...")
        elif choice == 'p':
            if parsed_data:
                print("\n[ ELEMENTS PREVIEW ]")
                for i, el in enumerate(parsed_data.get("elements", [])[:5]):
                    print(f"Elmt {i+1}: From={el['REL'][0]}, To={el['REL'][1]}, DX={el['REL'][2]}")
                print("... showing first 5 elements.")
            else:
                print("No data loaded. Please (L)oad first.")
            input("Press Enter to continue...")
        elif choice == 'e':
            if parsed_data:
                generate_custom_csv(parsed_data, output_file)
            else:
                print("No data loaded. Please (L)oad first.")
            input("Press Enter to continue...")
        elif choice == 's':
            if parsed_data:
                from serializer import CIISerializer, SerializerSettings
                from comparator import compare_files
                s_settings = SerializerSettings()
                serializer = CIISerializer(s_settings)
                gen_str = serializer.serialize(parsed_data)
                diff = compare_files(input_file, gen_str.encode("latin-1"))
                print(f"Is exact match? {diff.is_exact_match}")
                print(f"Diff lines: {diff.generate_diff_report().count(chr(10))}")
            else:
                print("No data loaded. Please (L)oad first.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
