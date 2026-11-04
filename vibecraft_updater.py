import os, sys, time, shutil, zipfile, tempfile
from pathlib import Path

def wait_pid(pid):
    if not pid: return
    deadline=time.time()+60
    while time.time()<deadline:
        try:
            os.kill(pid, 0)
            time.sleep(0.4)
        except OSError:
            return
    # Give Windows a little more time to release open files.
    time.sleep(2)

def main():
    if len(sys.argv)<4: return 2
    archive=Path(sys.argv[1]).resolve(); target=Path(sys.argv[2]).resolve(); pid=int(sys.argv[3])
    wait_pid(pid)
    temp=Path(tempfile.mkdtemp(prefix='vibecraft_update_'))
    try:
        with zipfile.ZipFile(archive,'r') as z:
            z.extractall(temp)
        candidates=list(temp.rglob('vibecraft.py'))
        if not candidates: raise RuntimeError('В архиве не найден vibecraft.py')
        source=candidates[0].parent
        # Only copy launcher files; preserve user data and Minecraft folders.
        for item in source.iterdir():
            if item.name in {'.git', '__pycache__', 'updates', 'accounts.sqlite3', 'config.json'}: continue
            dest=target/item.name
            if item.is_dir():
                shutil.copytree(item,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.git','accounts.sqlite3','config.json'))
            else:
                shutil.copy2(item,dest)
        runbat=target/'run.bat'
        if runbat.exists():
            os.startfile(str(runbat))
        return 0
    except Exception as exc:
        try:
            (Path.home()/'VibeCraft'/'update_error.txt').write_text(str(exc),encoding='utf-8')
        except Exception: pass
        return 1
    finally:
        shutil.rmtree(temp,ignore_errors=True)

if __name__=='__main__':
    raise SystemExit(main())
