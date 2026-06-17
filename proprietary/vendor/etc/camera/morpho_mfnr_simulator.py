#!/usr/bin/env python
import os
import shutil
import platform
import sys

SLAKVER         = "2022.11.14"
PROJECTS        = "mfnr"
ARM_VER         = "arm64-v8a"
SIMULATOR_PATH  = "/data/local/tmp/morpho_" + PROJECTS
SIMULATOR       = SIMULATOR_PATH + "/morpho_" + PROJECTS+"_simulator"
XML_FILE        = SIMULATOR_PATH + "/morpho_" + PROJECTS+"_params.xml"
INPUT_YUV_PATH  = SIMULATOR_PATH + "/yuv"
OUTPUT_PATH     = SIMULATOR_PATH  + "/output"
INPUT_DIR       = "input"
RUN_TIMES       = 1
BATCH_FLAG      = 1
YUV_EXT         = [".yuv", ".YUV", ".nv21", ".NV21", ".nv12", ".NV12", "P010", "p010"]
REMOTE_PATH     = "/data/local/tmp/ODM/mfnr"
REMOTE_FLAG     = 0
REMOTE_SCRIPTS  = "morpho_mfnr_simulator_ext.sh"
ADBDEVICES      = "adb"
ZOOM_RATIO      = "0"
EXTERN_SELECT_BASE  = "1"
FACE_ENABLE     = 0
MERGE_NUM       = 0

def help():
    print("Usage:")
    print("[Windows   Platform]: python morpho_mfnr_simulator.py [-n run_times] [-d input_direcory] [-h]")
    print("[Linux/Mac Platform]: ./morpho_mfnr_simulator.py [-n run_times] [-d input_direcory] [-h]")
    print("-n : specify the simulation times for one input, if not set, default is 1")
    print("-d : specify the input directory, only for single input, not for batch runing")
    print("     if not set, the default directory is ./input and will simulate all sub input directories. ")
    return

def adb_exec(cmd):
    print(cmd)
    os.system(cmd);

def check_argv():
    global INPUT_DIR
    global BATCH_FLAG
    global RUN_TIMES

    argc = len(sys.argv)

    for i in range(1, argc):
        if sys.argv[i] == "-h":
            help()
            sys.exit(0)
        if sys.argv[i] == "-n":
            i = i + 1
            if i >= argc:
                print("Error: Invalid argv in [-n]")
                sys.exit(0)

            RUN_TIMES = int(sys.argv[i])
            if RUN_TIMES <= 1: 
                print("Error: Invalid argv in [-n], run_times = " + str(RUN_TIMES))
                sys.exit(0)
            
        if sys.argv[i] == "-d":
            i = i + 1
            if i >= argc:
                print("Error: Invalid argv in [-d]")
                sys.exit(0)
            
            INPUT_DIR = sys.argv[i]
            BATCH_FLAG = 0
            if os.path.exists(INPUT_DIR) != True and REMOTE_FLAG != 1:
                print("Error: Invalid input dir in [-d]: " + INPUT_DIR)
                sys.exit(0)
    
    print("ARM_VER     = " + ARM_VER)
    print("RUN_TIMES   = " + str(RUN_TIMES))
    print("BATCH_FLAG  = " + str(BATCH_FLAG))
    print("INPUT_DIR   = " + INPUT_DIR)
        
    return

def build_simualtion_env():
    print ("Build Simulation Directory: " + SIMULATOR_PATH)
    # cmd = ADBDEVICES + " shell rm -rf " + SIMULATOR_PATH
    # adb_exec(cmd)
    cmd = ADBDEVICES + " shell rm -rf " + OUTPUT_PATH
    adb_exec(cmd)

    cmd = ADBDEVICES + " shell mkdir " + SIMULATOR_PATH
    adb_exec(cmd)
    cmd = ADBDEVICES + " shell mkdir " + REMOTE_PATH
    adb_exec(cmd)
    cmd = ADBDEVICES + " shell mkdir " + INPUT_YUV_PATH
    adb_exec(cmd)
    cmd = ADBDEVICES + " shell mkdir " + OUTPUT_PATH
    adb_exec(cmd)

    cmd = ADBDEVICES + " shell setprop debug.morpho." + PROJECTS + ".face_enable %s" % (FACE_ENABLE)
    adb_exec(cmd);
    cmd = ADBDEVICES + " shell setprop debug.morpho." + PROJECTS + ".merge_num %s" % (MERGE_NUM)
    adb_exec(cmd);

    if os.path.exists("libs/" + ARM_VER) == True:
        dir = "libs/" + ARM_VER
    elif os.path.exists(ARM_VER) == True:
        dir = ARM_VER
    else:
        print("Can't find simulator and library.")
        exit(0)

    files = os.listdir(dir)
    for file in files:
        cmd = ADBDEVICES + " push " + dir + "/" + file + " " + SIMULATOR_PATH
        adb_exec(cmd)

    cmd = ADBDEVICES + " shell chmod 777 " + SIMULATOR
    adb_exec(cmd)
    
    return

def push_tuning_file_to_device():
    dirs = os.listdir(".")

    for file in dirs:
        if os.path.isfile(file) == True:
            if file.endswith(".xml") == True:
                cmd = ADBDEVICES + " push " + file + " " + SIMULATOR_PATH
                adb_exec(cmd)
    return

def pull_simulation_result(dir):
    cmd = ADBDEVICES + " pull " + SIMULATOR_PATH + "/output/ ."
    adb_exec(cmd)

    cmd = ADBDEVICES + " shell rm " + SIMULATOR_PATH + "/output/*"
    adb_exec(cmd)

    dir = dir.split("/")[-1]
    output_dir = "output/" + dir
    
    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)

    files = os.listdir("output")
    for file in files:
        if (file.endswith(".jpeg") == True) or (file.endswith(".jpg") == True):
            dir = os.getcwd()
            src = os.path.join(dir, "output", file)
            dst = os.path.join(dir, output_dir, file)
            shutil.move(src, dst)
            #break
    return

def simulate(input_dir):
    print("#########Simulate Input Directory: " + input_dir)

    cmd = ADBDEVICES + " shell rm -rf " + INPUT_YUV_PATH + "/*"
    adb_exec(cmd)

    dirs = os.listdir(input_dir)
    for file in dirs:
        if file.endswith(".xml") == True:
            cmd = ADBDEVICES + " push " + input_dir + "/" + file + " " + SIMULATOR_PATH
            adb_exec(cmd)
            continue

        for ext in YUV_EXT:
            if file.endswith(ext) == True:
                if platform.system().lower() != "windows":
                    file=file.replace("(", "\(")
                    file=file.replace(")", "\)")

                cmd = ADBDEVICES + " push " + input_dir + "/" + file + " " + INPUT_YUV_PATH
                adb_exec(cmd)
                break

    #Start simulating
    EXECUTOR = "LD_LIBRARY_PATH=" + SIMULATOR_PATH + ":/vendor/lib64:/system/lib64:/system/apex/com.android.runtime.release/lib ." + SIMULATOR  

    cmd = "adb shell " + EXECUTOR + " -o " + OUTPUT_PATH + " -x " + XML_FILE + " -n " + str(RUN_TIMES) + " -i " + INPUT_YUV_PATH +"/*" 
    print(cmd)
    os.system(cmd)

    pull_simulation_result(input_dir)
    return

def foreach_input_dir():
    dirs = os.listdir(INPUT_DIR)

    for dir in dirs:
        if os.path.isfile(dir) == True:
            continue

        simulate(INPUT_DIR+"/"+dir)
    return

def simulate_remote(remote_dir):
    print("#########Simulate Remote Directory: " + remote_dir)
    cmd = ADBDEVICES + ' push ' + REMOTE_SCRIPTS + " " + SIMULATOR_PATH
    adb_exec(cmd)

    cmd = ADBDEVICES + ' shell chmod +x ' + os.path.join(SIMULATOR_PATH, REMOTE_SCRIPTS)
    adb_exec(cmd)

    if BATCH_FLAG == 1:
        cmd = ADBDEVICES + ' shell ' + os.path.join(SIMULATOR_PATH, REMOTE_SCRIPTS) + " " + REMOTE_PATH + " " + str(RUN_TIMES)
    else: 
        cmd = ADBDEVICES + ' shell ' + os.path.join(SIMULATOR_PATH, REMOTE_SCRIPTS) + " -d " + INPUT_DIR + " " + str(RUN_TIMES)
    print(cmd)
    os.system(cmd)

    cmd = ADBDEVICES + " pull " + os.path.join(SIMULATOR_PATH, 'output')
    print(cmd)
    os.system(cmd)


def batch_simulate():
    print ("PYAKVER= " + SLAKVER )
    print ("############################################ Simulation Start #################################################")

    check_argv()
    build_simualtion_env()
    push_tuning_file_to_device()

    if REMOTE_FLAG == 1:
        simulate_remote(REMOTE_PATH)
        return True

    if BATCH_FLAG == 0:
        simulate(INPUT_DIR)
    else:
        foreach_input_dir()

    print ("############################################ Simulation End #################################################")
    return

def chi():
    batch_simulate()

if __name__ == "__main__":
    chi()
