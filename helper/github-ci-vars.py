import datetime
import json
import re
import subprocess

envs = subprocess.check_output(['tox', '-l']).decode().rstrip().split('\n')
matrix = []

for env in envs:
    version = re.search(r'^py(?P<major>\d)(?P<minor>\d+)-', env)

    # github "commit" checks will fail even though workflow passes overall.
    # temp remove the optional targets to make github CI work.
    if 'master' in env:
        continue

    matrix.append({
        'toxenv': env,
        'python-version': f'{version.group("major")}.{version.group("minor")}',
        'experimental': bool('master' in env)
    })

print(f"::set-output name=date::{datetime.date.today()}")
print(f"::set-output name=matrix::{json.dumps(matrix)}")
