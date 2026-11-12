#!/usr/bin/env python3
"""Check generated pages, local targets, CFP fidelity and unopened payment flows."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'docs'
errors = []


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.links = []
        self.h1s = 0
        self.images = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if 'id' in attr:
            if attr['id'] in self.ids:
                errors.append(f'{self.path}: duplicate id {attr["id"]}')
            self.ids.add(attr['id'])
        if tag == 'h1':
            self.h1s += 1
        if tag == 'img':
            self.images.append(attr)
            if 'alt' not in attr:
                errors.append(f'{self.path}: image without alt text')
        for key in ('href','src'):
            if key in attr:
                self.links.append(attr[key])


def main():
    pages = {p.resolve(): Page(p) for p in PUBLIC.rglob('*.html')}
    if len(pages) != 8:
        errors.append(f'Expected 7 conference pages and 404; found {len(pages)}')
    count = 0
    for path, page in pages.items():
        if page.h1s != 1:
            errors.append(f'{path}: expected 1 h1, found {page.h1s}')
        text = path.read_text(encoding='utf-8')
        for unwanted in ('WCCA','ICCV','Openreview','***@gmail.com','[DD Month YYYY]','javascript:'):
            if unwanted in text:
                errors.append(f'{path}: inherited sample or invalid content {unwanted}')
        for removed in ('accommodation', 'visa'):
            if removed in text.lower():
                errors.append(f'{path}: removed travel service still appears: {removed}')
        if 'wydsc2027@sogang.ac.kr' not in text:
            errors.append(f'{path}: official contact missing')
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            if href == '#':
                errors.append(f'{path}: empty action link')
                continue
            target = (PUBLIC / unquote(url.path).lstrip('/')) if url.path.startswith('/') else (path.parent / unquote(url.path))
            if not url.path:
                target = path
            if target.is_dir():
                target = target / 'index.html'
            target = target.resolve()
            count += 1
            if not target.is_relative_to(PUBLIC.resolve()):
                errors.append(f'{path}: link escapes publishing directory: {href}')
            elif not target.is_file():
                errors.append(f'{path}: broken local target {href}')
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f'{path}: missing fragment {href}')
    config = json.loads((ROOT / 'data/conference.json').read_text(encoding='utf-8'))
    cfp = (PUBLIC / 'call-for-papers/index.html').read_text(encoding='utf-8')
    from html import unescape
    readable_cfp = unescape(cfp)
    for expected in (
        config['papal_quote'],
        config['papal_quote_source'],
        config['papal_quote_url'],
        f'between {config["submission_open_date"]}, and {config["submission_deadline"]}',
    ):
        if expected not in readable_cfp:
            errors.append(f'CFP source or submission-period content omitted: {expected}')
    for track in config['tracks']:
        for topic in track['topics']:
            if topic not in readable_cfp:
                errors.append(f'CFP topic omitted: {topic}')
    registration = (PUBLIC / 'registration/index.html').read_text(encoding='utf-8')
    if not config['registration_url']:
        if 'Registration is not yet open.' not in registration:
            errors.append('Registration must clearly report that it is not open')
        for fake in ('<form','Pay with PayPal','Registration successful','Payment successful'):
            if fake in registration:
                errors.append(f'Unconfigured registration exposes fake action: {fake}')
    if not (PUBLIC / '.nojekyll').is_file():
        errors.append('Missing .nojekyll')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(pages)} pages, {count} local links/assets, all {sum(len(t["topics"]) for t in config["tracks"])} CFP topics, official email, registration status and payment gating.')


if __name__ == '__main__':
    main()
