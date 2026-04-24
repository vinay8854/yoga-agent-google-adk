import pathlib, sys

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))

# 1. Syntax check all Python files
files = ['skill_loader.py', 'agent.py', 'run_test.py']
all_ok = True
for f in files:
    fpath = BASE / f
    try:
        src = fpath.read_text(encoding='utf-8')
        compile(src, f, 'exec')
        print(f'  OK  {f}')
    except SyntaxError as e:
        print(f'  FAIL  {f}  SyntaxError: {e}')
        all_ok = False

# 2. Skills loading check
if all_ok:
    print()
    from skill_loader import SkillManager
    mgr = SkillManager('yoga')
    names = [s['name'] for s in mgr.skills]
    prompt = mgr.get_full_instructions()
    print(f'  Skills loaded : {names}')
    print(f'  Prompt length : {len(prompt)} chars')
    print()
    print('All checks passed — ready to run!')
