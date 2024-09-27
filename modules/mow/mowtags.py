class MowTags:
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"

    gps_latitude = "GPSLatitude"
    gps_latitudeRef = "GPSLatitudeRef"
    gps_longitude = "GPSLongitude"
    gps_longitudeRef = "GPSLongitudeRef"
    gps_altitude = "GPSAltitude"

    expected = [date, source, description, rating]
    optional = [
        subject,
        hierarchicalsubject,
        label,
        gps_longitude,
        gps_longitudeRef,
        gps_latitude,
        gps_latitudeRef,
        gps_altitude,
    ]

    all = expected + optional
