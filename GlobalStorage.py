"""
This file is used as a global storage for the software.
 This allows the import and export of variables without re-import stuff like omnipose that can leads
 to recompute things.
"""

RUN = None
def getRUN():
    return RUN
def setRUN(run):
    global RUN
    RUN = run