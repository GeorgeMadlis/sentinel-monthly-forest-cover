import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_review_site import main  # noqa: E402


class ReviewSiteTests(unittest.TestCase):
    def build(self, files, *args):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        review = Path(tmp.name) / 'review'
        for rel, text in files.items():
            (review / rel).parent.mkdir(parents=True, exist_ok=True)
            (review / rel).write_text(text)
        return review, main([str(review), *args])

    def test_links_are_relative_and_rewritten_to_viewers(self):
        review, code = self.build({
            'investigation.json': json.dumps({'investigation_id': 'demo', 'stages': {'inspect': {'status': 'complete'}},
                                              'artifacts': {'inspect/visual_findings.md': 'abc'}}),
            'inspect/visual_findings.md': '# Findings\n\nSee [metrics](roi_metrics.csv) and ![sheet](contact.png).\n',
            'inspect/roi_metrics.csv': 'roi,file\nROI-01,contact.png\n',
            'inspect/contact.png': 'png',
            'inspect/maps/comparison.html': '<a href="map.html">map</a>',
            'inspect/maps/map.html': '<script src="leaflet.js"></script>',
            'inspect/maps/leaflet.js': '',
        }, '--strict')
        self.assertEqual(code, 0)
        landing = (review / 'index.html').read_text()
        self.assertIn('demo', landing)
        self.assertIn('href="_html/investigation.json.html"', landing)
        self.assertIn('href="inspect/maps/comparison.html"', landing)
        md = (review / '_html/inspect/visual_findings.md.html').read_text()
        self.assertIn('href="roi_metrics.csv.html"', md)
        self.assertIn('src="../../inspect/contact.png"', md)
        # Quoted paths inside JSON become links to the viewer page.
        self.assertIn('href="inspect/visual_findings.md.html"', (review / '_html/investigation.json.html').read_text())
        files = json.loads((review / '_html/files.json').read_text())['files']
        self.assertEqual({f['path'] for f in files} & {'index.html'}, set())
        self.assertNotIn(str(review), landing)

    def test_strict_mode_reports_missing_and_absolute_links(self):
        review, code = self.build({
            'report/report.md': '[gone](missing.json)\n',
            'report/report.html': '<img src="/etc/passwd.png"><a href="nope.html">x</a>',
        }, '--strict')
        self.assertEqual(code, 1)
        check = json.loads((review / '_html/link_check.json').read_text())
        self.assertEqual([p['problem'] for p in check['html_link_problems']], ['absolute path', 'missing'])
        self.assertEqual(check['document_link_problems'][0]['target'], 'missing.json')

    def test_rebuild_does_not_modify_artifacts(self):
        review, _ = self.build({'report/report.md': '# R\n'})
        before = (review / 'report/report.md').read_text()
        self.assertEqual(main([str(review)]), 0)
        self.assertEqual((review / 'report/report.md').read_text(), before)
        self.assertFalse((review / '_html/_html').exists())


if __name__ == '__main__':
    unittest.main()
