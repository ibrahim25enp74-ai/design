"""Build one or more concepts, print the key figures and write preview PNGs."""
import importlib
import subprocess
import sys

import render

for key in sys.argv[1:]:
    m = importlib.import_module("concept_" + key.lower())
    plan = m.build()
    u = plan.units()
    lu = plan.landuse()
    print("== %s %s" % (plan.key, plan.name))
    print("units V %(V)d D %(D)d M2 %(M2)d M3 %(M3)d total %(total)d pop %(pop)d" % u)
    tot = sum(lu.values())
    for k, v in lu.items():
        print("  %-9s %8.0f  %5.1f%%" % (k, v, 100 * v / tot))
    print("  total     %8.0f   leftover %.0f" % (tot, plan.leftover.area))
    for k, v in plan.detail.items():
        tgt = plan.parcels[k].get("target")
        print("    %-12s %7.0f %s" % (k, v, "(target %d)" % tgt if tgt else ""))
    render.preview(plan, "out/prev_%s.html" % key)
    subprocess.run(["node", "shot.js", "png", "out/prev_%s.html" % key, "out/prev_%s.png" % key, "2400"], check=True)
