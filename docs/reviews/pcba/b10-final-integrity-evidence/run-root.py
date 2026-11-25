# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "openpyxl==3.1.5", "pyyaml==6.0.3", "xlrd==2.0.1"]
# ///
from pathlib import Path
import runpy,tempfile,shutil,subprocess,json,hashlib
root=Path('/mnt/storage/projects/cad-skills-worktrees/pcba')
m=runpy.run_path(str(root/'tests/test_pcba_design.py'))
evidence=root/'docs/reviews/pcba/b10-final-integrity-evidence'
evidence.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    project=m['standard_copy'](Path(tmp))
    code,out,err=m['run_package'](project,package_id='pkg-standard')
    (evidence/'package-run.json').write_text(out)
    (evidence/'package-run.stderr').write_text(err)
    print('Package exit',code,flush=True)
    if code: raise SystemExit(code)
    package=project/'out/pcba/packages/pkg-standard'
    retained=root/'tests/fixtures/pcba-design/retained'
    shutil.rmtree(retained/'pkg-standard')
    shutil.copytree(package,retained/'pkg-standard')
code,out,err=m['run_check'](m['STANDARD'],retained/'pkg-standard')
(retained/'validator-result.json').write_text(out)
(evidence/'validator-run.stderr').write_text(err)
print('Full validator exit',code,flush=True)
if code: raise SystemExit(code)
copy_log=[]
skill=root/'skills/pcba-design'
for line in (skill/'COPY_SHA256.txt').read_text().splitlines():
    digest,name=line.split(maxsplit=1)
    name=name.strip()
    measured=hashlib.sha256((skill/name).read_bytes()).hexdigest()
    if measured != digest: raise RuntimeError(name)
    copy_log.append(f'PASS {name} {measured}')
(evidence/'copies.log').write_text('\n'.join(copy_log)+f'\n{len(copy_log)}/{len(copy_log)} pass\nExit: 0\n')
print('Copies',len(copy_log),flush=True)
log=evidence/'focused-run.log'
with log.open('w') as out:
    out.write('Command: uv run tests/test_pcba_design.py\n')
    out.flush()
    result=subprocess.run(['uv','run','tests/test_pcba_design.py'],cwd=root,stdout=out,stderr=subprocess.STDOUT)
    out.write(f'\nExit: {result.returncode}\n')
print('\n'.join(log.read_text().splitlines()[-8:]),flush=True)
raise SystemExit(result.returncode)
