import os
import sys

# Add calibreweb to sys.path, so we "import cps" works locally like it does when script is installed
for path in sys.path:
    if path.endswith("site-packages"):
        sys.path.append(os.path.join(path, 'calibreweb'))
