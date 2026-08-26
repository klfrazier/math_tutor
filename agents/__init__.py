"""Loads the openai-agents SDK (whose top-level package is also named
``agents``) and exposes this project's own agents/*.py submodules via a
meta_path finder.

The SDK requires being importable as ``agents`` for its internal relative
imports (e.g. ``from . import _config``). Because this project's local
package is also named ``agents`` (per agents.md Section 3.3), we bind
``sys.modules["agents"]`` to the real SDK and install a finder that
resolves ``agents.session_state`` and ``agents.math_tutor`` to the local
files on demand. Loading the SDK here, in the package __init__, guarantees
it is in place before any ``agents.*`` submodule is imported.
"""

import importlib.abc
import importlib.util
import os
import sys

_SDK_SITE = "/home/vscode/.local/lib/python3.13/site-packages"
_SDK_DIR = os.path.join(_SDK_SITE, "agents")
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_SUBMODULES = ("session_state", "math_tutor")


class _LocalAgentsSubmoduleFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        prefix = "agents."
        if not fullname.startswith(prefix):
            return None
        name = fullname[len(prefix):]
        if name not in _LOCAL_SUBMODULES:
            return None
        mod_path = os.path.join(_PROJECT_DIR, f"{name}.py")
        if not os.path.exists(mod_path):
            return None
        return importlib.util.spec_from_file_location(fullname, mod_path)


if not hasattr(sys.modules.get("agents"), "Runner"):
    for _k in list(sys.modules.keys()):
        if _k == "agents" or _k.startswith("agents."):
            del sys.modules[_k]
    _spec = importlib.util.spec_from_file_location(
        "agents",
        os.path.join(_SDK_DIR, "__init__.py"),
        submodule_search_locations=[_SDK_DIR],
    )
    _sdk = importlib.util.module_from_spec(_spec)
    sys.modules["agents"] = _sdk
    _spec.loader.exec_module(_sdk)
    if not any(isinstance(f, _LocalAgentsSubmoduleFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _LocalAgentsSubmoduleFinder())
else:
    _sdk = sys.modules["agents"]

Agent = _sdk.Agent
Runner = _sdk.Runner
function_tool = _sdk.function_tool
