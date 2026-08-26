import sys
import os

_SDK_SITE = "/home/vscode/.local/lib/python3.13/site-packages"
_CWD = os.path.dirname(os.path.abspath(__file__))

_saved = {}
for _k in list(sys.modules.keys()):
    if _k == "agents" or _k.startswith("agents."):
        _saved[_k] = sys.modules.pop(_k)

_orig_path = sys.path[:]
sys.path = [p for p in sys.path if os.path.abspath(p) != _CWD]
if _SDK_SITE not in sys.path:
    sys.path.insert(0, _SDK_SITE)

import agents as _sdk  # noqa: E402

Agent = _sdk.Agent
Runner = _sdk.Runner
function_tool = _sdk.function_tool

_sdk_mods = {}
for _k in list(sys.modules.keys()):
    if _k == "agents" or _k.startswith("agents."):
        _sdk_mods[_k] = sys.modules.pop(_k)

for _k, _v in _saved.items():
    sys.modules[_k] = _v

sys.modules["_openai_agents_sdk"] = _sdk
for _k, _v in _sdk_mods.items():
    _new_key = "_openai_agents_sdk" + _k[len("agents"):]
    sys.modules[_new_key] = _v
    _v.__name__ = _new_key

sys.path = _orig_path
