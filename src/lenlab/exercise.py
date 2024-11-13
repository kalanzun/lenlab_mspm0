import logging

from .flash import flash
from .profile import profile
from .sys_info import sys_info

logger = logging.getLogger(__name__)


def exercise():
    sys_info()
    flash()
    # profile(n=10_000)  # 54 minutes
    profile(n=1_000)  # 6 minutes
