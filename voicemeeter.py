from voicemeeterlib import api
from contextlib import contextmanager
import time

# Holds the active Voicemeeter API instance
vm = None

# Create and manage a Voicemeeter connection lifecycle
@contextmanager
def vm_connect(mode="banana"):
    global vm
    vm = api(mode)
    try:
        vm.login()

        # Wait until Voicemeeter is fully ready
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
