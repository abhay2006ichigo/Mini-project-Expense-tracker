import sys
import os

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import importlib.util
spec = importlib.util.spec_from_file_location("main_app", os.path.join(_parent_dir, "app.py"))
if spec and spec.loader:
    main_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_app)
    app = main_app.app
    application = app
