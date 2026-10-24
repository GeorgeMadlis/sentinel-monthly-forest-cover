import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import yaml

from forest_change.bundle import audit_links, build_bundle, digest, local_file, verify_bundle


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.review = self.root / 'review'
        self.review.mkdir()
        assignment = self.review / 'plan.md'
        assignment.write_text('Synthetic bounded plan.\n')
        self.record = {
            'status': 'planned', 'repos': {'forest_cover_lab': 'a' * 40,
                'sentinel_monthly_forest_cover': 'b' * 40, 'lab_graph_revision': 'c' * 64},
            'instances': [{'id': 'audit-01', 'host_planned': 'codex', 'delegation': {'mode': 'sequential_role'},
                           'assignment': 'plan.md', 'actual_executions': []}],
            'graph': {'nodes': [{'id': 'audit-01', 'instance': 'audit-01',
                                'step_plan': {'plan_sha256': digest(assignment)}}]}}
        (self.review / 'round.yaml').write_text(yaml.safe_dump(self.record))
        geo = {'type': 'FeatureCollection', 'features': []}
        self.spec = {'status': 'private_planned_draft', 'report_markdown': 'Synthetic planned report',
                     'map_layers': [], 'unavailable_layers': ['all scientific layers'],
                     'metadata': {'forest_mask_status': 'not_available'}, 'files': []}
        for name, content, dest in [
                ('rois.geojson', json.dumps(geo), 'metadata/rois.geojson'),
                ('aoi.geojson', json.dumps(geo), 'metadata/aoi.geojson'),
                ('graph.svg', '<svg xmlns="http://www.w3.org/2000/svg"/>', 'metadata/graph.svg'),
                ('graph.mmd', 'flowchart TD', 'metadata/graph.mmd'),
                ('leaflet.js', '/* synthetic test stub */', 'maps/leaflet.js'),
                ('leaflet.css', '', 'maps/leaflet.css')]:
            p = self.review / name
            p.write_text(content)
            self.spec['files'].append({'path': name, 'destination': dest, 'sha256': digest(p)})
        self.save_spec()
        self.out = self.root / 'draft'

    def save_spec(self):
        (self.review / 'bundle_spec.json').write_text(json.dumps(self.spec))

    def test_zip_extract_roundtrip_inventory_and_not_run(self):
        result = build_bundle(self.review, self.out)
        extracted = self.root / 'extracted'
        with zipfile.ZipFile(result['zip']) as z:
            z.extractall(extracted)
        self.assertEqual(verify_bundle(extracted)['files_verified'], result['files_verified'])
        self.assertGreater(result['local_links_checked'], 10)
        self.assertFalse(result['scientific_verification'])
        execution = json.loads((extracted / 'agents/audit-01/execution.json').read_text())
        self.assertEqual(execution, {'status': 'not_run', 'actual_executions': []})
        expected = self.record['graph']['nodes'][0]['step_plan']['plan_sha256']
        self.assertEqual(digest(extracted / 'agents/audit-01/plan.md'), expected)
        self.assertEqual(digest(extracted / 'metadata/plan.md'), expected)
        self.assertNotIn('fetch(', (extracted / 'maps/index.html').read_text())

    def test_refuse_overwrite(self):
        build_bundle(self.review, self.out)
        before = digest(self.out / 'bundle_manifest.json')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            build_bundle(self.review, self.out)
        self.assertEqual(before, digest(self.out / 'bundle_manifest.json'))

    def test_tamper_and_unlisted_file(self):
        build_bundle(self.review, self.out)
        p = self.out / 'report.md'
        original = p.read_bytes()
        p.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            verify_bundle(self.out)
        p.write_bytes(original)
        (self.out / 'unlisted.txt').write_text('extra')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            verify_bundle(self.out)

    def test_input_escape_symlink_and_bad_hash(self):
        outside = self.root / 'outside.txt'
        outside.write_text('external')
        with self.assertRaises(ValueError):
            local_file(self.review, '../outside.txt')
        (self.review / 'link').symlink_to(outside)
        with self.assertRaises(ValueError):
            local_file(self.review, 'link')
        self.spec['files'][0]['sha256'] = '0' * 64
        self.save_spec()
        with self.assertRaisesRegex(ValueError, 'input checksum'):
            build_bundle(self.review, self.out)
        self.assertFalse(self.out.exists())

    def test_assignment_hash_and_executions_cannot_be_misrepresented(self):
        bad = copy.deepcopy(self.record)
        bad['instances'][0]['actual_executions'] = [{'status': 'completed'}]
        (self.review / 'round.yaml').write_text(yaml.safe_dump(bad))
        with self.assertRaisesRegex(ValueError, 'without executions'):
            build_bundle(self.review, self.out)
        (self.review / 'round.yaml').write_text(yaml.safe_dump(self.record))
        (self.review / 'plan.md').write_text('changed after planning')
        with self.assertRaisesRegex(ValueError, 'Step-plan checksum'):
            build_bundle(self.review, self.out)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.out.with_suffix('.zip').exists())

    def test_broken_and_remote_dependencies(self):
        p = self.root / 'index.html'
        for text in ['<img src="missing.png">', '<script src="https://example.org/script.js"></script>',
                     '<a href="file:///tmp/outside">link</a>']:
            p.write_text(text)
            with self.assertRaises(ValueError):
                audit_links(self.root)


if __name__ == '__main__':
    unittest.main()
