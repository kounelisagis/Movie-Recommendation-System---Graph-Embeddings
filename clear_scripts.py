import os
from shutil import copy

read_path = '1.scripts'
write_path = '2.scripts'

files = []
for r, d, f in os.walk(read_path):
    for file in f:
        try:
            with open(read_path + '\\' + file, encoding="utf8") as opened_file:
                read_data = opened_file.read()
                if 'INT' in read_data or 'EXT' in read_data:
                    new_file = file.replace(".txt", "")
                    if ",-The" in new_file:
                        new_file = "The-" + new_file.replace(",-The", "")
                    if ",-A" in new_file:
                        new_file = "A-" + new_file.replace(",-A", "")

                    copy(os.path.join(r, file), write_path+"\\"+new_file+".txt")
                else:
                    print(os.path.join(r, file))
        
            opened_file.closed

        except Exception as e:
            print(e)
