import exiftool

from exiftool import ExifToolHelper



with ExifToolHelper() as et:
    for d in et.get_metadata("tests/test.MOV"):
        for k, v in d.items():
            print(f"Dict: {k} = {v}")

    # print(et.set_tags(
    #     ["tests/test3_copy.JPG"],
    #     tags={"XMP:Source": "quatsch.JPG"},
    #     params=["-P", "-overwrite_original","-v2"],
    # ))
    
    # print(et.get_tags("tests/test3_copy.JPG",
    #     tags="XMP-dc:Source"))
    
    #print(et.get_metadata("tests/test3_copy.JPG"))
