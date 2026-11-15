# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Make a defective copy of the native schematic for the ERC exit test (T5). Host script.

  uv run scripts/make_defective_sch.py IN.kicad_sch OUT.kicad_sch

It deletes all net labels that have the text of the first label. The pins that these labels named have no net then.
(Earlier versions of this script were wrong. Version 1 deleted one label of a net with other labels: no violation, log
`T5_erc_171`. Version 2 damaged the file: logs `T5_erc_b_172` and `T5_erc_c_173`. Both started the block scan at the tab and not at the parenthesis.)
Exit status: 0 done, 2 incorrect input.
"""

import re
import sys
from pathlib import Path


def block_end(text: str, start: int) -> int:
    depth, i = 0, start
    while True:
        depth += 1 if text[i] == "(" else -1 if text[i] == ")" else 0
        i += 1
        if depth == 0:
            return i


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or not Path(args[0]).is_file():
        print("make_defective_sch: give the input schematic and the output file")
        return 2
    text = Path(args[0]).read_text()
    first = re.search(r'\n\t\(label "([^"]*)"', text)
    if not first:
        print("make_defective_sch: the schematic has no net label")
        return 2
    name = first.group(1)
    spans = [(m.start(), block_end(text, m.start() + 2)) for m in re.finditer(r'\n\t\(label "' + re.escape(name) + '"', text)]
    for start, end in reversed(spans):
        text = text[:start] + text[end:]
    Path(args[1]).write_text(text)
    print(f"removed {len(spans)} labels named {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
