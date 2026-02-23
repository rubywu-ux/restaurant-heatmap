import plistlib
from html.parser import HTMLParser

with open('Past Orders | Uber Eats.webarchive', 'rb') as f:
    plist = plistlib.load(f)

main = plist.get('WebMainResource', {})
data = main.get('WebResourceData', b'')
html_text = data.decode('utf-8', errors='replace')

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False
    def handle_data(self, data):
        if not self.skip:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

extractor = TextExtractor()
extractor.feed(html_text)
text = '\n'.join(extractor.text_parts)

with open('uber_eats_text.txt', 'w') as f:
    f.write(text)

print(text[:80000])
