import importlib, subprocess, sys
import pr_render
for k in sys.argv[1:]:
    c = importlib.import_module("sch_" + k.lower()).build()
    u = c.units(); a = c.area_by_use()
    print(k, u)
    print("  ", {x: round(y) for x, y in a.items()})
    print("   total", round(sum(a.values())))
    pr_render.preview(c, "out/pr_%s.html" % k)
    subprocess.run(["node", "shot.js", "png", "out/pr_%s.html" % k, "out/pr_%s.png" % k, "2600"], check=True)
