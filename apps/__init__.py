"""App profiles. Each module defines NAME, PACKAGE, TITLE and run(d, outdir, count, interval).

Add an app by writing a module here and listing it in APPS.
"""

from . import thermal_imager

APPS = {m.NAME: m for m in (thermal_imager,)}
