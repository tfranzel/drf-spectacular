import datetime
import json
import os
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

with open(os.environ['GITHUB_OUTPUT'], "a") as fh:
    fh.write(f"date={datetime.date.today()}\n")
    fh.write(f"matrix={json.dumps(matrix)}\n")
