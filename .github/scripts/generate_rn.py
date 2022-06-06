version = "0.0.0"
with open("VERSION", "r+") as version_file:
    version = version_file.read()

rn = ""
with open("CHANGELOG.md","r+") as changelog:
    is_read = False
    for line in changelog.readlines():
        if version in line:
            is_read = True
        elif "---" in line:
            is_read = False
        elif (is_read == True) and (line != ""):
            rn += line

with open("release-notes.md", "w+") as release_notes:
    release_notes.write(rn)
