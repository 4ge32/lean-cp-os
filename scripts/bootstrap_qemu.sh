#!/bin/sh
# Unprivileged Debian/Ubuntu setup. APT verifies signed metadata and package hashes;
# packages are extracted into a workspace prefix, never installed over system files.
set -eu
qemu_prefix="${1:-/workspace/qemu-tools}"
python3 - "$qemu_prefix" <<'PY'
import os
import pathlib
import shlex
import subprocess
import sys
prefix = pathlib.Path(sys.argv[1]).resolve()
release = {}
for line in pathlib.Path('/etc/os-release').read_text().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        release[k] = v.strip('"')
arch = subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip()
if arch != 'amd64':
    raise SystemExit('This relocatable bootstrap supports amd64 hosts; use native package installation elsewhere.')
distro, codename = release.get('ID'), release.get('VERSION_CODENAME')
if distro == 'debian':
    source = f'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian {codename} main\n'
elif distro == 'ubuntu':
    source = f'deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu {codename} main universe\n'
else:
    raise SystemExit('Use your package manager to install qemu-system-arm on this host distribution.')
for name in ['etc/empty', 'lists/partial', 'cache/archives/partial', 'root', 'bin']:
    (prefix / name).mkdir(parents=True, exist_ok=True)
(prefix / 'etc/sources.list').write_text(source)
config = prefix / 'etc/apt.conf'
config.write_text(f'''Dir::Etc::main "/dev/null";
Dir::Etc::parts "{prefix}/etc/empty";
Dir::Etc::sourcelist "{prefix}/etc/sources.list";
Dir::Etc::sourceparts "-";
Dir::State::Lists "{prefix}/lists";
Dir::Cache "{prefix}/cache";
Debug::NoLocking "true";
''')
env = dict(os.environ, APT_CONFIG=str(config))
subprocess.run(['/usr/bin/apt-get', 'update'], check=True, env=env)
subprocess.run(['/usr/bin/apt-get', '--download-only', '--no-install-recommends', '-y',
                'install', 'qemu-system-arm'], check=True, env=env)
for package in sorted((prefix / 'cache/archives').glob('*.deb')):
    subprocess.run(['dpkg-deb', '-x', str(package), str(prefix / 'root')], check=True)
root = prefix / 'root'
qemu = root / 'usr/bin/qemu-system-aarch64'
if not qemu.is_file():
    # If already installed globally APT need not download it.
    qemu = pathlib.Path('/usr/bin/qemu-system-aarch64')
if not qemu.is_file():
    raise SystemExit('APT succeeded but qemu-system-aarch64 was not found.')
data = root / 'usr/share/qemu'
if not data.is_dir():
    data = pathlib.Path('/usr/share/qemu')
wrapper = prefix / 'bin/qemu-system-aarch64'
wrapper.write_text('#!/bin/sh\n' +
    'export LD_LIBRARY_PATH=' + shlex.quote(str(root / 'usr/lib/x86_64-linux-gnu')) +
    '${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}\nexec ' + shlex.quote(str(qemu)) +
    ' -L ' + shlex.quote(str(data)) + ' "$@"\n')
wrapper.chmod(0o755)
subprocess.run([str(wrapper), '--version'], check=True)
print('Set QEMU_SYSTEM_AARCH64=' + str(wrapper) + ' or add its bin directory to PATH.')
PY
