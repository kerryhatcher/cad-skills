from pathlib import Path
p = Path("/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/geom-trial/analyze.py")
s = p.read_text()
old = "    if kind == 'circle': return (x - r, y - r, x + r, y + r)"
new = "    if kind == 'circle': return (x, y, x, y)  # a circle core is its centre; its radius enters once"
assert s.count(old) == 1
p.write_text(s.replace(old, new))
print("fixed")
