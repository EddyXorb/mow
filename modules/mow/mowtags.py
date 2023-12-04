class MowTags:
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"

    expected = [date, source, description, rating]
    optional = [subject, hierarchicalsubject, label]

    all = expected + optional
