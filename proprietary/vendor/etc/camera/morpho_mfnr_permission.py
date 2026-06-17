#!/usr/bin/env python
import os
import shutil

#disable: 0; enable: 1
DEBUG_ENABLE = "1"
#disable: 0; error: 1; all: 2;
LOG_LEVEL = "2"
#disable: 0; dump input: 1; dump output: 2; dump all: 3;
DUMP_MASK ="0"
DUMP_PATH = "/data/local/tmp/morpho/mfnr/dump"
#disable: 0; enable: 1
DRAW_FACE_RECT = "0"
RUN_MODE = 0
# DUMP_BASE = 0
FACE_ENABLE=0
BYPASS    = 0
LOGO      = 1
adb       = "adb "

permission = {
        "debug.morpho.mfnr.enable" : DEBUG_ENABLE,
        "debug.morpho.mfnr.dump_path" : DUMP_PATH,
        "debug.morpho.mfnr.dump" : DUMP_MASK,
        "debug.morpho.mfnr.log_level" : LOG_LEVEL,
        "debug.morpho.mfnr.draw_face_rect" : DRAW_FACE_RECT,
        "debug.morpho.mfnr.draw_logo" : LOGO,
        # "debug.morpho.mfnr.run_mode" : RUN_MODE,
        "debug.morpho.mfnr.bypass" : BYPASS,
        # "debug.morpho.mfnr.dump_base" : DUMP_BASE,
        "debug.morpho.mfnr.face_enable" : FACE_ENABLE,
        }

def adb_exec(cmd):
    print(cmd)
    os.system(cmd);

def set_permission():
    print("------------------set_permission-------------------");
    cmd = adb + " root"
    print(cmd)
    os.system(cmd)

    cmd = adb + " remount"
    adb_exec(cmd)

    cmd = adb + " shell setenforce 0"
    adb_exec(cmd)

    cmd = adb + " shell logcat -G 200M"
    adb_exec(cmd)

    cmd = adb + " shell mkdir /data/local/tmp/morpho"
    adb_exec(cmd)

    cmd = adb + " shell mkdir -p %s" % (DUMP_PATH)
    adb_exec(cmd)

    cmd = adb + " shell chmod 777 %s -R" % (DUMP_PATH)
    adb_exec(cmd)

    for prop,val in permission.items():
        cmd = adb + " shell setprop %s %s" % (prop, val)
        adb_exec(cmd);

    print("------------------checker_permission-------------------");
    cmd = adb + " shell getenforce"
    adb_exec(cmd);

    for prop,val in permission.items():
        cmd = adb + " shell getprop %s" % (prop)
        adb_exec(cmd);

def chi():
    set_permission()

if __name__ == "__main__":
    chi()
