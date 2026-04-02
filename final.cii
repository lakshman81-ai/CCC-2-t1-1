import difflib

class DiffResult:
    def __init__(self, original_bytes: bytes, generated_bytes: bytes):
        self.original_bytes = original_bytes
        self.generated_bytes = generated_bytes
        self.is_exact_match = (original_bytes == generated_bytes)

    def generate_diff_report(self) -> str:
        if self.is_exact_match:
            return "Exact match achieved."

        orig_lines = self.original_bytes.decode('latin-1').splitlines(keepends=True)
        gen_lines = self.generated_bytes.decode('latin-1').splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_lines,
            gen_lines,
            fromfile='original.cii',
            tofile='generated.cii'
        )
        return "".join(diff)

def compare_files(original_path: str, generated_bytes: bytes) -> DiffResult:
    with open(original_path, 'rb') as f:
        original_bytes = f.read()
    return DiffResult(original_bytes, generated_bytes)
