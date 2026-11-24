"""Regression tests for the published-document theme injection."""
import importlib.util
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(spec)
original_cwd = Path.cwd()
try:
    with patch.object(sys, 'argv', [str(spec.origin)]):
        spec.loader.exec_module(build)
finally:
    os.chdir(original_cwd)


THEME_PATTERN = r'<!-- nd-itc-theme -->.*?<!-- /nd-itc-theme -->'
PAGE = '<!doctype html>\n<html><head><title>Document</title></head>\n<body><h1 id="text">Document text &amp; anchors</h1></body></html>\n'


def theme_block(prefix='../'):
    return ('<!-- nd-itc-theme --><link rel="stylesheet" href="%sdoc-theme.css">'
            '<script src="%sdoc-theme.js"></script><!-- /nd-itc-theme -->') % (prefix, prefix)


class ThemeDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = Path.cwd()
        os.chdir(self.temp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.temp.cleanup()

    def check_page(self, source, path='cPP/document.html', changed=1):
        page = Path(path)
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(source, encoding='utf-8')
        with patch.object(build, 'DOC_PAGES', [path]):
            self.assertEqual(build.theme_docs(), changed)
            result = page.read_text(encoding='utf-8')
            self.assertEqual(re.findall(THEME_PATTERN, result, flags=re.S),
                             [theme_block('../' * path.count('/'))])
            self.assertEqual(re.sub(THEME_PATTERN, '', result, flags=re.S),
                             re.sub(THEME_PATTERN, '', source, flags=re.S))
            first_bytes = page.read_bytes()
            first_mtime = page.stat().st_mtime_ns
            for _ in range(3):
                self.assertEqual(build.theme_docs(), 0)
                self.assertEqual(page.read_bytes(), first_bytes)
                self.assertEqual(page.stat().st_mtime_ns, first_mtime)

    def test_adds_one_block_to_unthemed_document(self):
        self.check_page(PAGE)

    def test_existing_current_block_is_not_appended_or_rewritten(self):
        self.check_page(PAGE.replace('</head>', theme_block() + '</head>'), changed=0)

    def test_collapses_six_identical_blocks(self):
        self.check_page(PAGE.replace('</head>', theme_block() * 6 + '</head>'))

    def test_updates_stale_block(self):
        self.check_page(PAGE.replace('</head>', theme_block('old/') + '</head>'))

    def test_collapses_mixed_and_multiline_blocks(self):
        stale = '<!-- nd-itc-theme -->\n<link href="old.css">\n<!-- /nd-itc-theme -->'
        self.check_page(PAGE.replace('</head>', stale + theme_block() + stale + '</head>'))

    def test_preserves_other_head_content(self):
        source = PAGE.replace('</head>', theme_block() + '<meta name="test" content="keep">'
                              + theme_block() + '</head>')
        self.check_page(source)

    def test_uses_correct_paths_at_other_depths(self):
        for path in ('document.html', 'published/cPP/document.html'):
            with self.subTest(path=path):
                self.check_page(PAGE, path)

    def test_missing_document_is_skipped(self):
        with patch.object(build, 'DOC_PAGES', ['missing.html']):
            self.assertEqual(build.theme_docs(), 0)
        self.assertFalse(Path('missing.html').exists())

    def test_missing_head_is_left_untouched(self):
        page = Path('fragment.html')
        source = theme_block('old/') + '<p>Document fragment</p>'
        page.write_text(source, encoding='utf-8')
        with patch.object(build, 'DOC_PAGES', [str(page)]):
            self.assertEqual(build.theme_docs(), 0)
        self.assertEqual(page.read_text(encoding='utf-8'), source)


if __name__ == '__main__':
    unittest.main()
