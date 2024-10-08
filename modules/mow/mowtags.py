class MowTags:
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"
    stagehistory = "XMP:Contributor"

    gps_latitude = "Composite:GPSLatitude"  # this avoids the need to use the GPSLatitudeRef tag when writing
    gps_longitude = "Composite:GPSLongitude"  # this avoids the need to use the GPSLongitudeRef tag when writing

    # unfortunately, the elevation tags cannot be set using the Composite: prefix. We thus need to distinguish between read-only and write-only tags
    gps_elevation_write_only = "GPSAltitude"
    gps_elevationRef_write_only = (
        "GPSAltitudeRef"  # 0 = Above Sea Level, 1 = Below Sea Level
    )
    gps_elevation_read_only = "Composite:GPSAltitude"

    expected = [date, source, description, rating]
    gps_all = [gps_latitude, gps_longitude, gps_elevation_read_only]
    optional = [
        subject,
        hierarchicalsubject,
        label,
        stagehistory,
        *gps_all,
    ]

    all = expected + optional
