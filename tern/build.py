"""Build Tern on a Windows machine, resumable across GitHub Actions jobs.

Every step skips itself when its output already exists, so a job that unpacks
the previous job's work tree simply carries on.

Usage: python -I build.py --root D:\\t --version 158.0.8127.37 [--stop-at <unix time>]
Exit codes: 0 built and packaged, 124 stopped at --stop-at (resume in the next job).
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEPOT_TOOLS = 'https://chromium.googlesource.com/chromium/tools/depot_tools.git'
STOPPED = 124


def run(cmd, cwd, env, stop_at=None):
    print('+', ' '.join(map(str, cmd)), flush=True)
    if stop_at is None:
        subprocess.run(cmd, cwd=cwd, env=env, check=True, shell=os.name == 'nt')
        return
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, shell=os.name == 'nt')
    try:
        proc.wait(timeout=max(1, stop_at - time.time()))
    except subprocess.TimeoutExpired:
        print('build: time is up for this job, stopping the build to resume in the next one', flush=True)
        if os.name == 'nt':
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], check=False)
        else:
            proc.kill()
        proc.wait()
        sys.exit(STOPPED)
    if proc.returncode:
        sys.exit(f'build: {cmd[0]} failed with exit code {proc.returncode}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--version', required=True)
    ap.add_argument('--stop-at', type=float, default=None)
    a = ap.parse_args()
    root, src = a.root, a.root / 'src'
    root.mkdir(parents=True, exist_ok=True)
    dt = root / 'depot_tools'
    env = dict(os.environ, DEPOT_TOOLS_WIN_TOOLCHAIN='0', PATH=f'{dt}{os.pathsep}{os.environ["PATH"]}')

    # 1. depot_tools (Google's checkout and build tools)
    if not (dt / 'gclient.py').exists():
        run(['git', 'clone', '--depth=1', DEPOT_TOOLS, str(dt)], root, env)
        run(['gclient', '--version'], root, env)  # bootstraps its Python and tools

    # 2. Chromium source at the release tag, without git history, plus Google's
    #    toolchain (clang, rust, gn, PGO profiles) through the hooks.
    synced = root / '.synced'
    if not synced.exists() or synced.read_text().strip() != a.version:
        if src.exists():
            sys.exit(f'build: {src} exists from another version; start from an empty --root')
        (root / '.gclient').write_text(
            'solutions = [{"name": "src", "managed": False, "custom_deps": {},\n'
            f'  "url": "https://chromium.googlesource.com/chromium/src.git@refs/tags/{a.version}",\n'
            '  "custom_vars": {"checkout_pgo_profiles": True}}]\n'
            'target_os = ["win"]\n')
        run(['gclient', 'sync', '--no-history', '--shallow', '--nohooks', '-j8'], root, env)
        run(['gclient', 'runhooks'], root, env)
        synced.write_text(a.version)

    # 3. Tern branding (marks itself done inside src)
    run([sys.executable, '-I', str(HERE / 'apply.py'), str(src)], root, env)

    # 4. Build configuration
    out = src / 'out' / 'Tern'
    if not (out / 'build.ninja').exists():
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / 'args.gn', out / 'args.gn')
        run(['gn', 'gen', r'out\Tern'], src, env)

    # 5. Compile (stops at --stop-at, the next job resumes)
    run(['autoninja', '-C', r'out\Tern', 'chrome'], src, env, a.stop_at)

    # 6. Package
    credits = out / 'credits.html'
    if not credits.exists():
        with open(credits, 'w', encoding='utf-8') as f:
            subprocess.run([sys.executable, r'tools\licenses\licenses.py', 'credits'],
                           cwd=src, env=env, check=True, stdout=f)
    shutil.copyfile(src / 'LICENSE', out / 'LICENSE')
    run([sys.executable, '-I', str(HERE / 'package.py'), str(src), str(out),
         str(root / f'tern-{a.version}-win-x64.zip')], root, env)


if __name__ == '__main__':
    main()
