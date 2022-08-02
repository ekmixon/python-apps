import yaml
import os
import subprocess


basedir = "."
dirs = os.listdir(basedir)
#print(dirs)
#basename = "testing"
for basename in dirs:
    if basename == ".gitignore" or basename == ".github" or basename == "README.md" or basename == ".git" or basename == "unsupported" or ".swp" in basename or ".swo" in basename:
        continue

    print(f"\n[DEBUG] Analyzing: {basename}")
    try:
        versions = os.listdir(f"./{basename}")
    except NotADirectoryError:
        continue

    for version in versions:
        filepath = f"{basename}/{version}/api.yaml"

        try:
            with open(filepath, "r") as tmp:
                try:
                    ret = yaml.full_load(tmp.read())
                except yaml.scanner.ScannerError as e:
                    print(f"Bad yaml in {filepath} (2): {e}")
                    continue

                newname = ret["name"].lower().replace(" ", "-", -1).replace(".", "-", -1)
                if newname != basename:
                    print(f"Bad name: {basename} vs {newname}")

                if ret["app_version"] != version:
                    print(f'Bad version ({basename}): {version} vs {ret["app_version"]}')
                            #else:
                            #    print("%s:%s is valid" % (basename, version))
        except (NotADirectoryError, FileNotFoundError) as e:
            #print("Error inner file: %s" % e)
            pass

    try:
        subfolders = os.listdir(f"{basedir}/{basename}")
    except:
        continue

    for subfolder in subfolders:
        apifile = f"{basedir}/{basename}/{subfolder}/api.yaml"
        pythonfile = f"{basedir}/{basename}/{subfolder}/src/app.py"

        action_names = []
        try:
            with open(apifile, "r") as tmp:
                try:
                    apidata = yaml.full_load(tmp.read())
                except yaml.scanner.ScannerError as e:
                    print(f"Bad yaml in {apifile} (2): {e}")
                    continue

                action_names.extend(item["name"] for item in apidata["actions"])
        except NotADirectoryError as e:
            continue

        with open(pythonfile, "r") as tmp:
            pythondata = tmp.read()
            for action_name in action_names:
                if action_name not in pythondata:
                    print(f"===> Couldn't find action \"{action_name}\" from {apifile} in script {pythonfile}") 

            code = f"python3 {pythonfile}"
            process = subprocess.Popen(
                code,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,  # nosec
            )
            stdout = process.communicate()
            item = ""
            if len(stdout[0]) > 0:
                #print("Succesfully ran bash!")
                item = stdout[0]
            else:
                item = stdout[1]
                if "ModuleNotFoundError" in item:
                    continue

                print(f"FAILED to run bash with code {code}: {item}")




    #break


#for item in 
