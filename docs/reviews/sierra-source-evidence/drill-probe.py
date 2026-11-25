# /// script
# requires-python = ">=3.11"
# ///
"""Measure the inch drill export on a temporary copy of the trial board."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

root = pathlib.Path('/mnt/storage/projects/cad-skills')
source = root / 'examples/pcb-trial/results/final_r2/trial.kicad_pcb'
work = pathlib.Path(tempfile.mkdtemp(prefix='b9-drill-root-'))
shutil.copyfile(source, work / 'board.kicad_pcb')
image = 'sha256:b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f'
command = ['podman', 'run', '--rm', '--pull=never', '--network', 'none',
           '--security-opt', 'label=disable', '-v', f'{work}:/work:rw', '-w', '/work', image,
           'kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon',
           '--drill-origin', 'absolute', '--excellon-units', 'in',
           '--excellon-zeros-format', 'suppresstrailing', '--excellon-separate-th',
           '--output', '/work/drill', '/work/board.kicad_pcb']
run = subprocess.run(command, capture_output=True, text=True, timeout=30)
result = {'command': command, 'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr,
          'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'work': str(work), 'files': []}
for file in sorted((work / 'drill').glob('*')):
    if file.is_file():
        result['files'].append({'path': str(file), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                                'text': file.read_text()})
out = root / 'docs/reviews/sierra-source-evidence/drill-probe.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
