"""App profiles. Each module defines NAME, TITLE, PACKAGE and ROUTINES.

ROUTINES maps a routine name to fn(d, outdir, count=, interval=, duration=, pull=);
the first entry is the default. Add an app by writing a module here and listing it in APPS.
"""

from . import thermal_imager

APPS = {m.NAME: m for m in (thermal_imager,)}
