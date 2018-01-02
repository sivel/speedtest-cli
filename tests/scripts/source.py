#!/usr/bin/env python

import sys
import subprocess

cmd = [sys.executable, 'speedtest.py', '--source', '127.0.0.1']

p = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

stdout, stderr = p.communicate()

if p.returncode != 1:
    raise SystemExit('%s did not fail with exit code 1' % ' '.join(cmd))

if 'Invalid argument'.encode() not in stderr:
    raise SystemExit(
        '"Invalid argument" not found in stderr:\n%s' % stderr.decode()
    )
