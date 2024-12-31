# Todos

- [ ] Write tests for sequence checker of grouper
- [ ] Conversion: assure xmp-tags are maintained after conversion (especially for videos: xmp:date is vanished) by reading them before conversion and writing them to result
- [ ] new flag --filedialog to enable selection of folders/files on which to apply the current stage command
- [ ] bug: mp4-files don't get xmp:Date written and are missing longitude and latitude gps values
- [ ] bug: unknown bug (maybe due to a nextcloud bug or virtual files) causes deleted files to be present in completely unrelated directories. Example: ![alt text](2024-09-30_Bug.png) It is interesting, that the first folder contains a 'ß' whereas the correct folder uses 'ss'. This was changed by me due to issues in xmp-metadata.
- [ ] bug: stage history writes tag **sourcefile** sometimes
- [ ] feature: check if all stages were passed during **aggregation** using history of xmp:contributor
- [ ] feature: make it possible to disable interpolation in localize
- [x] define an entrypoint for mow in order to make it possible to install mow globally and create distributions
