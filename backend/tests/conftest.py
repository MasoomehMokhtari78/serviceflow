import sys
from os.path import dirname, abspath

backend_dir = dirname(dirname(abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
