# Todos 
- Write tests for sequence checker of grouper
- Conversion: assure xmp-tags are maintained after conversion (especially for videos: xmp:date is vanished) by reading them before conversion and writing them to result
- Conversion: convert all ORF-Files into DNG-Format using [this](https://github.com/BradenM/pydngconverter) tool
- new flag --filedialog to enable selection of folders/files on which to apply the current stage command
- new flag for rate: --overrule [jpg,orf,...] to ignore already existing ratings that may differ between multiple files of same media e.g. jg and orf os same image
- fix: mp4-files don't get xmp:Date written and are missing longitude and latitude gps values