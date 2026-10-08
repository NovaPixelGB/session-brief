"""Create a free single-issue Atom feed so readers can subscribe without email."""
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

root = Path(__file__).parent
data = json.loads((root/'site/latest.json').read_text(encoding='utf-8'))
origin = 'https://novapixelgb.github.io/session-brief/'
ns = 'http://www.w3.org/2005/Atom'
def add(parent, tag, text=None, **attrs):
    element = SubElement(parent, '{'+ns+'}'+tag, attrs)
    element.text = text
    return element
feed = Element('{'+ns+'}feed')
add(feed, 'title', 'Session Brief — BTC / ETH / SOL')
add(feed, 'id', origin)
add(feed, 'updated', data['generated_at'])
add(feed, 'link', href=origin+'feed.xml', rel='self')
add(feed, 'link', href=origin)
author = add(feed, 'author'); add(author, 'name', 'Session Brief')
entry = add(feed, 'entry')
add(entry, 'title', 'Closed-hour brief: '+data['london_hour'])
add(entry, 'id', origin+'#hour-'+data['hour_end'])
add(entry, 'updated', data['generated_at'])
add(entry, 'link', href=origin)
lines = ['Prices in USDT; Binance spot only. Historical research.']
for r in data['assets']:
    ratio = f"{r['volume_ratio']:.2f}x" if r['volume_ratio'] is not None else 'unavailable'
    lines.append(f"{r['symbol']}: 1h {r['change_1h']:+.2f}%, range {r['range_1h']:.2f}%, volume / seven-day same-hour median {ratio}.")
add(entry, 'content', '\n'.join(lines), type='text')
(root/'site/feed.xml').write_bytes(tostring(feed, encoding='utf-8', xml_declaration=True))
print('Generated subscription feed')
