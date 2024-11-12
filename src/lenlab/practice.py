import logging

from .flash import flash
from .profile import profile
from .sys_info import sys_info

logger = logging.getLogger(__name__)


def practice():
    sys_info()
    flash()
    profile()
