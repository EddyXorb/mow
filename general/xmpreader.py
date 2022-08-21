import xml.etree.ElementTree as ET


class XMPReader:
    """
    Reads XMP-data from files. XMP is an xml-format to store informations about the file like rating, author, location etc. similar to exif.
    In contrast to exif it is less difficult to work with as it is stored as plain text and it is not restricted to predefined fields.
    """

    MAX_LINE_NR_FOR_SEARCH = 1000
    START_XMP_IDENTIFIER = "<x:xmpmeta"
    END_XMP_IDENTIFIER = "</x:xmpmeta>"
    NAMESPACES = {
        "xmp": "http://ns.adobe.com/xap/1.0/",
        "MicrosoftPhoto": "http://ns.microsoft.com/photo/1.0/",
    }

    def __init__(self, filepath: str):
        self.file = filepath
        self.rawxml = "init_me"
        self.xmlroot = "init_me"

    def _extractXMP(self, file: str) -> str:
        xml = []
        found = False
        with open(file, "rb") as f:
            for nr, line in enumerate(f.readlines()):
                if (self.START_XMP_IDENTIFIER in str(line)) and not found:
                    found = True
                if found:
                    xml.append(line.decode("utf-8"))
                    if self.END_XMP_IDENTIFIER in str(line):
                        break
                if nr > self.MAX_LINE_NR_FOR_SEARCH:
                    return None

        return "".join(xml)

    def _updateInternalXml(self):
        if self.rawxml == "init_me":
            self.rawxml = self._extractXMP(self.file)
            if self.rawxml is None:
                return False

            self.xmlroot: ET.ElementTree = ET.ElementTree(
                ET.fromstring(self.rawxml)
            ).getroot()

        return True

    def getRawXml(self) -> str:
        self._updateInternalXml()
        return self.rawxml

    def getAll(self) -> str:
        if not self._updateInternalXml():
            print(f"Could not read {self.file}.")
            return ""

        out = []
        for child in self.xmlroot[0][0]:

            entry = f"{child.tag} is {child.text}"
            for prefix, uri in self.NAMESPACES.items():
                entry = entry.replace("{" + uri + "}", prefix + ":")
            out.append(entry)

        return out

    def _verifyInput(self, namespace) -> str:
        if not self._updateInternalXml():
            print(f"Did not find XMP-metadata for file {self.file}!")
            return False

        if namespace not in self.NAMESPACES:
            raise Exception(
                "Namespace", namespace, "is not contained in XMP-Reader. Update it."
            )

        return True

    def get(self, namespace: str, tag: str, fallback: str) -> str:
        if not self._verifyInput(namespace):
            print(f"Return fallback {fallback} for tag request {tag}.")
            return fallback

        searchresult = self.xmlroot[0][0].find(f"{namespace}:{tag}", self.NAMESPACES)
        if searchresult is None:
            print(
                f"Could not find {namespace}:{tag} in {self.file}'s XMP. Return fallback {fallback}."
            )
            return fallback

        return searchresult.text
