#!/usr/bin/env python3

from pathlib import Path
import re

pyproject = Path("pyproject.toml")

text = pyproject.read_text(encoding="utf-8")

pattern = re.compile(
    r'^(\s*license\s*=\s*)"([^"]+)"\s*$',
    re.MULTILINE,
)

new_text, count = pattern.subn(
    r'\1{ text = "\2" }',
    text,
)

if count:
    pyproject.write_text(new_text, encoding="utf-8")
    print(f"Patched {count} license field(s) in pyproject.toml")
else:
    print("No SPDX string license field found; nothing to patch")