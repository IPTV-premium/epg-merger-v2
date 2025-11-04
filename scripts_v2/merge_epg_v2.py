import os, sys, gzip, requests, xml.etree.ElementTree as ET
from pathlib import Path

HEADERS={"User-Agent":"EPG-Merger/2.0 (+github.com/IPTV-premium/epg-merger-v2)"}
TIMEOUT=120
URLS=[u for u in (os.getenv("EPG_URL1"), os.getenv("EPG_URL2")) if u]

def fetch(url:str)->bytes:
    r=requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    b=r.content
    if b[:2]==b"\x1f\x8b" or "gzip" in (r.headers.get("Content-Type","").lower()):
        b=gzip.decompress(b)
    return b

def merge(urls):
    tv=ET.Element("tv"); tv.set("generator-info-name","epg-merger-v2")
    channels={}; programmes=[]
    for i,u in enumerate(urls,1):
        try:
            root=ET.fromstring(fetch(u))
            for c in root.findall("channel"):
                cid=c.get("id")
                if cid and cid not in channels: channels[cid]=c
            programmes.extend(root.findall("programme"))
            print(f"OK source {i}: channels={len(channels)} programmes={len(programmes)}")
        except Exception as e:
            print(f"WARN source {i}: {e}", file=sys.stderr)
    for c in channels.values(): tv.append(c)
    for p in programmes: tv.append(p)
    return ET.ElementTree(tv)

def main()->int:
    if not URLS: print("Missing EPG_URL1/EPG_URL2", file=sys.stderr); return 1
    out=Path(os.getenv("OUTPUT_DIR","build")); out.mkdir(parents=True, exist_ok=True)
    tree=merge(URLS)
    xml_path=out/"merged_epg.xml"
    with xml_path.open("wb") as f:
        f.write(b'<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)
    if xml_path.stat().st_size<1000: print("Result too small; aborting", file=sys.stderr); return 2
    with xml_path.open("rb") as fin, gzip.open(out/"merged_epg.xml.gz","wb", compresslevel=6) as fout:
        fout.write(fin.read())
    print(f"Wrote {xml_path} and {out/'merged_epg.xml.gz'}"); return 0

if __name__=="__main__": raise SystemExit(main())
