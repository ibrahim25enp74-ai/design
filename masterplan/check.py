import importlib, sys, json, time
import analysis
for key in sys.argv[1:]:
    t=time.time()
    plan = importlib.import_module("concept_" + key.lower()).build()
    m = analysis.analyze(plan)
    print("==", key, "%.1fs" % (time.time()-t))
    for k in ("gross_pop_density","tower_net_units_ha","tower_far","landuse_balance","green_pc","green_total_pc","homes_on_green",
              "road_len_total","road_len_per_unit","road_area_share","directness","drive_mean","drive_max","through_local_m",
              "overlooked","front_on_main_road","shaded_homes","orientation_ok","sellable","d_edu","d_util","d_waste","d_fence",
              "d_tower_fence","tower_sep","front_min","rear_min","trees","wadi_intrusions"):
        v=m[k]; print("  %-20s %s" % (k, ("%.2f" % v) if isinstance(v,float) else v))
    for k,v in m["walk"].items(): print("  walk %-7s within %.0f%% max %.0f mean %.0f" % (k, 100*v["within"], v["max"], v["mean"]))
    for r in analysis.compliance(m):
        if not r[3]: print("  FAIL", r[0], r[1], r[2])
