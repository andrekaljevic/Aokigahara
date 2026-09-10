from pathlib import Path
from pyproj import Transformer
from shapely.geometry import box, LineString, Point, mapping
from shapely.ops import transform as shp_transform
import json, csv, math, html

OUT=Path('/mnt/data')
BBOX={'west':138.55,'south':35.43,'east':138.72,'north':35.53}
TO_METRIC=Transformer.from_crs(4326,6676,always_xy=True)
TO_WGS=Transformer.from_crs(6676,4326,always_xy=True)

def ll_to_xy(lon,lat): return TO_METRIC.transform(lon,lat)
def xy_to_ll(x,y): return TO_WGS.transform(x,y)

def norm_extent(lons,lats):
    return {'west':min(lons),'east':max(lons),'south':min(lats),'north':max(lats)}

veg_sheets=[
    {
        'sheet_id':'533815','name':'Narusawa 1:25,000 Existing Vegetation Map',
        'extent':norm_extent([138.7052,138.6219],[35.4199,35.5449]),
        'survey_period':'2004-04-01/2005-03-31','formats':'JPEG, Shp',
        'source':'https://www.biodic.go.jp/chm/dataset/9e762c9ab2e86fc651f47989c60f9f07',
        'note':'Official Ministry of the Environment Biodiversity Center metadata. Direction labels in metadata appear inverted; this build normalises the numeric min/max extent only.'
    },
    {
        'sheet_id':'533805','name':'Fuji 1:25,000 Existing Vegetation Map',
        'extent':norm_extent([138.7052,138.6219],[35.3366,35.4616]),
        'survey_period':'2004-04-01/2005-03-31','formats':'JPEG, Shp',
        'source':'https://www.biodic.go.jp/chm/dataset/fac603a7f0494ecc052793c5d5e92095',
        'note':'Official Ministry of the Environment Biodiversity Center metadata. Direction labels in metadata appear inverted; this build normalises the numeric min/max extent only.'
    },
]

control_points=[
    {'name':'Fugaku Wind Cave','lat':35.477444,'lon':138.657361,'type':'cave / route control','confidence':'B+','coordinate_basis':'geotagged/open-map cross-check; validate against GSI before final lock','source_url':'https://commons.wikimedia.org/wiki/Category:Fugaku_Wind_Cave','official_geometry_url':'https://www.pref.yamanashi.jp/bunka/bunkazaihogo/bunkazai_data/yamanashinobunkazai_nb0014.html'},
    {'name':'Narusawa Ice Cave','lat':35.474778,'lon':138.666528,'type':'cave / route control','confidence':'B+','coordinate_basis':'geotagged/open-map cross-check; validate against GSI before final lock','source_url':'https://commons.wikimedia.org/wiki/Category:Narusawa_Ice_Cave','official_geometry_url':'https://www.pref.yamanashi.jp/bunka/bunkazaihogo/bunkazai_data/yamanashinobunkazai_nb0014.html'},
    {'name':'Lake Saiko Bat Cave','lat':35.493111,'lon':138.672861,'type':'cave / route control','confidence':'B+','coordinate_basis':'geotagged/open-map cross-check; validate against GSI before final lock','source_url':'https://commons.wikimedia.org/wiki/Category:Lake_Saiko_Bat_Cave','official_geometry_url':'https://www.pref.yamanashi.jp/bunka/bunkazaihogo/bunkazai_data/yamanashinobunkazai_nb0014.html'},
    {'name':'Ryugu Cave','lat':35.48509,'lon':138.66813,'type':'cave / route control','confidence':'B','coordinate_basis':'OSM/secondary map cross-check; source spread is tens of metres','source_url':'https://www.openstreetmap.org/search?query=Ryugu%20Cave%20Yamanashi','official_geometry_url':'https://www.yamanashi-kankou.jp/kankou/spot/ryugudoketsu.html'},
    {'name':'Sankodai','lat':35.48792,'lon':138.68247,'type':'panorama / camera validation','confidence':'B','coordinate_basis':'secondary map cross-check; validate exact camera stations in field/GPX','source_url':'https://www.openstreetmap.org/search?query=Sankodai%20Yamanashi','official_geometry_url':''},
    {'name':'Koyodai ridge / viewpoint','lat':35.48426,'lon':138.67956,'type':'panorama / camera validation','confidence':'B','coordinate_basis':'secondary map cross-check; several nearby named viewpoint points exist','source_url':'https://www.openstreetmap.org/search?query=Koyodai%20Yamanashi','official_geometry_url':'https://www.yamanashi-kankou.jp/kankou/spot/koyodai.html'},
    {'name':'Omuro Cave','lat':35.44784,'lon':138.66147,'type':'protected cave control','confidence':'B','coordinate_basis':'secondary geographic gazetteer cross-check; validate against official schematic/GSI','source_url':'https://www.openstreetmap.org/search?query=Omuro%20Cave%20Yamanashi','official_geometry_url':'https://www.pref.yamanashi.jp/documents/97765/guidelineryakuzu.pdf'},
]
for p in control_points:
    p['x_m'],p['y_m']=ll_to_xy(p['lon'],p['lat'])

# Approximate evidence corridors are deliberately NOT route geometry. They exist only to score which cells have route-continuous evidence nearby.
# Each corridor is supported by an official schematic or a public GPS/activity source but is simplified to known anchors.
route_evidence=[
    {
        'id':'R1','name':'Fugaku–Narusawa public cave corridor','confidence':'B','basis':'YAMAP model course 2.5 km / 1:02 / 58 m up-down plus Yamanashi current route context',
        'source_url':'https://yamap.com/model-courses/95828',
        'points':[(138.657361,35.477444),(138.666528,35.474778)]
    },
    {
        'id':'R2','name':'Saiko cave / viewpoint evidence chain','confidence':'C+','basis':'control-point chain for evidence proximity only; not a claimed surveyed trail line',
        'source_url':'https://www.pref.yamanashi.jp/documents/97765/guidelineryakuzu.pdf',
        'points':[(138.672861,35.493111),(138.66813,35.48509),(138.67956,35.48426),(138.68247,35.48792)]
    },
    {
        'id':'R3','name':'Route 139 to Sankodai evidence chain','confidence':'C+','basis':'2026 YAMAP 11.8 km activity confirms Fugaku → Narusawa → Koyodai/Sankodai ordering; simplified for coverage scoring only',
        'source_url':'https://yamap.com/activities/47364623',
        'points':[(138.657361,35.477444),(138.666528,35.474778),(138.67956,35.48426),(138.68247,35.48792)]
    }
]
route_lines=[]
for r in route_evidence:
    coords=[ll_to_xy(lon,lat) for lon,lat in r['points']]
    route_lines.append((r,LineString(coords)))

# Make 250m metric grid across broad research AOI. The AOI is a research envelope, not a forest boundary.
x1,y1=ll_to_xy(BBOX['west'],BBOX['south']); x2,y2=ll_to_xy(BBOX['east'],BBOX['north'])
minx,maxx=sorted([x1,x2]); miny,maxy=sorted([y1,y2])
cell=250.0
startx=math.floor(minx/cell)*cell; endx=math.ceil(maxx/cell)*cell
starty=math.floor(miny/cell)*cell; endy=math.ceil(maxy/cell)*cell

features=[]; grid_rows=[]
counts={'High':0,'Medium':0,'Low':0}
priority_counts={'P1':0,'P2':0,'P3':0}

def within_extent(lon,lat,e): return e['west'] <= lon <= e['east'] and e['south'] <= lat <= e['north']

# Research-focus envelope is only a prioritisation device; it is not the forest boundary.
focus_box=box(*ll_to_xy(138.575,35.442),*ll_to_xy(138.695,35.505))

idx=0
for ix,x in enumerate([startx+i*cell for i in range(int(round((endx-startx)/cell)))]):
    for iy,y in enumerate([starty+j*cell for j in range(int(round((endy-starty)/cell)))]):
        poly=box(x,y,x+cell,y+cell)
        c=poly.centroid
        lon,lat=xy_to_ll(c.x,c.y)
        if not (BBOX['west']-0.005 <= lon <= BBOX['east']+0.005 and BBOX['south']-0.005 <= lat <= BBOX['north']+0.005):
            continue
        idx += 1
        gid=f'G{ix:03d}_{iy:03d}'
        # Nearest control point.
        dists=[(math.hypot(c.x-p['x_m'],c.y-p['y_m']),p['name']) for p in control_points]
        nearest_d,nearest_name=min(dists)
        # Nearest simplified route-evidence corridor.
        route_dist, route_name=min((line.distance(c),r['name']) for r,line in route_lines)
        # Vegetation sheet coverage.
        sheets=[v['sheet_id'] for v in veg_sheets if within_extent(lon,lat,v['extent'])]
        if sheets:
            veg_status='covered by identified 1:25k vegetation GIS sheet(s): '+','.join(sheets)
            veg_score=2
        elif lon < 138.6219 and 35.42 <= lat <= 35.545:
            veg_status='western gap: adjacent Shoji-sheet vegetation GIS retrieval still required'
            veg_score=0
        else:
            veg_status='outside the two identified vegetation sheets / context; retrieve adjoining sheet if build extends here'
            veg_score=1
        # Evidence heuristic (not physical certainty).
        if nearest_d <= 450 or route_dist <= 300:
            visual='High'; visual_score=3
        elif nearest_d <= 1100 or route_dist <= 800:
            visual='Medium'; visual_score=2
        else:
            visual='Low'; visual_score=1
        if route_dist <= 300:
            route_conf='High'
        elif route_dist <= 800 or nearest_d <= 850:
            route_conf='Medium'
        else:
            route_conf='Low'
        # Terrain source is identified globally, but actual DEM mesh availability has not been downloaded/verified.
        terrain_status='GSI terrain source identified; exact 1m/5m tile coverage not yet locally verified'
        # Overall research confidence deliberately cannot exceed Medium unless close to both route/control evidence and vegetation GIS coverage.
        if visual=='High' and veg_score==2 and route_conf in ('High','Medium'):
            overall='High'
        elif visual!='Low' or veg_score==2:
            overall='Medium'
        else:
            overall='Low'
        counts[overall]+=1
        in_focus=focus_box.contains(c)
        # Priority is the urgency of further research, not importance of the physical cell.
        if in_focus and (overall=='Low' or veg_score==0 or route_conf=='Low'):
            priority='P1'
        elif in_focus or overall=='Medium':
            priority='P2'
        else:
            priority='P3'
        priority_counts[priority]+=1
        props={
            'grid_id':gid,'cell_size_m':250,'centroid_lon':round(lon,6),'centroid_lat':round(lat,6),
            'project_crs':'EPSG:6676','research_aoi_only':True,
            'nearest_anchor':nearest_name,'nearest_anchor_m':round(nearest_d,1),
            'nearest_route_evidence':route_name,'nearest_route_evidence_m':round(route_dist,1),
            'visual_route_evidence':visual,'route_evidence_confidence':route_conf,
            'vegetation_gis_status':veg_status,'terrain_source_status':terrain_status,
            'overall_reconstruction_evidence':overall,'research_priority':priority,
            'focus_envelope_heuristic':bool(in_focus),
            'warning':'Cell confidence measures evidence density, not whether the cell is inside the legal/geological/forest boundary.'
        }
        # Convert corners to WGS84 for GeoJSON.
        coords=[]
        for xx,yy in list(poly.exterior.coords):
            lo,la=xy_to_ll(xx,yy); coords.append([round(lo,7),round(la,7)])
        features.append({'type':'Feature','properties':props,'geometry':{'type':'Polygon','coordinates':[coords]}})
        grid_rows.append(props)

geojson={
    'type':'FeatureCollection',
    'name':'Aokigahara 250 m reconstruction evidence grid',
    'crs_note':'Geometry serialized as WGS84 EPSG:4326; cells generated as 250 m squares in EPSG:6676.',
    'disclaimer':'This is a research/evidence coverage grid over a broad AOI, not an Aokigahara boundary or access map.',
    'features':features
}
(OUT/'Aokigahara_250m_coverage_grid.geojson').write_text(json.dumps(geojson,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

with (OUT/'Aokigahara_250m_coverage_grid.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(grid_rows[0].keys())); w.writeheader(); w.writerows(grid_rows)

with (OUT/'Aokigahara_georegistration_control_points.csv').open('w',newline='',encoding='utf-8-sig') as f:
    fields=['name','lat','lon','x_m','y_m','type','confidence','coordinate_basis','source_url','official_geometry_url']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:(round(v,3) if k in ('x_m','y_m') else v) for k,v in p.items()} for p in control_points])

# Coverage methodology report.
coverage_report={
    'generated':'2026-09-09',
    'grid':{'cell_size_m':250,'feature_count':len(features),'research_aoi_wgs84_bbox':BBOX,'generation_crs':'EPSG:6676','serialized_geometry_crs':'EPSG:4326'},
    'overall_evidence_counts':counts,'research_priority_counts':priority_counts,
    'methodology':[
        'The grid covers a broad research AOI and must not be interpreted as the forest boundary.',
        'Evidence confidence is a heuristic based on proximity to known/geotagged control points, simplified route-evidence corridors and identified vegetation-GIS sheet coverage.',
        'Route-evidence corridors are deliberately simplified and are NOT surveyed trail geometry.',
        'GSI terrain data sources are identified, but this pass does not claim 1 m or 5 m DEM tile availability until the actual mesh files are downloaded and checked.',
        'A cell can be high-confidence for research coverage while still lying outside Aokigahara proper; boundary membership must come from aligned forest/lava/protection layers.'
    ],
    'vegetation_gis_sheets':veg_sheets,
    'route_evidence':route_evidence,
    'control_points':[{k:v for k,v in p.items() if k not in ('x_m','y_m')} for p in control_points],
    'next_high_value_actions':[
        'Retrieve the western 1:25,000 vegetation sheet(s), beginning with the Shoji mesh 533814, because the identified Narusawa/Fuji sheets begin at ~138.6219 E.',
        'Download actual GSI elevation mesh files for the AOI and record which cells have 1 m, DEM5A, DEM5B/5C or only 10 m coverage.',
        'Georegister the Yamanashi 2026 route/cave schematic using Fugaku, Narusawa, Saiko Bat Cave, Lake Sai/Route 139 and other stable controls; store residual error rather than treating the schematic as survey geometry.',
        'Acquire or extract route geometry from current public GPX/activity sources for the Route 139 cave corridor, Saiko/Wild Bird Forest and Shoji entrance routes.',
        'Hunt cell-by-cell for geotagged imagery/video in P1 cells, especially the western Motosu/Shoji and central/high-ground sectors.'
    ]
}
(OUT/'Aokigahara_coverage_methodology.json').write_text(json.dumps(coverage_report,ensure_ascii=False,indent=2),encoding='utf-8')

# Add high-value new sources/assets to the manifest.
manifest=OUT/'Aokigahara_visual_asset_manifest.csv'
rows=list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
new_assets=[
 {'title':'Yamanashi 2026 official usable-route / cave schematic','group':'official map/document','tags':'route network; caves; forest roads; Mt Omuro; Lake Sai','source_page':'https://www.pref.yamanashi.jp/documents/97765/guidelineryakuzu.pdf','media_url':'https://www.pref.yamanashi.jp/documents/97765/guidelineryakuzu.pdf','notes':'Primary official schematic. Distinguishes usable routes, old transport roads/forest roads and protected lava caves. Georegister; do not treat as survey geometry.'},
 {'title':'Ministry of Environment 1:25,000 existing vegetation map — Narusawa 533815','group':'official GIS/document','tags':'vegetation GIS; 1:25000; Narusawa; polygons','source_page':veg_sheets[0]['source'],'media_url':veg_sheets[0]['source'],'notes':'Official Biodiversity Center metadata; JPEG and Shp formats; 2004–05 survey. Use as polygon source for spatial vegetation classes.'},
 {'title':'Ministry of Environment 1:25,000 existing vegetation map — Fuji 533805','group':'official GIS/document','tags':'vegetation GIS; 1:25000; Fuji; polygons','source_page':veg_sheets[1]['source'],'media_url':veg_sheets[1]['source'],'notes':'Official Biodiversity Center metadata; JPEG and Shp formats; 2004–05 survey. Complements Narusawa sheet to the south.'},
 {'title':'YAMAP current Fugaku Wind Cave – Narusawa Ice Cave model course','group':'route / GPX evidence','tags':'route; current activity; Fugaku; Narusawa; Tokai Nature Trail','source_page':'https://yamap.com/model-courses/95828','media_url':'https://yamap.com/model-courses/95828','notes':'Current public route evidence. Model course reports 2.5 km, 1:02, 58 m ascent/descent; useful for route continuity, not authoritative survey geometry.'},
 {'title':'YAMAP 2026 Aokigahara – Sankodai – Ashiwadayama activity','group':'route / GPX evidence','tags':'route; 2026; Fugaku; Narusawa; Koyodai; Sankodai','source_page':'https://yamap.com/activities/47364623','media_url':'https://yamap.com/activities/47364623','notes':'11.8 km activity dated 2026-04-11; checkpoint order provides current continuity evidence from cave corridor to Koyodai/Sankodai.'},
 {'title':'YAMAP Shoji entrance trail activity index','group':'route / GPX evidence','tags':'Shoji entrance; route; 2026; western/central coverage','source_page':'https://yamap.com/landmarks/52798','media_url':'https://yamap.com/landmarks/52798','notes':'Current activity index includes a 2026-08-10 10.8 km Shoji entrance trail hike and several longer Aokigahara/Omuro routes; useful discovery source for western route ground truth.'},
 {'title':'Yamanashi 2025 Aokigahara three-course official experience flyer','group':'official map/document','tags':'Motosu; Shoji; Saiko; route concepts; current public programme','source_page':'https://www.pref.yamanashi.jp/documents/122515/1129chirashii.pdf','media_url':'https://www.pref.yamanashi.jp/documents/122515/1129chirashii.pdf','notes':'Official itinerary evidence for Motosu forest walk, Shoji/Kamahata forest walk and Saiko/Sankodai/Fugaku course.'},
 {'title':'Yamanashi Aokigahara official current tourism page (2026)','group':'official map/document','tags':'public trails; visitor access; cave corridor; Koyodai','source_page':'https://www.yamanashi-kankou.jp/aokigaharajukai/','media_url':'https://www.yamanashi-kankou.jp/aokigaharajukai/','notes':'Current official visitor context. Use for public-route/infrastructure validation and conservation constraints.'},
 {'title':'Shoji entrance trailhead in wet summer forest','group':'web extension','tags':'Shoji entrance; trailhead; wet season; signage; forest edge','source_page':'https://minkara.carview.co.jp/userid/803451/blog/27075701/','media_url':'https://cdn.snsimg.carview.co.jp/minkara/mybbs/000/002/549/742/2549742/p1.jpg','notes':'Secondary photographic ground truth. Shows Shoji entrance trailhead sign at 983 m and wet deciduous/conifer edge conditions.'},
 {'title':'Motosu-to-Tokai Nature Trail Aokigahara flat route image (2026)','group':'web extension','tags':'Motosu; Tokai Nature Trail; current; forest road/path','source_page':'https://note.com/grey/n/n3af1a7673ab7','media_url':'https://assets.st-note.com/img/1753792854-uFJqJZjRIMDVyXPvd3Koi5Bt.jpg','notes':'Current secondary route reference; use only after source-page validation. Added to strengthen western route appearance coverage.'},
 {'title':'Aokigahara current route junction sign — Ice Cave / Wind Cave / Lake Shoji','group':'web extension','tags':'trail junction; signage; Tokai Nature Trail; route continuity','source_page':'https://discover.hubpages.com/travel/What-is-Japans-Suicide-Forest-Really-Like','media_url':'https://images.saymedia-content.com/.image/t_share/MTc0NDY3NzY5NzM4MjA4NjE2/what-is-japans-suicide-forest-really-like.jpg','notes':'Secondary photo showing a bilingual junction sign linking Ice Cave, Wind Cave and Lake Shoji; useful for signage/material reference, not route survey.'},
]
existing={(r['title'],r['source_page']) for r in rows}
for a in new_assets:
    if (a['title'],a['source_page']) not in existing:
        rows.append(a)
with manifest.open('w',newline='',encoding='utf-8-sig') as f:
    fields=['title','group','tags','source_page','media_url','notes']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

# Update blueprint JSON with this pass.
bp_path=OUT/'Aokigahara_Reconstruction_Blueprint.json'
bp=json.loads(bp_path.read_text(encoding='utf-8'))
bp['version']='2026-09-09 expansion 3 — 250 m evidence grid'
bp['coverage_grid']={
    'cell_size_m':250,'generation_crs':'EPSG:6676','geometry_export_crs':'EPSG:4326','cell_count':len(features),
    'files':['Aokigahara_250m_coverage_grid.geojson','Aokigahara_250m_coverage_grid.csv'],
    'overall_evidence_counts':counts,'priority_counts':priority_counts,
    'warning':'Evidence-density grid only. It is not the Aokigahara forest/lava/protection boundary.'
}
bp['vegetation_gis_layers']=veg_sheets
bp['route_georegistration']={
    'primary_schematic':'https://www.pref.yamanashi.jp/documents/97765/guidelineryakuzu.pdf',
    'controls_file':'Aokigahara_georegistration_control_points.csv',
    'route_evidence':route_evidence,
    'method':'Use stable POIs and road/lake geometry as controls, fit the schematic to the project CRS, report residuals, and replace schematic segments with surveyed/GSI/GPX geometry wherever available.'
}
bp['current_coverage_findings']=[
    'Narusawa sheet 533815 and Fuji sheet 533805 provide official 1:25,000 existing-vegetation polygon sources over much of the central/eastern AOI; their metadata lists JPEG and Shp.',
    'The two identified sheets begin at approximately 138.6219 E, so the western Motosu/Shoji side still needs the adjoining vegetation sheet(s), with Shoji mesh 533814 the first retrieval target.',
    'Current YAMAP evidence strongly improves the public Route 139 cave corridor and the Fugaku/Narusawa-to-Sankodai continuity, but it must not replace official route geometry.',
    'The central high-ground and western interior remain the largest route-continuity and metre-scale visual gaps.'
]
bp_path.write_text(json.dumps(bp,ensure_ascii=False,indent=2),encoding='utf-8')

# Standalone interactive coverage map. Leaflet and base tiles require an internet connection; all grid/point geometry is embedded.
points_js=json.dumps([{k:p[k] for k in ('name','lat','lon','type','confidence','coordinate_basis','source_url')} for p in control_points],ensure_ascii=False)
routes_js=json.dumps([{'id':r['id'],'name':r['name'],'confidence':r['confidence'],'basis':r['basis'],'source_url':r['source_url'],'latlngs':[[lat,lon] for lon,lat in r['points']]} for r in route_evidence],ensure_ascii=False)
grid_js=json.dumps(geojson,ensure_ascii=False,separators=(',',':'))
map_html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aokigahara 250 m evidence coverage map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIINfQ3ynsOWo1MZQ8mMZrL93J6mvoMZp7A=" crossorigin=""/>
<style>html,body,#map{{height:100%;margin:0}}body{{font-family:system-ui,sans-serif}}.legend{{background:white;padding:10px 12px;line-height:1.35;box-shadow:0 1px 8px #5558;max-width:300px}}.sw{{display:inline-block;width:12px;height:12px;margin-right:6px}}.note{{font-size:12px;color:#444;margin-top:6px}}</style></head><body><div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script><script>
const grid={grid_js}; const pts={points_js}; const routes={routes_js};
const m=L.map('map').setView([35.48,138.65],12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}}).addTo(m);
function col(v){{return v==='High'?'#2e8b57':v==='Medium'?'#d6a42a':'#b94747'}}
const gl=L.geoJSON(grid,{{style:f=>({{color:col(f.properties.overall_reconstruction_evidence),weight:.45,fillColor:col(f.properties.overall_reconstruction_evidence),fillOpacity:.13}}),onEachFeature:(f,l)=>l.bindPopup(`<b>${{f.properties.grid_id}}</b><br>Evidence: ${{f.properties.overall_reconstruction_evidence}}<br>Research priority: ${{f.properties.research_priority}}<br>Nearest anchor: ${{f.properties.nearest_anchor}} (${{f.properties.nearest_anchor_m}} m)<br>Route evidence: ${{f.properties.route_evidence_confidence}}<br>${{f.properties.vegetation_gis_status}}<br><small>This cell is evidence coverage, not an Aokigahara boundary.</small>`)}}).addTo(m);
pts.forEach(p=>L.circleMarker([p.lat,p.lon],{{radius:5,weight:1,fillOpacity:.9}}).bindPopup(`<b>${{p.name}}</b><br>${{p.type}} · ${{p.confidence}}<br><small>${{p.coordinate_basis}}</small>`).addTo(m));
routes.forEach(r=>L.polyline(r.latlngs,{{weight:3,dashArray:'6 5',opacity:.7}}).bindPopup(`<b>${{r.name}}</b><br>Evidence corridor only · ${{r.confidence}}<br><small>${{r.basis}}</small>`).addTo(m));
L.control.scale({{metric:true,imperial:false}}).addTo(m);
const leg=L.control({{position:'bottomright'}}); leg.onAdd=()=>{{const d=L.DomUtil.create('div','legend');d.innerHTML='<b>250 m reconstruction-evidence grid</b><br><span class="sw" style="background:#2e8b57"></span>High evidence<br><span class="sw" style="background:#d6a42a"></span>Medium<br><span class="sw" style="background:#b94747"></span>Low<div class="note">Dashed lines are simplified evidence corridors, not surveyed routes. Grid covers a broad research AOI and does not define Aokigahara.</div>';return d}};leg.addTo(m);
</script></body></html>'''
(OUT/'Aokigahara_250m_Coverage_Map.html').write_text(map_html,encoding='utf-8')

# Update main dossier with a new expansion section before </main>. Remove prior expansion-3 block if rerun.
html_path=OUT/'Aokigahara_Reconstruction_Research_Dossier.html'
doc=html_path.read_text(encoding='utf-8')
start='<!-- EXPANSION3_START -->'; end='<!-- EXPANSION3_END -->'
if start in doc and end in doc:
    doc=doc.split(start)[0]+doc.split(end,1)[1]
manifest_count=len(rows)
# Update headline stats in a robust simple way.
import re
doc=re.sub(r'<div class="stats">.*?</div></header>',f'<div class="stats"><div class="stat"><b>{manifest_count}</b>indexed visual/map/GIS assets</div><div class="stat"><b>{len(features)}</b>250 m evidence cells</div><div class="stat"><b>2</b>official 1:25k vegetation GIS sheets located</div><div class="stat"><b>{len(control_points)}</b>georegistration controls</div></div></header>',doc,count=1,flags=re.S)
section=f'''{start}
<section id="coverage-grid"><h2>Expansion 3 — 250 m evidence grid & route georegistration</h2>
<p class="section-note">This pass converts the research into measurable spatial coverage. The grid is deliberately an <b>evidence-density grid</b>, not a proposed Aokigahara boundary.</p>
<div class="callout"><strong>Major improvement:</strong> official Ministry of the Environment 1:25,000 existing-vegetation GIS datasets have now been located for <b>Narusawa (533815)</b> and <b>Fuji (533805)</b>. Both advertise JPEG and Shp formats and originate from 2004–05 survey work. Normalised numeric extents show that they cover much of the central/eastern reconstruction AOI, while the western Motosu/Shōji side still needs the adjoining vegetation sheet(s).</div>
<div class="workflow">
<div class="step"><b>{len(features)} × 250 m cells</b><p>Generated in EPSG:6676 and exported as WGS84 GeoJSON/CSV. High/medium/low labels measure <i>research evidence density</i>, not physical certainty or boundary membership.</p></div>
<div class="step"><b>{counts['High']} high-evidence cells</b><p>Cells near known route/landmark controls and within an identified vegetation-GIS sheet. These are the best places to start camera matching.</p></div>
<div class="step"><b>{counts['Low']} low-evidence cells</b><p>These expose the genuine blind spots. P1 cells inside the research focus should drive the next image/video/GPX hunt.</p></div>
<div class="step"><b>Western vegetation gap</b><p>The two located sheets begin at about 138.6219°E. Retrieve the adjoining Shōji mesh (533814 is the first target) before assigning western vegetation polygons.</p></div>
</div>
<h3>Current route evidence</h3>
<p>Yamanashi's 2026 schematic explicitly distinguishes usable routes, former transport roads/forest roads and protected lava caves around Mt Omuro and Lake Sai. It is a primary official topology source, but it is schematic rather than survey-grade. The correct workflow is to georegister it to stable controls, report the residual error, and replace individual segments with GSI or public GPX geometry where available.</p>
<div class="workflow">
<div class="step"><b>Fugaku ↔ Narusawa</b><p>A current YAMAP model course reports 2.5 km, 1:02 and 58 m of ascent/descent, substantially strengthening route-continuity evidence along the best-documented public corridor.</p></div>
<div class="step"><b>Cave corridor → Sankodai</b><p>A 2026 YAMAP activity records 11.8 km and orders Fugaku Wind Cave → Narusawa Ice Cave → Koyodai → Sankodai before continuing to Ashiwadayama.</p></div>
<div class="step"><b>Shōji entrance</b><p>Current YAMAP activity listings include a 10.8 km Shōji entrance trail hike dated 10 August 2026 plus longer routes through Aokigahara/Omuro. This is now a priority discovery source for the western/central continuity gap.</p></div>
</div>
<h3>Georegistration controls</h3><div style="overflow:auto"><table style="width:100%;border-collapse:collapse"><tr><th style="text-align:left;padding:8px;border-bottom:1px solid var(--line)">Control</th><th style="text-align:left;padding:8px;border-bottom:1px solid var(--line)">WGS84</th><th style="text-align:left;padding:8px;border-bottom:1px solid var(--line)">Confidence / role</th></tr>'''+''.join(f'<tr><td style="padding:8px;border-bottom:1px solid var(--line)">{html.escape(p["name"])}</td><td style="padding:8px;border-bottom:1px solid var(--line)">{p["lat"]:.6f}, {p["lon"]:.6f}</td><td style="padding:8px;border-bottom:1px solid var(--line)">{html.escape(p["confidence"]+" · "+p["type"])} — validate exact point against GSI before final lock</td></tr>' for p in control_points)+f'''</table></div>
<h3>Files produced in this pass</h3><div class="refs">
<a href="Aokigahara_250m_Coverage_Map.html"><b>Interactive 250 m coverage map</b><br>Embedded grid and controls over an online OSM basemap.</a>
<a href="Aokigahara_250m_coverage_grid.geojson"><b>GeoJSON grid</b><br>{len(features)} cells, generated metrically in EPSG:6676 and serialized in WGS84.</a>
<a href="Aokigahara_250m_coverage_grid.csv"><b>CSV coverage table</b><br>Per-cell evidence, nearest anchor/route, vegetation-sheet status and research priority.</a>
<a href="Aokigahara_georegistration_control_points.csv"><b>Control-point register</b><br>Coordinates, confidence, provenance notes and official geometry references.</a>
<a href="Aokigahara_coverage_methodology.json"><b>Coverage methodology</b><br>Machine-readable scoring assumptions, caveats, source layers and next actions.</a>
</div>
<h3>What this changes</h3><p>The project can now distinguish three different questions cell-by-cell: <b>do we have terrain/vegetation source coverage?</b>, <b>do we have route-continuous evidence?</b>, and <b>do we have visual ground truth close enough to validate a build?</b> That is much closer to a digital-twin research workflow than counting photographs.</p>
<p><b>Next hard step:</b> download and catalogue the actual GSI elevation mesh files and Ministry vegetation Shapefiles, then replace these evidence heuristics with direct per-cell data coverage and the real vegetation polygons. Until that happens, the 250 m map is a research-priority instrument, not a claim of metre-perfect reconstruction.</p></section>
{end}'''
doc=doc.replace('</main>',section+'\n</main>',1)
html_path.write_text(doc,encoding='utf-8')

print(json.dumps({
 'grid_cells':len(features),'confidence':counts,'priorities':priority_counts,'manifest_assets':len(rows),
 'outputs':[p.name for p in [OUT/'Aokigahara_Reconstruction_Research_Dossier.html',OUT/'Aokigahara_Reconstruction_Blueprint.json',OUT/'Aokigahara_visual_asset_manifest.csv',OUT/'Aokigahara_250m_Coverage_Map.html',OUT/'Aokigahara_250m_coverage_grid.geojson',OUT/'Aokigahara_250m_coverage_grid.csv',OUT/'Aokigahara_georegistration_control_points.csv',OUT/'Aokigahara_coverage_methodology.json']]
},indent=2))
