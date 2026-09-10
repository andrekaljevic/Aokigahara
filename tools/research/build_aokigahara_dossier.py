from urllib.parse import quote
from pathlib import Path
import csv, html, re

out = Path('/mnt/data')

main_files = [
"038 Mount Fuji and Aokigahara forest (Japan) at sunrise Photo by Giles Laurent.jpg",
"Aerial panorama of Mount Fuji from Lake Saiko. June 2023.jpg",
"Aerial panorama of Mount Fuji with Saiko Iyashi-no-Sato Nenba in the foreground. June 2023.jpg",
"Aokigahara (suicide forest) + very tired Liz (42885146671).jpg",
"Aokigahara 05.jpg",
"Aokigahara 2013-11-13 (10863088565).jpg",
"Aokigahara 2013-11-13 (10863124286).jpg",
"Aokigahara 2013-11-13 (10863208834).jpg",
"Aokigahara 2013-11-13 (10863407043).jpg",
"Aokigahara 2013-11-13 (10863419343).jpg",
"Aokigahara and Misak Mountains s2.jpg",
"Aokigahara and Misaka Mountains.JPG",
"Aokigahara and Tenshi Mountains from Mount Ashiwada.jpg",
"Aokigahara Forest (10863114695).jpg",
"Aokigahara Forest (10863115895).jpg",
"Aokigahara Forest (10863122085).jpg",
"Aokigahara Forest (10863125735).jpg",
"Aokigahara Forest (10863133755).jpg",
"Aokigahara Forest (10863156655).jpg",
"Aokigahara Forest (10863169686).jpg",
"Aokigahara Forest (10863170736).jpg",
"Aokigahara Forest (10863177636).jpg",
"Aokigahara Forest (10863181206).jpg",
"Aokigahara Forest (10863196716).jpg",
"Aokigahara Forest (10863201036).jpg",
"Aokigahara Forest (10863202696).jpg",
"Aokigahara Forest (10863271994).jpg",
"Aokigahara Forest (10863283354).jpg",
"Aokigahara Forest (10863292224).jpg",
"Aokigahara Forest (10863293524).jpg",
"Aokigahara Forest (10863294354).jpg",
"Aokigahara Forest (10863296084).jpg",
"Aokigahara Forest (10863296864).jpg",
"Aokigahara Forest (10863297654).jpg",
"Aokigahara Forest (10863453833).jpg",
"Aokigahara Forest (10863460263).jpg",
"Aokigahara Forest (10863465773).jpg",
"Aokigahara Forest (10863467383).jpg",
"Aokigahara Forest (10863468883).jpg",
"Aokigahara Forest (10863480593).jpg",
"Aokigahara Forest (10863487993).jpg",
"Aokigahara forest 01.jpg",
"Aokigahara forest 02.jpg",
"Aokigahara forest 03.jpg",
"Aokigahara forest 04.jpg",
"Aokigahara Forest.jpg",
"Aokigahara Suicide Forest Japan.jpg",
"Aokigahara.JPG",
"Aokigara forest near wind cave 01.jpg",
"Aokigara forest near wind cave 02.jpg",
"Aokigara forest near wind cave 03.jpg",
"Aokigara forest near wind cave 04.jpg",
"Aokigara forest near wind cave 05.jpg",
"Aokigara forest near wind cave 06.jpg",
"Aokigara forest near wind cave 07.jpg",
"Entrance @ Ice Cave @ Aokigahara Forest (10863265844).jpg",
"Entrance @ Wind Cave @ Aokigahara Forest (10863287014).jpg",
"Fujisan, sacred place and source of artistic inspiration banner (Mount Fuji and Aokigahara).jpg",
"Hiking in Aokigahara Sea of Trees (50295849761).jpg",
"Inside Aokigara forest.ogv",
"Lake Motosu from Mount Ashiwada.jpg",
"Lake Sai and Aokigahara Forest Aerial photograph.jpg",
"Lake Sai and Aokigahara from Koyodai.jpg",
"Lake Sai and Mount Ashiwada.jpg",
"Lake Shōji from Panoramadai.JPG",
"Leave @ Aokigahara Forest (10863491293).jpg",
"LianaSwing.jpg",
"Lightbathing (22769737922).jpg",
"Mount Ashiwada and Aokigahara.jpg",
"Mount Ashiwada and Mount Fuji.jpg",
"Mount Ashiwada from Panoramadai.JPG",
"Mount Eboshi (Misaka Mountains).JPG",
"Mount Kenashi and Mount Ryu from Mount Ashiwada.jpg",
"Mount O and Lake Sai.JPG",
"Mount O and Mount Oni from Mount Ryu.JPG",
"Mount O and Mount Oni.JPG",
"Mount O from Mount Ryu.JPG",
"Mount O from Sankodai.JPG",
"SaiKo.jpg",
"Suicide Forest.jpg",
"Tenshi Mountains from Mount Ashiwada (with note).jpg",
"Warning signal for suicides in Aokigahara.jpg",
]

fugaku = [
"Facility for storing eggs of silk worms, Fugaku Wind Cave - July 2012.jpg",
"Fugaku fuketsu - Ice pond.jpg",
"Fugaku fuketsu - Natural refrigerator.jpg",
"Fugaku fuketsu - Walking in the cave.jpg",
"Fugaku Fuketu Entrance 20161025.jpg",
"Fugaku Fuketu Entrance Stairs 20161025.jpg",
"Ice Block in Fugaku wind cave.jpg",
"Lava shelf in Fugaku wind cave.jpg",
"Ropy lava in Fugaku wind cave.jpg",
]

narusawa = [
"Icicle in Narusawa Ice Cave.jpg",
"Lighting-uped Narusawa Ice Cave.jpg",
"Narusawa Hyoketsu Entrance 20161025.jpg",
"Narusawa-Hyoketsu-entrance.JPG",
"Stairs and passage towards the Narusawa Hyoketsu 20161025.jpg",
"頭上 足元 (1244710628).jpg",
]

bat = [
"Inside the Lake Saiko Bat Cave A-Point.JPG",
"Inside the Lake Saiko Bat Cave B-Point.JPG",
"Inside the Lake Saiko Bat Cave C-Point.JPG",
"Japan - Fujisan Area - Volcano Cave.jpg",
"Lake Saiko Bat Cave Corded Lava.JPG",
"Lake Saiko Bat Cave Diatom Earth Line.JPG",
"Lake Saiko Bat Cave Entrance.JPG",
"Lake Saiko Bat Cave Helmet rental.JPG",
"Lake Saiko Bat Cave Lava Dome.JPG",
"Lake Saiko Bat Cave Lava Stalactites.JPG",
"The written version of the name of Lake Sai and Aokigahara Forest Aerial photograph.jpg",
"Trail toward the Lake Saiko Bat Cave.JPG",
"Viewed from outside the Lake Saiko Bat Cave.JPG",
]

map_sources = [
    {
        'title':'Yamanashi Prefecture - Aokigahara Jukai Forest Guidelines (2026)',
        'url':'https://www.pref.yamanashi.jp/documents/97765/aokigaharajukaiforestguidelines.pdf',
        'role':'Primary route/cave geography. Figures map the Mt Omuro sector, Lake Sai sector, and general road/trail/forest-road network; distinguishes usable routes and designated natural-monument caves.',
        'grade':'A - primary official'
    },
    {
        'title':'Geospatial Information Authority of Japan - Volcano Land Condition Map, Fuji',
        'url':'https://www.gsi.go.jp/common/000253398.pdf',
        'role':'Critical microtopography. Figure 11 is LiDAR shaded relief around Aokigahara/Mt Omuro; Figure 12 is the corresponding 1:25,000 topographic map. Useful for lava-flow lobes, flow fronts, fissure/crater rows and terrain under canopy.',
        'grade':'A - primary official'
    },
    {
        'title':'Geological Survey of Japan - Geological Map of Fuji Volcano, 2nd ed. (2016)',
        'url':'https://www.gsj.jp/Map/EN/docs/misc_doc/misc_12_2nd.html',
        'role':'Authoritative 1:50,000 geology with downloadable vector data; use to separate Aokigahara/Jogan lava from older/younger units.',
        'grade':'A - primary official'
    },
    {
        'title':'GSJ Open-File Report 592 - Geological Map of Fuji Volcano, 2nd ed. Ver.1 (2014)',
        'url':'https://www.gsj.jp/publications/pub/openfile/openfile0592.html',
        'role':'Includes a high-resolution 1:25,000 raster geological map and legend. Useful as a second geology layer/check against the 2016 publication.',
        'grade':'A - primary official'
    },
    {
        'title':'GSI Maps / GSI Maps Vector',
        'url':'https://maps.gsi.go.jp/vector/',
        'role':'Current Japanese topography, contours, seamless aerial photography, elevation and relief. Best operational base for road/path/edge alignment and terrain validation.',
        'grade':'A - primary official'
    },
    {
        'title':'OpenStreetMap',
        'url':'https://www.openstreetmap.org/',
        'role':'Best open vector reference for current roads, tracks, paths, POIs and cave entrances. Validate important features against official sources before treating as authoritative.',
        'grade':'B - open community GIS'
    },
    {
        'title':'Official Yamanashi Tourism - Aokigahara Forest',
        'url':'https://www.yamanashi-kankou.jp/english/recover/aokigahara-forest.html',
        'role':'Official overview: forest on 864 lava, approximately 30 km², and designated paths connecting Narusawa Ice Cave, Fugaku Wind Cave and West Lake Bat Cave.',
        'grade':'A/B - official tourism'
    },
    {
        'title':'Narusawa Village - digital tourism brochures',
        'url':'https://www.vill.narusawa.yamanashi.jp/gyosei/soshikikarasagasu/kikakuka/koho_event/kankopamphlet/index.html',
        'role':'Official local PDFs and trekking maps; useful for Narusawa-side access, road geometry and surrounding mountain/trail context.',
        'grade':'A/B - official local'
    },
    {
        'title':'UNESCO - Fujisan maps',
        'url':'https://whc.unesco.org/en/list/1418/maps/',
        'role':'Protection/property context around Mount Fuji. Not an Aokigahara forest-boundary map, but useful for the wider protected cultural landscape.',
        'grade':'A - international official'
    },
    {
        'title':'Web Japan / niponica - Aokigahara schematic map',
        'url':'https://web-japan.org/niponica/niponica13/ja/feature/feature04.html',
        'img':'https://web-japan.org/niponica/images/ja/niponica13/feature04-06.jpg',
        'role':'Clear simplified orientation showing lakes, Route 139, principal caves, Mt Omuro and Aokigahara footprint.',
        'grade':'B - government information portal'
    },
    {
        'title':'Japanese Landform Atlas - Aokigahara lava-tunnel topography',
        'url':'https://www.web-gis.jp/GM1000/GM_Red1/GM_Red1-107.html',
        'img':'https://www.web-gis.jp/GM1000/GM_Red1/Photo/GM_Red1-107a.jpg',
        'role':'3D terrain view with cave/tunnel locations and lakes; useful for macro spatial relationships and topographic silhouette.',
        'grade':'B - specialist secondary'
    },
    {
        'title':'Yamanashi tourism terrain-context image',
        'url':'https://www.yamanashi-kankou.jp/portuguese/staff-journal/aokigahara2022pt.html',
        'img':'https://www.yamanashi-kankou.jp/portuguese/staff-journal/images/aokigahara2022pt6.png',
        'role':'Broad shaded-relief context of Aokigahara relative to Fuji and the Five Lakes; useful as an orientation layer, not a survey boundary.',
        'grade':'B - official tourism'
    },
    {
        'title':'Volcanological research - Jogan/Aokigahara lava-flow morphology',
        'url':'https://www.jstage.jst.go.jp/browse/vsj/2004/0/_contents/-char/en',
        'role':'Research literature on surface morphology and eruption process of the Aokigahara lava flow; use to explain flow texture, vents, lobe stacking and original lake division.',
        'grade':'A/B - academic'
    },
]

# Semantic role tags based on filename/category.
def tags_for(name, group):
    s=name.lower()
    tags=[]
    if group=='main': tags.append('aokigahara')
    if 'aerial' in s or 'panorama' in s or 'mount ' in s or 'mount fuji' in s or 'lake ' in s or 'saiko' in s or 'sankodai' in s or 'koyodai' in s or 'tenshi' in s or 'misaka' in s or 'misak' in s:
        tags.append('macro / edge / skyline')
    if 'forest' in s or 'liana' in s or 'lightbathing' in s or 'hiking' in s or 'leave @' in s:
        tags.append('interior / vegetation')
    if 'entrance' in s or 'cave' in s or 'fuketsu' in s or 'hyoketsu' in s or 'lava' in s or 'ice' in s or 'icicle' in s:
        tags.append('cave / lava')
    if 'warning' in s:
        tags.append('signage / visitor infrastructure')
    if group=='Fugaku Wind Cave': tags.append('Fugaku Wind Cave')
    if group=='Narusawa Ice Cave': tags.append('Narusawa Ice Cave')
    if group=='Lake Saiko Bat Cave': tags.append('Lake Saiko Bat Cave')
    if name.endswith('.ogv'): tags.append('motion reference')
    return '; '.join(dict.fromkeys(tags)) or 'general reference'

rows=[]
for group, files in [('main',main_files),('Fugaku Wind Cave',fugaku),('Narusawa Ice Cave',narusawa),('Lake Saiko Bat Cave',bat)]:
    for name in files:
        file_page='https://commons.wikimedia.org/wiki/File:' + quote(name.replace(' ','_'), safe='()@+,-._~%')
        media='https://commons.wikimedia.org/wiki/Special:Redirect/file/' + quote(name, safe='()@+,-._~')
        if not name.lower().endswith('.ogv'):
            media += '?width=900'
        rows.append({
            'title':name,
            'group':group,
            'tags':tags_for(name, group),
            'source_page':file_page,
            'media_url':media,
            'notes':'Wikimedia Commons; open source page for author, exact licence, original resolution and any geotags.'
        })

# Dedupe
seen=set(); unique=[]
for r in rows:
    if r['title'] not in seen:
        unique.append(r); seen.add(r['title'])
rows=unique

# CSV manifest
csv_path=out/'Aokigahara_visual_asset_manifest.csv'
with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
    w=csv.DictWriter(f, fieldnames=['title','group','tags','source_page','media_url','notes'])
    w.writeheader(); w.writerows(rows)

# HTML
photo_count=sum(not r['title'].lower().endswith('.ogv') for r in rows)
video_count=sum(r['title'].lower().endswith('.ogv') for r in rows)

def esc(x): return html.escape(x, quote=True)

def gallery_section(title, subtitle, items):
    cards=[]
    for r in items:
        if r['title'].lower().endswith('.ogv'):
            cards.append(f'''<article class="card video-card"><div class="video-placeholder">Motion reference</div><div class="cap"><b>{esc(r['title'])}</b><span>{esc(r['tags'])}</span><a href="{esc(r['source_page'])}" target="_blank" rel="noopener">Open Commons source / video</a></div></article>''')
        else:
            cards.append(f'''<article class="card"><a class="imgwrap" href="{esc(r['source_page'])}" target="_blank" rel="noopener"><img loading="lazy" decoding="async" src="{esc(r['media_url'])}" alt="{esc(r['title'])}"></a><div class="cap"><b>{esc(r['title'])}</b><span>{esc(r['tags'])}</span><a href="{esc(r['source_page'])}" target="_blank" rel="noopener">Source, author, licence & original</a></div></article>''')
    return f'''<section><h2>{esc(title)}</h2><p class="section-note">{esc(subtitle)}</p><div class="gallery">{''.join(cards)}</div></section>'''

map_cards=[]
for m in map_sources:
    img = ''
    if m.get('img'):
        img=f'<a class="mapimg" href="{esc(m["url"])}" target="_blank" rel="noopener"><img loading="lazy" src="{esc(m["img"])}" alt="{esc(m["title"])}"></a>'
    map_cards.append(f'''<article class="mapcard">{img}<div><div class="grade">{esc(m['grade'])}</div><h3>{esc(m['title'])}</h3><p>{esc(m['role'])}</p><a href="{esc(m['url'])}" target="_blank" rel="noopener">Open source</a></div></article>''')

html_text=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aokigahara Reconstruction Research Dossier</title>
<style>
:root{{--bg:#0f1110;--panel:#181b19;--panel2:#20241f;--text:#edf0ea;--muted:#b7c0b4;--line:#333a32;--accent:#dfe9dc;--warn:#e8dca8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}}
a{{color:var(--accent)}} .hero{{padding:54px max(24px,6vw) 30px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#151915,var(--bg))}}
h1{{font-size:clamp(32px,5vw,64px);line-height:1.02;margin:0 0 16px;max-width:1100px;letter-spacing:-.03em}} .dek{{font-size:18px;max-width:1050px;color:var(--muted)}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0 0}} .stat{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:11px 14px}} .stat b{{font-size:20px;display:block}}
main{{padding:28px max(18px,5vw) 80px;max-width:1800px;margin:auto}} section{{margin:26px 0 54px}} h2{{font-size:28px;margin:0 0 8px}} .section-note{{color:var(--muted);max-width:1100px;margin:0 0 18px}}
.callout{{background:#1b211b;border:1px solid #3f4a3d;border-radius:16px;padding:18px 20px;margin:18px 0}} .callout strong{{color:var(--warn)}}
.workflow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:18px}} .step{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}} .step b{{display:block;margin-bottom:5px}} .step p{{margin:0;color:var(--muted)}}
.mapgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}} .mapcard{{background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden}} .mapcard>div{{padding:16px}} .mapimg{{display:block;aspect-ratio:16/10;background:#111}} .mapimg img{{width:100%;height:100%;object-fit:cover;display:block}} .mapcard h3{{margin:4px 0 8px;font-size:19px}} .mapcard p{{color:var(--muted);margin:0 0 10px}} .grade{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#b9c7b5}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;min-width:0}} .imgwrap{{display:block;aspect-ratio:4/3;background:#111;overflow:hidden}} .imgwrap img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .2s ease}} .imgwrap:hover img{{transform:scale(1.015)}} .cap{{padding:11px 12px 13px}} .cap b{{display:block;font-size:13px;line-height:1.35;margin-bottom:6px;word-break:break-word}} .cap span{{display:block;color:var(--muted);font-size:12px;margin-bottom:7px}} .cap a{{font-size:12px}}
.video-placeholder{{aspect-ratio:4/3;display:grid;place-items:center;background:linear-gradient(135deg,#1b221b,#293229);font-size:19px;color:#cbd8c8}}
.source-note{{font-size:13px;color:var(--muted)}} footer{{padding:25px max(18px,5vw);color:var(--muted);border-top:1px solid var(--line)}}
@media print{{body{{background:white;color:#111}} .hero,.card,.mapcard,.step,.callout,.stat{{background:white;color:#111;border-color:#ccc}} .dek,.section-note,.mapcard p,.step p,.cap span,.source-note,footer{{color:#444}} .gallery{{grid-template-columns:repeat(3,1fr)}} a{{color:#111}}}}
</style>
</head>
<body>
<header class="hero">
<h1>Aokigahara: visual & geospatial reconstruction dossier</h1>
<p class="dek">A source atlas for recreating the real place rather than an imagined “forest”: macro extent, terrain, 864 Jōgan lava morphology, forest edges, lakes, roads, trails, cave systems, canopy/interior texture, visitor infrastructure and key viewpoints.</p>
<div class="stats"><div class="stat"><b>{photo_count}</b>still-image references</div><div class="stat"><b>{video_count}</b>motion reference</div><div class="stat"><b>{len(map_sources)}</b>map / GIS / geology sources</div><div class="stat"><b>2026</b>official guideline layer included</div></div>
</header>
<main>
<section>
<h2>How to use this dossier</h2>
<div class="callout"><strong>Do not treat “Aokigahara” as one perfectly defined polygon.</strong> Sources quote roughly 30–35 km² because the name can refer to a modern forested landscape, the Jōgan/Aokigahara lava field, a protected/natural-monument context, or a tourism-defined area. For a faithful digital reconstruction, align several layers instead of forcing one outline.</div>
<div class="workflow">
<div class="step"><b>1. Geology first</b><p>Use GSJ vectors/raster to place the AD 864–866 Aokigahara/Jōgan lava units, older cones and flow boundaries.</p></div>
<div class="step"><b>2. Terrain second</b><p>Use GSI LiDAR/elevation/shaded-relief material to recover lava lobes, flow fronts, fissure rows and micro-relief hidden by canopy.</p></div>
<div class="step"><b>3. Modern surface</b><p>Use current GSI aerial imagery plus OSM/local maps for canopy edge, roads, tracks, car parks, paths, buildings and current visitor infrastructure.</p></div>
<div class="step"><b>4. Ground truth</b><p>Use the image atlas below to match tree density, trunk scale, roots over basalt, moss/lichen, light penetration, path surfacing, cave entrances and lake-edge views.</p></div>
<div class="step"><b>5. Validate by viewpoints</b><p>Reproduce Sankodai/Koyodai/Lake Sai macro views and check skyline, relative lake positions, Mt Omuro and Mount Fuji alignment.</p></div>
</div>
</section>

<section><h2>Primary maps, terrain & geology</h2><p class="section-note">These are more important than the photo gallery for exact placement. The highest-value pair is the 2026 Yamanashi forest-guidelines mapping plus GSI/GSJ terrain/geology.</p><div class="mapgrid">{''.join(map_cards)}</div></section>

{gallery_section('Aokigahara main visual corpus', 'Wikimedia Commons currently lists 82 files in the Aokigahara category. This section indexes the complete current category set gathered for the dossier, including broad aerials, overlooks, interior forest, path/edge views, lakes and signage. The motion clip is linked rather than auto-loaded.', [r for r in rows if r['group']=='main'])}
{gallery_section('Fugaku Wind Cave detail set', 'Entrance geometry, stairs, interior passage, ice, ropy lava, lava shelf and historic cold-storage use.', [r for r in rows if r['group']=='Fugaku Wind Cave'])}
{gallery_section('Narusawa Ice Cave detail set', 'Entrance geometry, descent/passage and ice formations. Useful for vertical proportions, lighting, wall/floor material and circulation.', [r for r in rows if r['group']=='Narusawa Ice Cave'])}
{gallery_section('Lake Saiko Bat Cave detail set', 'Exterior/approach, A/B/C interior points, corded lava, lava dome, stalactites and visitor infrastructure.', [r for r in rows if r['group']=='Lake Saiko Bat Cave'])}

<section>
<h2>Reconstruction priorities the image corpus should answer</h2>
<div class="workflow">
<div class="step"><b>Macro silhouette</b><p>Forest–lake boundaries, visible cones/ridges, Mt Fuji direction, Mt Omuro scale and relationship to the Five Lakes.</p></div>
<div class="step"><b>Canopy structure</b><p>Mixed conifer/broadleaf composition, trunk spacing, vertical density, irregular crown profile and seasonal variation.</p></div>
<div class="step"><b>Ground morphology</b><p>Shallow soil, exposed basalt, collapsed/ropy lava, hummocks, surface roots, moss carpets and low understorey.</p></div>
<div class="step"><b>Light & atmosphere</b><p>Canopy occlusion, muted indirect light, dappled shafts, humidity/green bounce, winter snow contrast and autumn colour.</p></div>
<div class="step"><b>Human layer</b><p>Route 139, prefectural/forest roads, narrow surfaced tracks, signed paths, cave visitor structures, fences and car parks.</p></div>
<div class="step"><b>Subsurface</b><p>Three principal tourist lava caves plus other mapped protected caves; treat exact accessible/non-accessible status from the 2026 guideline map as authoritative.</p></div>
</div>
<p class="source-note">Licence note: the gallery hotlinks to Wikimedia Commons thumbnails and links each file page for author/licence/original metadata. External map previews remain hosted by their source sites. For a production asset pack, download only after checking each file’s stated licence and attribution requirements.</p>
</section>
</main>
<footer>Compiled 9 September 2026. Designed as a source atlas, not as a claim that every illustrated boundary is legally or geologically identical.</footer>
</body></html>'''

html_path=out/'Aokigahara_Reconstruction_Research_Dossier.html'
html_path.write_text(html_text, encoding='utf-8')

print('HTML:', html_path)
print('CSV:', csv_path)
print('main files', len(main_files), 'fugaku', len(fugaku), 'narusawa', len(narusawa), 'bat', len(bat), 'unique total', len(rows), 'still', photo_count, 'video', video_count)
