# Import certain modules based on python version
# so we're compatible with multiple versions of python

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from Queue import Queue
except ImportError:
    from queue import Queue
