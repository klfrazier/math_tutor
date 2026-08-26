"""Bootstraps the openai-agents SDK, whose top-level package is also named
``agents`` -- the same name as this project's local ``agents/`` directory
(per agents.md Section 3.3). We resolve the collision by:

1. Temporarily removing the project directory from sys.path so the real
   SDK package is what gets imported under the name "agents".
2. Keeping that SDK module permanently bound to sys.modules["agents"],
   since the SDK performs lazy internal relative imports (e.g. tracing)
   at arbitrary points during Runner.run(), which only resolve correctly
   if "agents" keeps pointing to the SDK for the lifetime of the process.
3. Installing a sys.meta_path finder that resolves "agents.session_state"
   and "agents.math_tutor" to this project's own agents/*.py files on
   demand (lazily, the first time something actually imports them), so
   normal "from agents.math_tutor import math_tutor_agent" style imports
   keep working without ever falling back to Python's default package
   finder for the local agents/ directory (which would re-trigger the
   name collision), and without forcing an eager, circular load order.
"""

import importlib.abc
import importlib.util
import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_SDK_SITE = "/home/vscode/.local/lib/python3.13/site-packages"
_LOCAL_SUBMODULES = ("session_state", "math_tutor")


class _LocalAgentsSubmoduleFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        prefix = "agents."
        if not fullname.startswith(prefix):
            return None
        name = fullname[len(prefix):]
        if name not in _LOCAL_SUBMODULES:
            return None
        mod_path = os.path.join(_PROJECT_DIR, "agents", f"{name}.py")
        if not os.path.exists(mod_path):
            return None
        return importlib.util.spec_from_file_location(fullname, mod_path)


if not hasattr(sys.modules.get("agents"), "Runner"):
    for _k in list(sys.modules.keys()):
        if _k == "agents" or _k.startswith("agents."):
            del sys.modules[_k]

    _orig_path = sys.path[:]
    sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _PROJECT_DIR]
    if _SDK_SITE not in sys.path:
        sys.path.insert(0, _SDK_SITE)

    import agents as _sdk  # noqa: E402

    sys.path = _orig_path

    if not any(isinstance(f, _LocalAgentsSubmoduleFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _LocalAgentsSubmoduleFinder())
else:
    _sdk = sys.modules["agents"]

Agent = _sdk.Agent
Runner = _sdk.Runner
function_tool = _sdk.function_tool
