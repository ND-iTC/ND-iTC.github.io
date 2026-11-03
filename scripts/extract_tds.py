import re, json
src = open('TD/tech_dec.adoc', encoding='utf-8').read()
tbl = src.split('[#td-table', 1)[1].split('|===')[1]
cells = re.split(r'\n\|', '\n'+tbl.strip())
cells = [c.strip() for c in cells if c.strip() != '']
cells = cells[6:]  # header
tds = []
for i in range(0, len(cells), 6):
    idc, title, ref, date, impact, status = cells[i:i+6]
    m = re.match(r'(https?://\S+?)\[(.*),window="_blank"\]$', title, re.S)
    url, t = m.group(1), m.group(2)
    path = re.sub(r'/+', '/', url.split('nd-itc.github.io/',1)[1])
    tds.append(dict(id=idc.replace('RFI#','RFI#'), title=t.strip(), reference=' '.join(ref.replace('\n',' ').split()),
                    date=date, applies=[x.strip() for x in impact.replace('\n',' ').split(',') if x.strip()],
                    status=status, file=path))
json.dump(tds, open('data/tds.json','w'), indent=1, ensure_ascii=False)
print(len(tds)); import os
for t in tds:
    if not os.path.exists(t['file']): print('MISSING', t['file'])
print(sorted({a for t in tds for a in t['applies']}))
