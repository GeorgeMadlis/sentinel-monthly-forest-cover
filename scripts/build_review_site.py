"""Make a review folder browsable offline through linked HTML pages.

Writes REVIEW/index.html (landing page) and REVIEW/_html/ (directory listings,
viewers for Markdown/JSON/CSV/text files, a SHA-256 file inventory and a link
check). Every link is relative, so the folder can be zipped, downloaded and
opened with any browser from the local filesystem. Existing review artifacts
are never modified; rerunning the script replaces only index.html and _html/.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

SITE = '_html'
TEXT_VIEW = {'.md', '.json', '.geojson', '.csv', '.tsv', '.txt', '.log', '.py', '.sh',
             '.bib', '.yaml', '.yml', '.xml', '.tex', '.toml', '.cfg', '.ini'}
IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
MAX_VIEW_BYTES = 5_000_000
# Leaflet marker/control sprites and raw downloads are not review figures.
GALLERY_SKIP = {'images', 'cache', SITE}
STAGES = ('inspect', 'research', 'corroborate', 'report')
STYLE = """
:root{--bg:#fff;--fg:#1d2228;--muted:#5d6670;--line:#d9dee3;--link:#0b5cad;--code:#f4f6f8;--bad:#b42318}
@media (prefers-color-scheme:dark){:root{--bg:#15181c;--fg:#e4e7ea;--muted:#9aa3ad;--line:#333a42;--link:#79b8ff;--code:#1f242a;--bad:#ff8a80}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}
a{color:var(--link)}nav{font-size:13px;color:var(--muted);margin-bottom:12px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 16px}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
pre,code{background:var(--code);font:12px/1.45 ui-monospace,Menlo,monospace}
pre{padding:12px;overflow:auto;white-space:pre-wrap;word-break:break-word}
.muted{color:var(--muted)}.broken{color:var(--bad);text-decoration:line-through}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.grid figure{margin:0;border:1px solid var(--line);padding:6px}.grid img{width:100%;height:160px;object-fit:contain}
.grid figcaption{font-size:12px;word-break:break-all}
.md img{max-width:100%}.wrap{overflow-x:auto}
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024


def href(from_page, target):
    """Relative URL from one REVIEW-relative page path to another REVIEW-relative path."""
    rel = os.path.relpath(target, os.path.dirname(from_page) or '.')
    return quote(rel.replace(os.sep, '/'))


def page(title, body, page_path):
    root = href(page_path, 'index.html')
    tree = href(page_path, f'{SITE}/index.html')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main>'
            f'<nav><a href="{root}">Review home</a> · <a href="{tree}">All files</a></nav>'
            f'{body}</main></body></html>')


class Site:
    def __init__(self, review):
        self.review = Path(review).resolve()
        self.files = []
        self.dirs = set()
        self.broken = []
        self.outside_links = []

    # ---------- inventory ----------
    def scan(self):
        for root, dirs, names in os.walk(self.review):
            rel_root = Path(root).relative_to(self.review).as_posix()
            rel_root = '' if rel_root == '.' else rel_root
            dirs[:] = sorted(d for d in dirs if not (rel_root == '' and d == SITE))
            self.dirs.add(rel_root)
            for name in sorted(names):
                rel = f'{rel_root}/{name}' if rel_root else name
                if rel == 'index.html':
                    continue
                path = Path(root) / name
                if path.is_symlink():
                    target = path.resolve()
                    if self.review not in target.parents:
                        self.outside_links.append({'path': rel, 'target': str(target)})
                        continue
                self.files.append(rel)
        self.file_set = set(self.files)

    def viewable(self, rel):
        return Path(rel).suffix.lower() in TEXT_VIEW and (self.review / rel).stat().st_size <= MAX_VIEW_BYTES

    def view_path(self, rel):
        """Where a file is best opened: its viewer page, or the file itself."""
        return f'{SITE}/{rel}.html' if self.viewable(rel) else rel

    def resolve(self, base_dir, target):
        """Resolve a link/path string to a REVIEW-relative existing path, or None."""
        if not target or len(target) > 400 or '\n' in target:
            return None
        candidates = []
        p = Path(unquote(target))
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates += [self.review / base_dir / p, self.review / p]
        for c in candidates:
            try:
                c = c.resolve()
            except (OSError, RuntimeError):
                continue
            if c == self.review or self.review in c.parents:
                rel = c.relative_to(self.review).as_posix()
                if rel in self.file_set or rel in self.dirs:
                    return rel
        return None

    def link(self, page_path, base_dir, target, label):
        """Rewrite a document link so it works inside the downloaded folder."""
        parts = urlsplit(target)
        if parts.scheme or target.startswith(('#', '//', 'mailto:')):
            return f'<a href="{html.escape(target)}">{label}</a>'
        rel = self.resolve(base_dir, parts.path)
        if rel is None:
            self.broken.append({'page': page_path, 'target': target})
            return f'<span class="broken" title="missing: {html.escape(target)}">{label}</span>'
        dest = f'{SITE}/{rel}/index.html' if rel in self.dirs else self.view_path(rel)
        frag = f'#{parts.fragment}' if parts.fragment else ''
        return f'<a href="{href(page_path, dest)}{frag}">{label}</a>'

    # ---------- renderers ----------
    def inline(self, text, page_path, base_dir):
        out, pos = [], 0
        pattern = re.compile(r'`([^`]+)`|!\[([^\]]*)\]\(([^)\s]+)[^)]*\)|\[([^\]]+)\]\(([^)\s]+)[^)]*\)|<(https?://[^>]+)>')
        for m in pattern.finditer(text):
            out.append(self.emphasis(html.escape(text[pos:m.start()])))
            if m.group(1) is not None:
                out.append(f'<code>{html.escape(m.group(1))}</code>')
            elif m.group(3) is not None:
                rel = self.resolve(base_dir, urlsplit(m.group(3)).path)
                if rel:
                    out.append(f'<img alt="{html.escape(m.group(2))}" src="{href(page_path, rel)}">')
                elif urlsplit(m.group(3)).scheme:
                    out.append(f'<img alt="{html.escape(m.group(2))}" src="{html.escape(m.group(3))}">')
                else:
                    self.broken.append({'page': page_path, 'target': m.group(3)})
                    out.append(f'<span class="broken">[missing image {html.escape(m.group(3))}]</span>')
            elif m.group(5) is not None:
                out.append(self.link(page_path, base_dir, m.group(5), self.emphasis(html.escape(m.group(4)))))
            else:
                out.append(f'<a href="{html.escape(m.group(6))}">{html.escape(m.group(6))}</a>')
            pos = m.end()
        out.append(self.emphasis(html.escape(text[pos:])))
        return ''.join(out)

    @staticmethod
    def emphasis(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        return re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)

    def markdown(self, text, page_path, base_dir):
        """Small dependency-free Markdown subset: headings, lists, tables, code, quotes."""
        lines, out, i = text.splitlines(), [], 0
        inl = lambda s: self.inline(s, page_path, base_dir)
        while i < len(lines):
            line = lines[i]
            if line.startswith('```'):
                j = i + 1
                while j < len(lines) and not lines[j].startswith('```'):
                    j += 1
                out.append('<pre><code>' + html.escape('\n'.join(lines[i + 1:j])) + '</code></pre>')
                i = j + 1
            elif m := re.match(r'(#{1,6})\s+(.*)', line):
                n = len(m.group(1))
                anchor = re.sub(r'[^\w-]+', '-', m.group(2).lower()).strip('-')
                out.append(f'<h{n} id="{anchor}">{inl(m.group(2))}</h{n}>')
                i += 1
            elif line.lstrip().startswith('|') and i + 1 < len(lines) and re.match(r'\s*\|?\s*:?-{3,}', lines[i + 1]):
                cells = lambda s: [c.strip() for c in s.strip().strip('|').split('|')]
                rows = [f'<tr>{"".join(f"<th>{inl(c)}</th>" for c in cells(line))}</tr>']
                i += 2
                while i < len(lines) and lines[i].lstrip().startswith('|'):
                    rows.append(f'<tr>{"".join(f"<td>{inl(c)}</td>" for c in cells(lines[i]))}</tr>')
                    i += 1
                out.append('<div class="wrap"><table>' + ''.join(rows) + '</table></div>')
            elif re.match(r'\s*([-*+]|\d+[.)])\s+', line):
                ordered = bool(re.match(r'\s*\d', line))
                items = []
                while i < len(lines) and (m := re.match(r'\s*(?:[-*+]|\d+[.)])\s+(.*)', lines[i])):
                    items.append(f'<li>{inl(m.group(1))}</li>')
                    i += 1
                tag = 'ol' if ordered else 'ul'
                out.append(f'<{tag}>{"".join(items)}</{tag}>')
            elif line.startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].startswith('>'):
                    quote_lines.append(lines[i][1:].strip())
                    i += 1
                out.append(f'<blockquote>{inl(" ".join(quote_lines))}</blockquote>')
            elif re.match(r'\s*(-{3,}|\*{3,})\s*$', line):
                out.append('<hr>')
                i += 1
            elif not line.strip():
                i += 1
            else:
                para = []
                while i < len(lines) and lines[i].strip() and not re.match(r'(#{1,6}\s|```|>|\s*\||\s*([-*+]|\d+[.)])\s)', lines[i]):
                    para.append(lines[i].strip())
                    i += 1
                if not para:
                    para.append(line.strip())
                    i += 1
                out.append(f'<p>{inl(" ".join(para))}</p>')
        return '<div class="md">' + '\n'.join(out) + '</div>'

    def linkify_paths(self, text, page_path, base_dir):
        """Escape text and turn quoted strings that name review files into links."""
        out, pos = [], 0
        for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"', text):
            out.append(html.escape(text[pos:m.start()]))
            value = m.group(1)
            rel = self.resolve(base_dir, value) if ('/' in value or '.' in value) else None
            token = html.escape(m.group(0))
            if rel:
                dest = f'{SITE}/{rel}/index.html' if rel in self.dirs else self.view_path(rel)
                token = f'<a href="{href(page_path, dest)}">{token}</a>'
            out.append(token)
            pos = m.end()
        out.append(html.escape(text[pos:]))
        return ''.join(out)

    def table(self, text, delimiter, page_path, base_dir):
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        if not rows:
            return '<p class="muted">Empty table.</p>'
        cell = lambda c: (self.link(page_path, base_dir, c, html.escape(c))
                          if self.resolve(base_dir, c) else html.escape(c))
        head = ''.join(f'<th>{html.escape(c)}</th>' for c in rows[0])
        body = ''.join('<tr>' + ''.join(f'<td>{cell(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
        return f'<div class="wrap"><table><tr>{head}</tr>{body}</table></div>'

    def render_file(self, rel, page_path=None):
        page_path = page_path or f'{SITE}/{rel}.html'
        base_dir = os.path.dirname(rel)
        suffix = Path(rel).suffix.lower()
        text = (self.review / rel).read_text(encoding='utf-8', errors='replace')
        if suffix == '.md':
            body = self.markdown(text, page_path, base_dir)
        elif suffix in ('.csv', '.tsv'):
            body = self.table(text, '\t' if suffix == '.tsv' else ',', page_path, base_dir)
        elif suffix in ('.json', '.geojson'):
            try:
                text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
            except ValueError:
                pass
            body = f'<pre>{self.linkify_paths(text, page_path, base_dir)}</pre>'
        else:
            body = f'<pre>{self.linkify_paths(text, page_path, base_dir)}</pre>'
        raw = href(page_path, rel)
        folder = href(page_path, f'{SITE}/{base_dir}/index.html' if base_dir not in ('', SITE) else f'{SITE}/index.html')
        header = (f'<h1>{html.escape(Path(rel).name)}</h1><p class="muted">{html.escape(rel)} · '
                  f'<a href="{raw}">raw file</a> · <a href="{folder}">folder</a></p>')
        self.write(page_path, page(rel, header + body, page_path))

    def file_row(self, page_path, rel, hashes):
        size = (self.review / rel).stat().st_size
        open_link = href(page_path, self.view_path(rel))
        raw = href(page_path, rel)
        extra = f' · <a href="{raw}">raw</a>' if self.view_path(rel) != rel else ''
        return (f'<tr><td><a href="{open_link}">{html.escape(Path(rel).name)}</a>{extra}</td>'
                f'<td>{human(size)}</td><td><code title="{hashes[rel]}">{hashes[rel][:12]}</code></td></tr>')

    def gallery(self, page_path, images):
        figures = ''.join(f'<figure><a href="{href(page_path, r)}"><img loading="lazy" src="{href(page_path, r)}" alt=""></a>'
                          f'<figcaption>{html.escape(r)}</figcaption></figure>' for r in images)
        return f'<div class="grid">{figures}</div>' if images else ''

    def render_dir(self, rel_dir, hashes):
        page_path = f'{SITE}/{rel_dir}/index.html' if rel_dir else f'{SITE}/index.html'
        prefix = f'{rel_dir}/' if rel_dir else ''
        subdirs = sorted(d for d in self.dirs if d and os.path.dirname(d) == rel_dir)
        files = [f for f in self.files if os.path.dirname(f) == rel_dir and not f.startswith(f'{SITE}/')]
        crumbs, acc = [f'<a href="{href(page_path, f"{SITE}/index.html")}">review</a>'], ''
        for part in rel_dir.split('/') if rel_dir else []:
            acc = f'{acc}/{part}' if acc else part
            crumbs.append(f'<a href="{href(page_path, f"{SITE}/{acc}/index.html")}">{html.escape(part)}</a>')
        body = [f'<h1>{" / ".join(crumbs)}</h1>']
        if subdirs:
            count = lambda d: sum(1 for f in self.files if f.startswith(f'{d}/'))
            body.append('<h2>Folders</h2><ul>' + ''.join(
                f'<li><a href="{href(page_path, f"{SITE}/{d}/index.html")}">{html.escape(d[len(prefix):])}/</a>'
                f' <span class="muted">({count(d)} files)</span></li>' for d in subdirs) + '</ul>')
        if files:
            body.append('<h2>Files</h2><div class="wrap"><table><tr><th>File</th><th>Size</th><th>SHA-256</th></tr>'
                        + ''.join(self.file_row(page_path, f, hashes) for f in files) + '</table></div>')
            body.append(self.gallery(page_path, [f for f in files if Path(f).suffix.lower() in IMAGES]))
        self.write(page_path, page(rel_dir or 'Review files', ''.join(body), page_path))

    def landing(self, hashes, generated):
        page_path = 'index.html'
        inv = self.load_json('investigation.json')
        title = inv.get('investigation_id') or self.review.name
        body = [f'<h1>{html.escape(str(title))}</h1>',
                '<p class="muted">Offline review bundle. Download or unzip the whole folder and open this '
                'index.html; every link is relative to it. Viewer pages for Markdown, JSON, CSV and logs '
                f'are under {SITE}/. Generated {html.escape(generated)}.</p>']
        stages = inv.get('stages') or {}
        if stages:
            rows = ''.join(f'<tr><td>{html.escape(k)}</td><td>{html.escape(str(v.get("status", "")))}</td>'
                           f'<td>{html.escape(str(v.get("reason") or v.get("scope") or ""))}</td></tr>'
                           for k, v in stages.items() if isinstance(v, dict))
            body.append(f'<h2>Stage status</h2><table><tr><th>Stage</th><th>Status</th><th>Note</th></tr>{rows}</table>')
        key = [f for f in ('report/report.html', 'report.html', 'report/report.md', 'report.md',
                           'findings.json', 'investigation.json', 'semantic_trace.json', 'rois.geojson')
               if f in self.file_set]
        docs = sorted(f for f in self.files if Path(f).suffix.lower() == '.md'
                      and not f.startswith(('cache/', 'semantic_context/')) and f not in key)
        maps = sorted(f for f in self.files if Path(f).suffix.lower() == '.html'
                      and not f.startswith('cache/') and f not in key)
        def items(paths):
            return '<ul>' + ''.join(f'<li><a href="{href(page_path, self.view_path(p))}">{html.escape(p)}</a></li>'
                                    for p in paths) + '</ul>'
        if key:
            body.append('<h2>Start here</h2>' + items(key))
        for stage in STAGES:
            stage_files = [f for f in docs if f.startswith(f'{stage}/')]
            if stage_files:
                body.append(f'<h2>{stage.title()} stage</h2>' + items(stage_files))
        other = [f for f in docs if not f.startswith(tuple(f'{s}/' for s in STAGES))]
        if other:
            body.append('<h2>Documents</h2>' + items(other))
        if maps:
            # Comparison pages first; long families (e.g. one map per experiment setting) collapse.
            groups = {}
            for f in sorted(maps, key=lambda f: (Path(f).name != 'comparison.html', f)):
                groups.setdefault(f.split('/')[0] if '/' in f else '', []).append(f)
            parts = []
            for name, paths in groups.items():
                if len(paths) > 8:
                    parts.append(f'<details><summary>{html.escape(name)}/ ({len(paths)} pages)</summary>{items(paths)}</details>')
                else:
                    parts.append(items(paths))
            body.append('<h2>Interactive maps and HTML pages</h2>' + ''.join(parts))
        figures = sorted(f for f in self.files if Path(f).suffix.lower() in IMAGES
                         and not GALLERY_SKIP & set(Path(f).parts) and not f.startswith('experiments/'))
        if figures:
            body.append('<h2>Figures</h2>' + self.gallery(page_path, figures))
        total = sum((self.review / f).stat().st_size for f in self.files)
        body.append(f'<h2>All files</h2><p><a href="{SITE}/index.html">Browse {len(self.files)} files '
                    f'({human(total)})</a> · <a href="{SITE}/files.html">SHA-256 inventory</a> · '
                    f'<a href="{SITE}/link_check.html">link check</a></p>')
        self.write(page_path, page(str(title), ''.join(body), page_path))

    # ---------- checks ----------
    def check_html(self):
        """Verify that every relative href/src in every HTML page resolves inside REVIEW."""
        problems = []
        pages = [p for p in self.review.rglob('*.html')]
        for path in pages:
            rel_page = path.relative_to(self.review).as_posix()
            if rel_page.startswith('cache/'):
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
            for target in re.findall(r'''(?:href|src)\s*=\s*["']([^"']*)["']''', text):
                parts = urlsplit(html.unescape(target))
                if parts.scheme in ('http', 'https', 'data', 'mailto', 'javascript') or not parts.path:
                    continue
                if parts.scheme == 'file' or parts.path.startswith('/'):
                    problems.append({'page': rel_page, 'target': target, 'problem': 'absolute path'})
                    continue
                dest = (path.parent / unquote(parts.path)).resolve()
                if self.review != dest and self.review not in dest.parents:
                    problems.append({'page': rel_page, 'target': target, 'problem': 'outside review folder'})
                elif not dest.exists():
                    problems.append({'page': rel_page, 'target': target, 'problem': 'missing'})
        return len(pages), problems

    # ---------- io ----------
    def load_json(self, rel):
        try:
            return json.loads((self.review / rel).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def write(self, rel, text):
        path = self.review / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def build(self):
        shutil.rmtree(self.review / SITE, ignore_errors=True)
        self.scan()
        generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        hashes = {f: sha256(self.review / f) for f in self.files}
        for rel in self.files:
            if self.viewable(rel):
                self.render_file(rel)
        for d in sorted(self.dirs):
            self.render_dir(d, hashes)
        self.landing(hashes, generated)
        inventory = {'generated_at_utc': generated, 'review': self.review.name,
                     'files': [{'path': f, 'bytes': (self.review / f).stat().st_size, 'sha256': hashes[f]}
                               for f in self.files],
                     'excluded_symlinks_outside_review': self.outside_links}
        self.write(f'{SITE}/files.json', json.dumps(inventory, indent=2) + '\n')
        self.render_file(f'{SITE}/files.json', f'{SITE}/files.html')
        # The link-check viewer must exist before the check so the landing page's link to it resolves.
        self.write(f'{SITE}/link_check.json', '{}\n')
        self.render_file(f'{SITE}/link_check.json', f'{SITE}/link_check.html')
        checked, problems = self.check_html()
        report = {'generated_at_utc': generated, 'checked_html': checked,
                  'html_link_problems': problems, 'document_link_problems': self.broken,
                  'note': 'Links assembled at runtime by JavaScript are not checked.'}
        self.write(f'{SITE}/link_check.json', json.dumps(report, indent=2) + '\n')
        self.render_file(f'{SITE}/link_check.json', f'{SITE}/link_check.html')
        return report


def make_zip(review):
    review = Path(review).resolve()
    target = review.with_name(review.name + '.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for path in sorted(review.rglob('*')):
            if path.is_file():
                z.write(path, Path(review.name) / path.relative_to(review))
    return target


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('review', help='review folder, e.g. reviews/<UTC timestamp>-road-investigation')
    p.add_argument('--zip', action='store_true', help='also write <review>.zip next to the folder')
    p.add_argument('--strict', action='store_true', help='exit 1 when any link is missing or not portable')
    args = p.parse_args(argv)
    if not Path(args.review).is_dir():
        p.error(f'not a directory: {args.review}')
    report = Site(args.review).build()
    issues = len(report['html_link_problems']) + len(report['document_link_problems'])
    print(f"{Path(args.review) / 'index.html'}: {report['checked_html']} HTML pages checked, {issues} link problems")
    if args.zip:
        print(make_zip(args.review))
    return 1 if args.strict and issues else 0


if __name__ == '__main__':
    sys.exit(main())
