import re

from karp.plugins.plugin import Plugin


class NpeglSegmentationPlugin(Plugin):
    """
    The field Segementation.xml contains XML and this plugin extracts
    one attribute (name) and text in <e>-elements to populate lists which
    make it possible to search for word forms and lemma in the data.
    """

    def __init__(self):
        npegl_lemma_pattern = r"name=\"(\w+)\">"
        self.npegl_lemma_prog = re.compile(npegl_lemma_pattern, re.UNICODE)
        npegl_wordform_pattern = r"<e.*?>(.+?)</e>"
        self.npegl_wordform_prog = re.compile(npegl_wordform_pattern, re.UNICODE)

    def output_config(self):
        return {
            "type": "object",
            "fields": {
                "v_lemmata": {"type": "string", "collection": True},
                "v_wordforms": {"type": "string", "collection": True},
            },
        }

    def generate(self, segmentation):
        lemmata = []
        match = self.npegl_lemma_prog.search(segmentation)
        while match:
            lemmata.append(match.group(1))
            match = self.npegl_lemma_prog.search(segmentation, match.end(1))

        word_forms = []
        match = self.npegl_wordform_prog.search(segmentation)
        while match:
            word_forms.append(match.group(1))
            match = self.npegl_wordform_prog.search(segmentation, match.end(1))

        return {"v_lemmata": lemmata, "v_wordforms": word_forms}
