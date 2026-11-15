import sys
sys.argv=[sys.argv[0], sys.argv[1]]
exec(open(sys.argv[0].replace('debug.py','analyze.py')).read().split("print('flashes:'")[0])
for k in (3,4,7):
    print(k, shapes[k][0], round(shapes[k][1],4), round(shapes[k][2],4), [round(v,4) for v in (shapes[k][3] or [])], shapes[k][4])
    print('  core_box', [round(v,4) for v in core_box(shapes[k])])
