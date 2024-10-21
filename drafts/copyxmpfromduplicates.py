#Little helper script to copy xmp tags from already tagged files into files already present in database but untagged.
from dataclasses import dataclass
import os
from typing import DefaultDict, Dict, List
from exiftool import ExifToolHelper
from os.path import join
taggedfilesfolder = (

)
searchfolders = [

]

xmptags = ["XMP:Rating","XMP:HierarchicalSubject","XMP:Subject"]

@dataclass
class File:
    origName: str
    path: str
    tags: str

cnt = 0
taggedfiles: list[File] = []
with ExifToolHelper() as et:
    for root, dirs, files in os.walk(taggedfilesfolder):
        for f in files:
            file, ext = os.path.splitext(f)
            tags = {}
            try:
                tags = et.get_tags(join(root,f),xmptags,params=["-vvv"])[0]
            except Exception as e:
                print(f"tried {join(root,f)} but {e}")
            if len(tags) != len(xmptags) + 1:
                continue
            print(tags)
            tags.pop("SourceFile")
            if "@" in file or ".T." in file:
                originalName = "_".join(file.split("_")[1:])
                taggedfiles.append(File(path=join(root, f), origName=originalName,tags=tags))
            else:
                print(f"No _ in {file}")
                taggedfiles.append(File(path=join(root, f), origName=file,tags=tags))
            print(taggedfiles[-1])
            cnt += 1

            
            

searchfiles = DefaultDict(lambda : [])
for folder in searchfolders:
    for root, dirs, files in os.walk(folder):
        for f in files:
            file, ext = os.path.splitext(f)
            if "@" in file or ".T." in file:
                searchfiles["_".join(file.split("_")[1:])].append(join(root,f))
            else:
                searchfiles[file].append(join(root, f))
        print(f"Found {len(searchfiles)}")


connection :DefaultDict(List) = DefaultDict(lambda : [])
for file in taggedfiles:
    if file.origName in searchfiles:
        connection[file.path] = (file,connection[file.path] + searchfiles[file.origName])
        print(f"Found {file} -> {searchfiles[file.origName]}")

unfound = 0
for f in taggedfiles:
    if not f.path in connection:
        unfound += 1
        print(f"Did not find {f.origName} -> {f.path}!")


print(f"Did not find {unfound} files!\n\n\n")
with ExifToolHelper() as et:
    for k,v in connection.items():
        basefile:File = v[0]
        for fileToModify in v[1]:
            if basefile.origName not in fileToModify:
                print(f"Attention! {fileToModify} != {basefile.origName}")
                continue
            print(f"Will modify {fileToModify} based ond {basefile}")
            try:
                et.set_tags(fileToModify,tags=basefile.tags,params=["-P", "-overwrite_original", "-v2"])
            except Exception as e:
                print(f"Could not set {fileToModify} due to {e}")

print(len(connection))