import importlib.util, pathlib, sys, tempfile, json
import os, pathlib as _pl
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)

spec = importlib.util.spec_from_file_location(
    "cap", pathlib.Path(SCRIPTS) / "capture.py")
cap = importlib.util.module_from_spec(spec); spec.loader.exec_module(cap)

class StubPage:
    """A 22,789px page whose height grows as lazy content mounts."""
    def __init__(self, real_height=22789, lazy_extra=3000):
        self.y = 0; self.max_y = 0; self.shots = []
        self.height = 8000; self.real = real_height; self.lazy = lazy_extra
    def set_viewport_size(self, *a, **k): pass
    def wait_for_timeout(self, *a): pass
    def screenshot(self, path=None, full_page=False): self.shots.append(str(path))
    def evaluate(self, expr):
        if "scrollHeight" in expr and "scrollTo" not in expr:
            # page grows toward its real height as we scroll (lazy mounting)
            self.height = min(self.real, self.height + self.lazy)
            return self.height
        if "scrollTo(0, document.body.scrollHeight)" in expr:
            self.y = self.height; self.max_y = max(self.max_y, self.y); return None
        if "scrollTo" in expr:
            self.y = int(expr.split(",")[1].strip(" )")); self.max_y = max(self.max_y, self.y)
            return None
        return {"ok": True}

out = pathlib.Path(tempfile.mkdtemp())
p = StubPage()
cap.capture_at_width(p, "window.__designCapture={ok:1}", 1440, 900, out, True)

PASS, FAIL = [], []
def check(n, c, d=''):
    (PASS if c else FAIL).append(n)
    print(f'{"PASS" if c else "FAIL"}  {n}{"  — " + d if d and not c else ""}')

check('scroll reached the true bottom of a 22,789px page',
      p.max_y >= p.real, f'max_y={p.max_y} of {p.real}')
scroll_shots = [s for s in p.shots if 'scroll-' in s]
check('screenshot budget still capped at 12', len(scroll_shots) == 12, str(len(scroll_shots)))
check('scrolling was NOT capped by the screenshot budget',
      p.max_y > 12 * 900, f'max_y={p.max_y}, budget would have stopped at {12*900}')
check('full-page screenshot still taken', any('full-' in s for s in p.shots))
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
sys.exit(1 if FAIL else 0)
