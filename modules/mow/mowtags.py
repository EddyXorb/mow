class MowTags:
    expected = [
        "XMP:Date",
        "XMP:Source",
        "XMP:Description",
        "XMP:Rating",
    ]
    optional = ["XMP:Subject", "XMP:HierarchicalSubject", "XMP:Label"]

    all = expected + optional
