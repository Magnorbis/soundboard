import voicemeeterlib
from contextlib import contextmanager
import threading
import time

# -------------------- CONNECTION --------------------
@contextmanager
def vm_connect(mode="banana"):
    """
    Context manager for connecting to Voicemeeter.
    mode: "basic", "banana", or "potato"
    """
    vm = voicemeeterlib.api(mode)
    try:
        vm.login()
        ready = False
        for _ in range(20):
            try:
                _ = vm.strip[0].gain
                ready = True
                break
            except Exception:
                time.sleep(0.25)
        if not ready:
            raise RuntimeError("Voicemeeter not ready. Please open it first.")
        yield vm
    finally:
        try:
            vm.logout()
        except Exception:
            pass
