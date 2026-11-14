# Misyon Akademisi giriş animasyonu, v2: daha gerçekçi (Blender 5.1, arka planda, Cycles + OptiX)
#
#   Önizleme:  blender -b -P intro_scene_v2.py -- preview ÇIKTI_KLASÖRÜ 1 100 200 ...
#   Kaydet:    blender -b -P intro_scene_v2.py -- save DOSYA.blend
#   Tam video: blender -b -P intro_scene_v2.py -- render ÇIKTI_YOLU ÖRNEK_SAYISI [ILERLEME.log]
#
# Yüz yok: profesör hep arkadan görünür. Videoda okunur yazı yok; yazılar sitede eklenir.
import sys, math, random
import bpy

FPS = 24
SECONDS = 20
CUT = 336            # kare: parlama ve laboratuvardan uzaya geçiş (14 sn)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = args[0] if args else 'preview'
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FPS * SECONDS
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.engine = 'CYCLES'
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 2
scene.cycles.sample_clamp_indirect = 10

try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.refresh_devices()
    for d in prefs.devices:
        d.use = (d.type == 'OPTIX')
    scene.cycles.device = 'GPU'
except Exception as e:
    print('GPU kullanılamadı, CPU:', e)
    scene.cycles.device = 'CPU'

# ======================================================================
# Yardımcılar
# ======================================================================
def srgb(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)

def f(sec):
    return int(round(sec * FPS)) + 1

def key(o, prop, frame, value):
    setattr(o, prop, value)
    o.keyframe_insert(prop, frame=frame)

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']

_cache = {}
def pbr(name, color, rough=0.6, metal=0.0, bump=0.0, bump_scale=200, emit=0.0, spec=0.5):
    k = (name, color, rough, metal, bump, emit)
    if k in _cache:
        return _cache[k]
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = srgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit > 0:
        b.inputs['Emission Color'].default_value = srgb(color)
        b.inputs['Emission Strength'].default_value = emit
    if bump > 0:
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = bump_scale
        n.inputs['Detail'].default_value = 6
        bm = nt.nodes.new('ShaderNodeBump')
        bm.inputs['Strength'].default_value = bump
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        nt.links.new(n.outputs['Fac'], bm.inputs['Height'])
        nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    _cache[k] = m
    return m

def wood_mat(name, dark='#5B3A1E', light='#B07A43', scale=3.0, rough=0.4, bands=14):
    m, nt, b = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 0.12, 1.0)
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.inputs['Scale'].default_value = bands
    wv.inputs['Distortion'].default_value = 6
    wv.inputs['Detail'].default_value = 3
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = srgb(dark)
    cr.color_ramp.elements[1].color = srgb(light)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    nt.links.new(wv.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    return m

def tweed_mat(name, c1, c2):
    m, nt, b = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 260
    n.inputs['Detail'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = srgb(c1)
    cr.color_ramp.elements[1].color = srgb(c2)
    bm = nt.nodes.new('ShaderNodeBump')
    bm.inputs['Strength'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    nt.links.new(n.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(n.outputs['Fac'], bm.inputs['Height'])
    nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.95
    return m

def planks_mat():
    m, nt, b = new_mat('Parke')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 5.0
    br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.4
    br.inputs['Row Height'].default_value = 0.22
    br.inputs['Color1'].default_value = srgb('#6B4423')
    br.inputs['Color2'].default_value = srgb('#8A5A31')
    br.inputs['Mortar'].default_value = srgb('#2A180B')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.28
    return m

def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)
    return o

def smooth(o, bevel=0.0, subsurf=0):
    if bevel > 0:
        md = o.modifiers.new('Bevel', 'BEVEL')
        md.width = bevel
        md.segments = 3
        md.limit_method = 'ANGLE'
    if subsurf:
        md = o.modifiers.new('Sub', 'SUBSURF')
        md.levels = subsurf
        md.render_levels = subsurf
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def box(name, loc, size, m, rot=(0, 0, 0), parent=None, bevel=0.0, sub=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    assign(o, m)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if parent:
        o.parent = parent
    if bevel > 0 or sub:
        smooth(o, bevel, sub)
    return o

def cyl(name, loc, radius, depth, m, rot=(0, 0, 0), parent=None, verts=24, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if parent:
        o.parent = parent
    assign(o, m)
    smooth(o, bevel, 0)
    return o

def sph(name, loc, radius, m, scale=(1, 1, 1), parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=seg, ring_count=max(8, seg // 2))
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if parent:
        o.parent = parent
    assign(o, m)
    bpy.ops.object.shade_smooth()
    return o

def empty(name, loc, parent=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    return o

def curve_line(name, pts, m, depth=0.006, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = depth
    cu.materials.append(m)
    o = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(o)
    return o

def area(name, loc, rot, energy, size, color='#FFFFFF', sy=None):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    L = bpy.context.object
    L.name = name
    L.data.energy = energy
    L.data.size = size
    if sy:
        L.data.shape = 'RECTANGLE'
        L.data.size_y = sy
    L.data.color = srgb(color)[:3]
    return L

# ======================================================================
# Dünya: gün batımı gökyüzü (laboratuvar) / uzay degradesi (kare 336'dan sonra)
# ======================================================================
w = bpy.data.worlds.new('Gok')
w.use_nodes = True
scene.world = w
nt = w.node_tree
nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING'):
    try:
        sky.sky_type = t
        break
    except Exception:
        continue
sky.sun_elevation = math.radians(7)
sky.sun_rotation = math.radians(-100)   # güneş sol pencerelerden girer
try:
    sky.sun_size = math.radians(1.2)
    sky.sun_intensity = 1.0
    sky.air_density = 1.2
    sky.dust_density = 1.6
except Exception:
    pass
tc = nt.nodes.new('ShaderNodeTexCoord')
sp = nt.nodes.new('ShaderNodeSeparateXYZ')
mr = nt.nodes.new('ShaderNodeMapRange')
mr.inputs['From Min'].default_value = -0.25
mr.inputs['From Max'].default_value = 0.55
cr = nt.nodes.new('ShaderNodeValToRGB')
cr.color_ramp.elements[0].color = srgb('#2B2E86')
cr.color_ramp.elements[1].color = srgb('#6A70E0')
mix = nt.nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
bg = nt.nodes.new('ShaderNodeBackground')
out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(tc.outputs['Generated'], sp.inputs['Vector'])
nt.links.new(sp.outputs['Z'], mr.inputs['Value'])
nt.links.new(mr.outputs['Result'], cr.inputs['Fac'])
nt.links.new(sky.outputs['Color'], mix.inputs['A'])
nt.links.new(cr.outputs['Color'], mix.inputs['B'])
nt.links.new(mix.outputs['Result'], bg.inputs['Color'])
nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
fac = mix.inputs['Factor']
fac.default_value = 0.0
fac.keyframe_insert('default_value', frame=1)
fac.keyframe_insert('default_value', frame=CUT - 1)
fac.default_value = 1.0
fac.keyframe_insert('default_value', frame=CUT)
bg.inputs['Strength'].default_value = 1.0

# ======================================================================
# Malzemeler
# ======================================================================
plaster = pbr('Siva', '#C9C6D6', 0.9, bump=0.05, bump_scale=60)
accent = pbr('AksanDuvar', '#34377F', 0.85, bump=0.04, bump_scale=60)
ceil_m = pbr('Tavan', '#D9D8E6', 0.95)
trim = pbr('Pervaz', '#ECEBF4', 0.5)
floor_m = planks_mat()
woodm = wood_mat('Ahsap', '#59361A', '#A8733D', bands=16)
woodd = wood_mat('AhsapKoyu', '#3A2210', '#6F4524', bands=22, rough=0.35)
mustard = pbr('Hardal', '#E8B230', 0.45)
indigo = pbr('Indigo', '#3A3F9A', 0.5)
metal = pbr('Metal', '#9AA0AE', 0.35, metal=1.0)
steel_d = pbr('KoyuMetal', '#3A3D48', 0.4, metal=1.0)
white = pbr('Beyaz', '#F1F2F8', 0.5)
black = pbr('Siyah', '#15161C', 0.5)
slate = pbr('Tahta', '#1E2630', 0.85, bump=0.15, bump_scale=120)
chalk = pbr('Tebesir', '#F4F1E6', 0.95, bump=0.3, bump_scale=400)
paper = pbr('Kagit', '#F4F1E8', 0.9)
green = pbr('Yaprak', '#2E7D4F', 0.6)
terra = pbr('Saksi', '#B4563A', 0.8)
glow_w = pbr('Isik', '#FFF3DD', 0.5, emit=18.0)
glow_s = pbr('EkranIsik', '#7FB6FF', 0.5, emit=3.0)
gold_foil = pbr('AltinFolyo', '#E0A93C', 0.38, metal=0.85, bump=0.12, bump_scale=14)
silver = pbr('Gumus', '#C8CCD8', 0.3, metal=1.0)

# ======================================================================
# Koridor ve oda kabuğu (gerçek kapı ve pencere boşlukları)
# ======================================================================
box('Zemin', (0, 1, -0.05), (9, 22, 0.1), floor_m)
box('Tavan', (0, 1, 3.25), (9, 22, 0.1), ceil_m)
# koridor
box('KoridorSol', (-1.4, -4.5, 1.6), (0.1, 9, 3.2), plaster)
box('KoridorSag', (1.4, -4.5, 1.6), (0.1, 9, 3.2), plaster)
box('KoridorArka', (0, -9.05, 1.6), (2.9, 0.1, 3.2), accent)
box('KoridorSuprgSol', (-1.34, -4.5, 0.06), (0.04, 9, 0.12), trim)
box('KoridorSuprgSag', (1.34, -4.5, 0.06), (0.04, 9, 0.12), trim)
# koridor ayrıntıları: çerçeveli resimler, bank, koşucu halı
for yy in (-3.0, -6.0):
    box('KorResimS', (-1.33, yy, 1.7), (0.03, 0.7, 0.9), woodd, bevel=0.004)
    box('KorResimSIc', (-1.31, yy, 1.7), (0.015, 0.6, 0.8), pbr('KR%d' % int(yy), '#B8C4E8', 0.7))
box('KorResimSag', (1.33, -4.5, 1.7), (0.03, 1.2, 0.8), woodd, bevel=0.004)
box('KorResimSagIc', (1.31, -4.5, 1.7), (0.015, 1.1, 0.7), pbr('KRs', '#E8B84A', 0.7))
box('KorBank', (1.1, -6.6, 0.25), (0.45, 1.3, 0.05), woodm, bevel=0.008)
for sy in (-0.55, 0.55):
    box('KorBankAyak', (1.1, -6.6 + sy, 0.12), (0.4, 0.05, 0.24), steel_d)
box('KorHali', (0, -4.5, 0.011), (1.0, 8.5, 0.022), pbr('KorHali', '#3A3F9A', 0.95, bump=0.4, bump_scale=300))
# kapı duvarı (y=0): 1.0 x 2.1 boşluk
box('DuvarSol', (-2.75, 0, 1.6), (2.5, 0.2, 3.2), plaster)
box('DuvarSag', (2.75, 0, 1.6), (2.5, 0.2, 3.2), plaster)
box('DuvarSol2', (-0.95, 0, 1.6), (0.9, 0.2, 3.2), plaster)
box('DuvarSag2', (0.95, 0, 1.6), (0.9, 0.2, 3.2), plaster)
box('DuvarUst', (0, 0, 2.65), (1.0, 0.2, 1.1), plaster)
for xx in (-0.52, 0.52):
    box('KasaD', (xx, 0, 1.05), (0.07, 0.26, 2.1), woodd, bevel=0.01)
box('KasaUst', (0, 0, 2.13), (1.14, 0.26, 0.07), woodd, bevel=0.01)
hinge = empty('Mentese', (-0.5, 0.0, 0))
door = box('Kapi', (0.5, 0, 1.05), (0.98, 0.05, 2.08), woodm, parent=hinge, bevel=0.006)
door.location = (0.49, 0, 1.04)
cyl('KapiKolu', (0.9, -0.05, 1.0), 0.018, 0.12, metal, rot=(math.radians(90), 0, 0), parent=hinge, verts=16)
cyl('KapiKolu2', (0.9, 0.05, 1.0), 0.018, 0.12, metal, rot=(math.radians(90), 0, 0), parent=hinge, verts=16)
key(hinge, 'rotation_euler', f(0), (0, 0, 0))
key(hinge, 'rotation_euler', f(1.5), (0, 0, 0))
key(hinge, 'rotation_euler', f(3.5), (0, 0, math.radians(105)))

# oda
LW = [(0, 2.2), (4.4, 6.6), (8.8, 11.0)]       # sol duvarın dolu kısımları (y aralıkları)
for i, (a, b) in enumerate(LW):
    box('OdaSolDuvar%d' % i, (-4.0, (a + b) / 2, 1.6), (0.2, b - a, 3.2), plaster)
for i, (a, b) in enumerate(((2.2, 4.4), (6.6, 8.8))):
    box('PencereAlt%d' % i, (-4.0, (a + b) / 2, 0.45), (0.2, b - a, 0.9), plaster)
    box('PencereUst%d' % i, (-4.0, (a + b) / 2, 2.85), (0.2, b - a, 0.7), plaster)
    box('Denizlik%d' % i, (-3.9, (a + b) / 2, 0.92), (0.3, b - a + 0.1, 0.05), woodm, bevel=0.01)
    for yy in (a, b, (a + b) / 2):
        box('PencereCita%d' % i, (-3.95, yy, 1.7), (0.05, 0.06, 1.6), white)
    box('PencereOrta%d' % i, (-3.95, (a + b) / 2, 1.7), (0.05, b - a, 0.05), white)
box('OdaSag', (4.0, 5.5, 1.6), (0.2, 11, 3.2), plaster)
box('OdaArka', (0, 11.0, 1.6), (8.2, 0.2, 3.2), accent)
for xx in (-3.9, 3.9):
    box('SupurgeY', (xx, 5.5, 0.07), (0.04, 11, 0.14), trim)
box('SupurgeArka', (0, 10.9, 0.07), (8, 0.04, 0.14), trim)

# dışarısı: zemin, uzak rampa ve roket (pencereden görünür)
box('DisZemin', (-130, 5, -0.2), (250, 300, 0.2), pbr('Dis', '#4A5A3E', 0.95))
tower_m = pbr('Kule', '#B8BDC9', 0.5, metal=0.6)
for dy in (-1.4, 1.4):
    for dx in (-1.4, 1.4):
        pass
box('RampaKule', (-72, 11, 14), (2.0, 2.0, 28), tower_m)
cyl('UzakRoket', (-72, 7.5, 12), 1.4, 24, white, verts=24)
bpy.ops.mesh.primitive_cone_add(radius1=1.4, radius2=0.0, depth=5, location=(-72, 7.5, 26.5), vertices=24)
assign(bpy.context.object, white)
box('UzakBina', (-95, -20, 5), (30, 18, 10), pbr('UzakB', '#7C8090', 0.8))

# ======================================================================
# Tahta ve tebeşir (okunur yazı yok: karalamalar ve çizilen yörünge)
# ======================================================================
box('TahtaCerceve', (0, 10.88, 1.65), (4.9, 0.05, 1.95), woodd, bevel=0.01)
box('Tahta', (0, 10.86, 1.65), (4.7, 0.03, 1.75), slate)
box('TebesirRaf', (0, 10.78, 0.72), (4.8, 0.14, 0.04), woodd, bevel=0.005)
for i, xx in enumerate((-1.3, -0.9, 1.1)):
    cyl('Tebesir%d' % i, (xx, 10.75, 0.76), 0.007, 0.07, chalk, rot=(0, math.radians(90), 0), verts=8)
# karalamalar
for gx, gz in ((-1.9, 2.25), (-1.9, 1.95), (-1.9, 1.65), (1.9, 2.25), (1.9, 1.95), (1.9, 1.15), (-1.9, 1.2)):
    pts = []
    x = gx - 0.35
    for i in range(14):
        x += random.uniform(0.03, 0.07)
        pts.append((x, 10.84, gz + random.uniform(-0.04, 0.04) + 0.03 * math.sin(i * 1.7)))
    curve_line('Karalama', pts, chalk, depth=0.0045)
# yörünge elipsi (çizilerek belirir)
bpy.ops.curve.primitive_bezier_circle_add(radius=1, location=(0.1, 10.83, 1.65), rotation=(math.radians(90), 0, 0))
orb = bpy.context.object
orb.name = 'Yorunge'
orb.scale = (1.45, 0.5, 1.0)
orb.rotation_euler = (math.radians(90), math.radians(10), 0)
orb.data.bevel_depth = 0.008
orb.data.materials.append(chalk)
orb.data.bevel_factor_start = 0.0
for fr, v in ((f(3.4), 0.0), (f(9.0), 1.0)):
    orb.data.bevel_factor_end = v
    orb.data.keyframe_insert('bevel_factor_end', frame=fr)
sph('GezegenT', (0.1, 10.83, 1.65), 0.22, pbr('GezegenM', '#6FB7E8', 0.9, bump=0.2, bump_scale=60), scale=(1, 0.1, 1))
sph('UyduT', (1.45, 10.83, 1.78), 0.05, chalk, scale=(1, 0.2, 1), seg=12)

# ======================================================================
# Kitaplık, raf, saksı, globe, saat, tavan lambaları
# ======================================================================
book_cols = ['#8E3B2E', '#2F4F7F', '#C9A23A', '#3E6B4F', '#6C4A8E', '#B7B3A6', '#A34A63', '#2A2F45']
def bookshelf(x, y0, y1, depth=0.34, facing=-1):
    h = 2.5
    box('KitapKasaArka', (x - facing * depth / 2 + facing * 0.01, (y0 + y1) / 2, h / 2), (0.03, y1 - y0, h), woodd)
    box('KitapKasaSol', (x, y0, h / 2), (depth, 0.04, h), woodd)
    box('KitapKasaSag', (x, y1, h / 2), (depth, 0.04, h), woodd)
    for i in range(6):
        z = 0.05 + i * 0.5
        box('KitapRaf', (x, (y0 + y1) / 2, z), (depth, y1 - y0, 0.035), woodd)
        yy = y0 + 0.07
        while yy < y1 - 0.12:
            bw = random.uniform(0.025, 0.06)
            bh = random.uniform(0.26, 0.40)
            if random.random() < 0.08:
                yy += random.uniform(0.1, 0.25)
                continue
            col = random.choice(book_cols)
            tilt = random.uniform(-0.05, 0.05) if random.random() < 0.08 else 0
            box('Kitap', (x + random.uniform(-0.015, 0.015), yy + bw / 2, z + 0.02 + bh / 2),
                (depth * 0.82, bw, bh), pbr('K' + col, col, 0.6), rot=(tilt, 0, 0))
            yy += bw + 0.004
bookshelf(3.72, 0.9, 4.1, facing=1)
bookshelf(3.72, 8.5, 10.8, facing=1)
# roket maketli duvar rafı
box('Raf', (3.72, 6.4, 1.55), (0.3, 3.0, 0.04), woodm, bevel=0.005)
for i, yy in enumerate((5.4, 6.0, 6.6, 7.2, 7.7)):
    h = 0.38 + 0.08 * (i % 3)
    cyl('Roket%d' % i, (3.72, yy, 1.57 + h / 2), 0.05, h, white if i % 2 == 0 else silver, verts=20)
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.0, depth=0.14, location=(3.72, yy, 1.57 + h + 0.07), vertices=20)
    assign(bpy.context.object, mustard if i % 2 == 0 else terra)
    for ang in (0, 90, 180, 270):
        box('Kanat', (3.72 + 0.045 * math.cos(math.radians(ang)), yy + 0.045 * math.sin(math.radians(ang)), 1.6),
            (0.01 if ang % 180 == 0 else 0.07, 0.07 if ang % 180 == 0 else 0.01, 0.1), indigo)
# duvar saati
cyl('Saat', (3.88, 3.0, 2.55), 0.22, 0.04, white, rot=(0, math.radians(90), 0), verts=40)
cyl('SaatCerceve', (3.9, 3.0, 2.55), 0.24, 0.02, black, rot=(0, math.radians(90), 0), verts=40)
box('SaatYelkovan', (3.84, 3.0, 2.62), (0.01, 0.015, 0.14), black)
box('SaatAkrep', (3.84, 3.07, 2.55), (0.01, 0.11, 0.015), black)
# çerçeveli gezegen resmi
box('Cerceve', (-3.9, 10.2, 1.9), (0.04, 0.9, 1.2), woodd, bevel=0.005)
sph('ResimGez', (-3.87, 10.2, 1.9), 0.3, pbr('ResimG', '#C9783C', 0.8, bump=0.2, bump_scale=30), scale=(0.1, 1, 1))
# globe
box('GlobeTaban', (-3.0, 9.6, 0.05), (0.4, 0.4, 0.05), woodd, bevel=0.01)
cyl('GlobeDirek', (-3.0, 9.6, 0.5), 0.03, 0.9, woodd, verts=16)
earth_g = bpy.data.materials.new('GlobeM')
earth_g.use_nodes = True
_n = earth_g.node_tree.nodes
_noi = _n.new('ShaderNodeTexNoise'); _noi.inputs['Scale'].default_value = 2.2; _noi.inputs['Detail'].default_value = 5
_cr = _n.new('ShaderNodeValToRGB')
_cr.color_ramp.elements[0].position = 0.5
_cr.color_ramp.elements[0].color = srgb('#2C6FB0')
_cr.color_ramp.elements[1].position = 0.55
_cr.color_ramp.elements[1].color = srgb('#4E9B57')
_tc = _n.new('ShaderNodeTexCoord')
earth_g.node_tree.links.new(_tc.outputs['Object'], _noi.inputs['Vector'])
earth_g.node_tree.links.new(_noi.outputs['Fac'], _cr.inputs['Fac'])
earth_g.node_tree.links.new(_cr.outputs['Color'], _n['Principled BSDF'].inputs['Base Color'])
_n['Principled BSDF'].inputs['Roughness'].default_value = 0.4
sph('Globe', (-3.0, 9.6, 1.12), 0.28, earth_g)
# saksı
cyl('Saksi', (3.4, 10.5, 0.2), 0.2, 0.4, terra, verts=24, bevel=0.01)
for i in range(9):
    a = i * 40
    sph('Yaprak', (3.4 + 0.18 * math.cos(math.radians(a)), 10.5 + 0.18 * math.sin(math.radians(a)), 0.7 + 0.12 * (i % 3)),
        0.14, green, scale=(0.5, 0.15, 1.4), seg=10)
# tavan lambaları (sarkıt) + ışık panelleri
for yy in (2.5, 6.0, 9.2):
    cyl('Sarkit', (0, yy, 2.9), 0.006, 0.7, black, verts=6)
    cyl('Abajur', (0, yy, 2.55), 0.28, 0.12, mustard, verts=32, bevel=0.01)
    sph('Ampul', (0, yy, 2.5), 0.07, glow_w, seg=12)
area('TavanIsik1', (0, 2.5, 2.4), (0, 0, 0), 130, 0.7, '#FFE9C4')
area('TavanIsik2', (0, 6.0, 2.4), (0, 0, 0), 130, 0.7, '#FFE9C4')
area('TavanIsik3', (0, 9.2, 2.4), (0, 0, 0), 130, 0.7, '#FFE9C4')

# ======================================================================
# Çalışma masası (uydu maketi) + sandalye, dizüstü, kupa, kâğıtlar
# ======================================================================
box('Masa', (2.55, 5.2, 0.76), (1.7, 0.85, 0.05), woodm, bevel=0.008)
for sx in (-0.78, 0.78):
    for sy in (-0.36, 0.36):
        box('MasaAyak', (2.55 + sx, 5.2 + sy, 0.37), (0.06, 0.06, 0.74), woodd, bevel=0.004)
box('MasaCekmece', (2.55, 5.2, 0.66), (1.5, 0.7, 0.12), woodd)
# uydu maketi (altın folyo)
model = empty('UyduMaketi', (2.55, 5.2, 0.915))
cyl('MaketStand', (2.55, 5.2, 0.81), 0.05, 0.09, steel_d, verts=20)
box('MaketStandTaban', (2.55, 5.2, 0.775), (0.14, 0.14, 0.01), steel_d)
box('MaketGovde', (0, 0, 0), (0.30, 0.10, 0.10), gold_foil, parent=model, bevel=0.004)
cellm = bpy.data.materials.new('Hucre')
cellm.use_nodes = True
_cn = cellm.node_tree.nodes
_ck = _cn.new('ShaderNodeTexChecker'); _ck.inputs['Scale'].default_value = 28
_ck.inputs['Color1'].default_value = srgb('#1C2F7A'); _ck.inputs['Color2'].default_value = srgb('#2E47B0')
_tc2 = _cn.new('ShaderNodeTexCoord')
cellm.node_tree.links.new(_tc2.outputs['Object'], _ck.inputs['Vector'])
cellm.node_tree.links.new(_ck.outputs['Color'], _cn['Principled BSDF'].inputs['Base Color'])
_cn['Principled BSDF'].inputs['Roughness'].default_value = 0.25
_cn['Principled BSDF'].inputs['Metallic'].default_value = 0.6
box('MaketPanelL', (-0.27, 0, 0), (0.24, 0.008, 0.10), cellm, parent=model)
box('MaketPanelR', (0.27, 0, 0), (0.24, 0.008, 0.10), cellm, parent=model)
cyl('MaketAnten', (0, 0, 0.10), 0.003, 0.14, silver, parent=model, verts=8)
sph('MaketAntenUc', (0, 0, 0.17), 0.01, mustard, parent=model, seg=12)
key(model, 'rotation_euler', f(0), (0, 0, math.radians(-20)))
key(model, 'rotation_euler', f(14), (0, 0, math.radians(110)))
# dizüstü
box('LaptopTaban', (1.95, 5.4, 0.795), (0.34, 0.24, 0.016), steel_d, bevel=0.004)
laptop_scr = box('LaptopEkran', (1.95, 5.52, 0.915), (0.34, 0.012, 0.23), black, rot=(math.radians(-8), 0, 0), bevel=0.003)
box('LaptopIsik', (1.95, 5.508, 0.915), (0.31, 0.003, 0.20), glow_s, rot=(math.radians(-8), 0, 0))
# kupa, kâğıt, kalemlik
cyl('Kupa', (3.1, 5.0, 0.84), 0.04, 0.09, white, verts=24, bevel=0.003)
cyl('KupaYildiz', (3.1, 4.96, 0.84), 0.012, 0.002, mustard, rot=(math.radians(90), 0, 0), verts=6)
box('Kagit1', (2.2, 4.95, 0.787), (0.21, 0.30, 0.004), paper, rot=(0, 0, math.radians(8)))
box('Kagit2', (2.3, 4.9, 0.791), (0.21, 0.30, 0.004), paper, rot=(0, 0, math.radians(-12)))
cyl('Kalemlik', (3.2, 5.45, 0.84), 0.035, 0.09, indigo, verts=20)
for i in range(4):
    cyl('Kalem', (3.19 + 0.01 * i, 5.44 + 0.006 * i, 0.93), 0.004, 0.12, mustard if i % 2 else white, rot=(math.radians(10 * (i - 2)), 0, 0), verts=6)
# masa lambası
box('LambaTaban', (3.1, 5.6, 0.79), (0.1, 0.1, 0.02), steel_d)
cyl('LambaKol', (3.1, 5.6, 1.0), 0.008, 0.4, steel_d, verts=8)
cyl('LambaBas', (3.13, 5.55, 1.2), 0.07, 0.09, mustard, rot=(math.radians(60), 0, 0), verts=24)
area('MasaLambaIsik', (3.13, 5.55, 1.12), (math.radians(150), 0, 0), 38, 0.12, '#FFD9A0')
# sandalye
seat = box('Sandalye', (2.55, 4.15, 0.46), (0.46, 0.46, 0.06), mustard, bevel=0.015)
box('SandalyeSirt', (2.55, 3.95, 0.78), (0.44, 0.06, 0.5), mustard, bevel=0.015)
cyl('SandalyeDirek', (2.55, 4.15, 0.25), 0.03, 0.4, steel_d, verts=12)
for a in range(5):
    box('SandalyeAyak', (2.55 + 0.22 * math.cos(math.radians(a * 72)), 4.15 + 0.22 * math.sin(math.radians(a * 72)), 0.03),
        (0.28, 0.035, 0.03), steel_d, rot=(0, 0, math.radians(a * 72)))

# orta çalışma tezgâhı: büyük roket modeli
box('Tezgah', (-1.6, 6.8, 0.78), (2.2, 0.9, 0.06), woodm, bevel=0.008)
for sx in (-1.0, 1.0):
    for sy in (-0.38, 0.38):
        box('TezgahAyak', (-1.6 + sx, 6.8 + sy, 0.38), (0.07, 0.07, 0.76), steel_d)
cyl('TezgahRoket', (-1.6, 6.8, 1.15), 0.1, 0.7, white, rot=(0, math.radians(90), 0), verts=32)
bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0.0, depth=0.26, location=(-1.12, 6.8, 1.15), rotation=(0, math.radians(90), 0), vertices=32)
assign(bpy.context.object, mustard)
for a in (0, 90, 180, 270):
    box('TezgahKanat', (-2.0, 6.8 + 0.12 * math.cos(math.radians(a)), 1.15 + 0.12 * math.sin(math.radians(a))),
        (0.18, 0.012 if a % 180 == 0 else 0.1, 0.1 if a % 180 == 0 else 0.012), indigo)
box('TezgahStandL', (-1.8, 6.8, 0.89), (0.05, 0.14, 0.16), woodd)
box('TezgahStandR', (-1.4, 6.8, 0.89), (0.05, 0.14, 0.16), woodd)
box('TezgahKagit', (-1.0, 6.55, 0.815), (0.5, 0.35, 0.004), paper, rot=(0, 0, math.radians(15)))
# halı
box('Hali', (0.45, 8.7, 0.012), (3.2, 2.2, 0.024), pbr('Hali', '#4B3F8F', 0.95, bump=0.4, bump_scale=300))

# ======================================================================
# PROFESÖR (arkadan, yüzsüz; eklemli kollar)
# ======================================================================
prof = empty('Profesor', (0.8, 9.1, 0))
tweed = tweed_mat('Tvit', '#5A4630', '#8B6E4A')
trousers = pbr('Pantolon', '#2A2F4F', 0.85, bump=0.15, bump_scale=300)
skin = pbr('Ten', '#D9A77F', 0.55)
hair = pbr('Sac', '#EEEEF4', 0.9, bump=0.5, bump_scale=500)
shirt = pbr('Gomlek', '#DCE3F2', 0.7)
shoe = pbr('Ayakkabi', '#2A1D14', 0.35)
# bacaklar
for sx in (-0.1, 0.1):
    cyl('Bacak', (sx, 0, 0.43), 0.078, 0.82, trousers, parent=prof, verts=20)
    box('Ayakkabi', (sx, 0.04, 0.045), (0.12, 0.27, 0.09), shoe, parent=prof, bevel=0.025)
# gövde (ceket): yumuşatılmış kutular
torso = box('Govde', (0, 0, 1.13), (0.47, 0.26, 0.62), tweed, parent=prof, bevel=0.06)
box('CeketEtek', (0, 0, 0.84), (0.46, 0.265, 0.12), tweed, parent=prof, bevel=0.03)
box('OmuzSol', (-0.2, 0, 1.4), (0.18, 0.22, 0.08), tweed, parent=prof, bevel=0.03)
box('OmuzSag', (0.2, 0, 1.4), (0.18, 0.22, 0.08), tweed, parent=prof, bevel=0.03)
box('CeketYirtmac', (0, -0.132, 0.9), (0.012, 0.004, 0.2), black, parent=prof)
cyl('Yaka', (0, 0, 1.455), 0.075, 0.05, shirt, parent=prof, verts=20)
cyl('Boyun', (0, 0, 1.5), 0.052, 0.1, skin, parent=prof, verts=16)
# baş: arkadan beyaz saç, kulaklar
sph('Kafa', (0, 0, 1.64), 0.115, skin, scale=(1, 1.05, 1.12), parent=prof)
sph('SacArka', (0, -0.02, 1.665), 0.128, hair, scale=(1, 1.02, 1.0), parent=prof)
for i in range(16):
    a = random.uniform(0, 2 * math.pi)
    el = random.uniform(-0.3, 1.1)
    r = 0.13
    sph('SacTutam', (r * math.cos(el) * math.cos(a), -0.015 + r * math.cos(el) * math.sin(a) * 0.95, 1.665 + r * math.sin(el) * 0.95),
        random.uniform(0.02, 0.034), hair, scale=(1, 1, 0.9), parent=prof, seg=8)
for sx in (-0.118, 0.118):
    sph('Kulak', (sx, 0.0, 1.635), 0.028, skin, scale=(0.45, 1, 1.25), parent=prof, seg=12)
# kollar: omuz -> dirsek -> bilek, parmaklı el
def make_arm(side, shoulder_pos):
    sh = empty('Omuz' + side, shoulder_pos, parent=prof)
    cyl('UstKol' + side, (0, 0, -0.14), 0.058, 0.3, tweed, parent=sh, verts=18)
    sph('Dirsek' + side, (0, 0, -0.29), 0.055, tweed, parent=sh, seg=12)
    el = empty('DirsekE' + side, (0, 0, -0.29), parent=sh)
    cyl('AltKol' + side, (0, 0, -0.14), 0.05, 0.28, tweed, parent=el, verts=18)
    wr = empty('Bilek' + side, (0, 0, -0.29), parent=el)
    cyl('Manset' + side, (0, 0, -0.015), 0.043, 0.04, shirt, parent=wr, verts=16)
    box('Avuc' + side, (0, 0, -0.07), (0.075, 0.03, 0.085), skin, parent=wr, bevel=0.01)
    for i, fx in enumerate((-0.026, -0.009, 0.009, 0.026)):
        cyl('Parmak', (fx, 0, -0.145), 0.0085, 0.075, skin, parent=wr, verts=8)
    cyl('Bas', (0.045 if side == 'S' else -0.045, 0.004, -0.08), 0.009, 0.05, skin, parent=wr, rot=(0, math.radians(25 if side == 'S' else -25), 0), verts=8)
    return sh, el, wr
shS, elS, wrS = make_arm('S', (-0.3, 0, 1.4))    # sol kol (tahtaya yazar)
shR, elR, wrR = make_arm('R', (0.3, 0, 1.4))     # sağ kol (el sallar, işaret eder)
# tebeşir sol elde
cyl('TebesirEl', (0, -0.02, -0.17), 0.007, 0.06, chalk, parent=wrS, verts=8)

# kol animasyonları (derece)
def rot(o, sec, xyz):
    key(o, 'rotation_euler', f(sec), tuple(math.radians(v) for v in xyz))

# sol kol: 3.0 - 9.0 arası tahtaya yazar (öne ve yukarı kaldırır, küçük salınım)
rot(shS, 0, (0, 0, 0)); rot(elS, 0, (0, 0, 0))
rot(shS, 3.0, (0, 0, 0)); rot(elS, 3.0, (0, 0, 0))
rot(shS, 3.8, (80, 0, 8)); rot(elS, 3.8, (30, 0, 0))
for i, tt in enumerate([4.4, 5.0, 5.6, 6.2, 6.8, 7.4, 8.0, 8.6]):
    rot(shS, tt, (78 - 6 * (i % 2), 0, 8 + 8 * (i % 3 - 1))); rot(elS, tt, (35 - 10 * (i % 2), 0, 0))
rot(shS, 9.4, (78, 0, 8)); rot(elS, 9.4, (30, 0, 0))
rot(shS, 10.4, (0, 0, 0)); rot(elS, 10.4, (0, 0, 0))
# sağ kol: 8.0 - 9.6 el sallar; 10.2 - 14 masadaki uyduyu işaret eder
rot(shR, 0, (0, 0, 0)); rot(elR, 0, (0, 0, 0))
rot(shR, 7.9, (0, 0, 0)); rot(elR, 7.9, (0, 0, 0))
rot(shR, 8.7, (0, -150, 0)); rot(elR, 8.7, (-20, 0, 0))
for i, tt in enumerate([9.0, 9.3, 9.6, 9.9]):
    rot(shR, tt, (0, -150, 0)); rot(elR, tt, (-20, 0, 18 if i % 2 == 0 else -18))
rot(shR, 10.8, (0, -85, 0)); rot(elR, 10.8, (0, 0, 0))
rot(shR, 14.0, (0, -85, 0)); rot(elR, 14.0, (0, 0, 0))
# gövde hafif döner (masaya yönelir), nefes/yük aktarma
rot(prof, 0, (0, 0, 0))
prof.rotation_euler = (0, 0, 0)
for tt, zr in ((0, 0), (2, 1.5), (4, -1), (6, 1), (8, -1), (9.6, 0), (11.0, -28), (14, -30)):
    key(prof, 'rotation_euler', f(tt), (0, 0, math.radians(zr)))
for tt, xx in ((0, 0.8), (3.5, 0.8), (6.0, 0.86), (9.0, 0.82), (11.0, 0.9), (14, 0.9)):
    key(prof, 'location', f(tt), (xx, 9.1, 0))

# ======================================================================
# Işıklar
# ======================================================================
area('KoridorIsik', (0, -4.0, 3.1), (0, 0, 0), 190, 2.0, '#E4E8FF', sy=1.2)
area('KoridorIsik2', (0, -7.5, 3.1), (0, 0, 0), 140, 1.5, '#E4E8FF')
area('KapiIsik', (0, 0.6, 2.9), (0, 0, 0), 60, 1.0, '#FFE6BF')
area('PencereDolgu1', (-3.2, 3.3, 1.8), (0, math.radians(90), 0), 380, 2.2, '#FFB070', sy=1.6)
area('PencereDolgu2', (-3.2, 7.7, 1.8), (0, math.radians(90), 0), 380, 2.2, '#FFB070', sy=1.6)
area('OdaDolgu', (0, 5.5, 3.0), (0, 0, 0), 160, 5.0, '#CAD2FF', sy=7.0)
area('TahtaIsik', (0, 9.8, 3.0), (math.radians(-150), 0, 0), 180, 4.0, '#FFF4E0', sy=0.4)

# ======================================================================
# KAMERA A: yürüyüş, el sallama, masaya dönüş (elle sarsıntı + alan derinliği)
# ======================================================================
bpy.ops.object.camera_add(location=(0, -6.8, 1.62))
camA = bpy.context.object
camA.name = 'KameraA'
camA.data.lens = 28
look = empty('Bakis', (0, 3, 1.5))
tr = camA.constraints.new('TRACK_TO')
tr.target = look
tr.track_axis = 'TRACK_NEGATIVE_Z'
tr.up_axis = 'UP_Y'
camA.data.dof.use_dof = True
camA.data.dof.focus_object = look
camA.data.dof.aperture_fstop = 2.8
camA.data.sensor_width = 36

WP = [  # (saniye, kamera konumu, bakış noktası)
    (0.0,  (0.0, -7.0, 1.62), (0.0, 3.0, 1.50)),
    (3.0,  (0.0, -3.9, 1.62), (0.0, 4.0, 1.50)),
    (5.0,  (0.0, -0.4, 1.62), (0.4, 8.0, 1.60)),
    (7.0,  (0.1, 2.4, 1.62), (0.8, 9.2, 1.70)),
    (9.0,  (0.3, 4.4, 1.60), (0.8, 9.2, 1.70)),
    (11.0, (0.9, 4.8, 1.50), (1.9, 7.0, 1.20)),
    (12.8, (1.8, 4.7, 1.20), (2.55, 5.2, 0.95)),
    (14.0, (2.05, 4.5, 1.06), (2.55, 5.2, 0.93)),
]
def v3(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
def cr_pt(p0, p1, p2, p3, u):
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * u + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * u * u +
                        (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * u ** 3) for i in range(3))
def sample(idx, t):
    n = len(WP)
    for i in range(n - 1):
        if WP[i][0] <= t <= WP[i + 1][0]:
            u = (t - WP[i][0]) / (WP[i + 1][0] - WP[i][0])
            if i == 0:
                u = u * u * (3 - 2 * u) * 0.5 + u * 0.5      # yumuşak başlangıç
            if i == n - 2:
                u = u * 0.6 + (u * u * (3 - 2 * u)) * 0.4    # yumuşak bitiş
            p0 = WP[max(i - 1, 0)][idx]; p1 = WP[i][idx]; p2 = WP[i + 1][idx]; p3 = WP[min(i + 2, n - 1)][idx]
            return cr_pt(p0, p1, p2, p3, u)
    return WP[-1][idx]
ph = [random.uniform(0, 6.28) for _ in range(6)]
last_pos = None
for fr in range(1, CUT):
    t = (fr - 1) / FPS
    tt = min(t, 14.0)
    p = list(sample(1, tt))
    lk = list(sample(2, tt))
    t1 = min(tt + 0.05, 14.0)
    p1 = sample(1, t1)
    speed = math.dist(p, p1) / 0.05
    walk = min(1.0, speed / 0.55)
    p[2] += 0.014 * math.sin(2 * math.pi * 1.9 * t) * walk
    p[0] += 0.009 * math.sin(2 * math.pi * 0.95 * t + ph[0]) * walk
    p[0] += 0.004 * math.sin(2 * math.pi * 0.37 * t + ph[1]) + 0.003 * math.sin(2 * math.pi * 0.83 * t + ph[2])
    p[2] += 0.003 * math.sin(2 * math.pi * 0.51 * t + ph[3])
    lk[0] += 0.02 * math.sin(2 * math.pi * 0.41 * t + ph[4])
    lk[2] += 0.015 * math.sin(2 * math.pi * 0.57 * t + ph[5])
    camA.location = p
    look.location = lk
    camA.keyframe_insert('location', frame=fr)
    look.keyframe_insert('location', frame=fr)
# alan derinliği: 11 sn sonrası makro (daha açık diyafram)
camA.data.dof.aperture_fstop = 2.8
camA.data.dof.keyframe_insert('aperture_fstop', frame=1)
camA.data.dof.keyframe_insert('aperture_fstop', frame=f(10.5))
camA.data.dof.aperture_fstop = 2.4
camA.data.dof.keyframe_insert('aperture_fstop', frame=f(13.2))
camA.data.keyframe_insert('lens', frame=1)
camA.data.lens = 35
camA.data.keyframe_insert('lens', frame=f(14.0))
camA.data.lens = 28
camA.data.keyframe_insert('lens', frame=1)

# ======================================================================
# UZAY SAHNESİ (z = 2000'de) + KAMERA B
# ======================================================================
Z0 = 2000.0
earth_m = bpy.data.materials.new('DunyaM')
earth_m.use_nodes = True
en = earth_m.node_tree.nodes
el_ = earth_m.node_tree.links
eb = en['Principled BSDF']
tc3 = en.new('ShaderNodeTexCoord')
mp3 = en.new('ShaderNodeMapping')
mp3.inputs['Scale'].default_value = (0.04, 0.04, 0.04)
n_land = en.new('ShaderNodeTexNoise'); n_land.inputs['Scale'].default_value = 2.4; n_land.inputs['Detail'].default_value = 8
cr_land = en.new('ShaderNodeValToRGB')
cr_land.color_ramp.elements[0].position = 0.52
cr_land.color_ramp.elements[0].color = srgb('#0B3C7A')
cr_land.color_ramp.elements[1].position = 0.56
cr_land.color_ramp.elements[1].color = srgb('#3E7D45')
n_cl = en.new('ShaderNodeTexNoise'); n_cl.inputs['Scale'].default_value = 5.5; n_cl.inputs['Detail'].default_value = 7
cr_cl = en.new('ShaderNodeValToRGB')
cr_cl.color_ramp.elements[0].position = 0.5
cr_cl.color_ramp.elements[0].color = (0, 0, 0, 1)
cr_cl.color_ramp.elements[1].position = 0.72
cr_cl.color_ramp.elements[1].color = (1, 1, 1, 1)
mixc = en.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
el_.new(tc3.outputs['Object'], mp3.inputs['Vector'])
el_.new(mp3.outputs['Vector'], n_land.inputs['Vector'])
el_.new(mp3.outputs['Vector'], n_cl.inputs['Vector'])
el_.new(n_land.outputs['Fac'], cr_land.inputs['Fac'])
el_.new(n_cl.outputs['Fac'], cr_cl.inputs['Fac'])
el_.new(cr_land.outputs['Color'], mixc.inputs['A'])
el_.new(srgb('#FFFFFF') and cr_cl.outputs['Color'], mixc.inputs['Factor'])
mixc.inputs['B'].default_value = (0.95, 0.97, 1.0, 1.0)
el_.new(mixc.outputs['Result'], eb.inputs['Base Color'])
eb.inputs['Roughness'].default_value = 0.7
sph('Dunya', (0, 70, Z0 - 112), 100, earth_m, seg=128)

atm_m = bpy.data.materials.new('AtmosferM')
atm_m.use_nodes = True
_at = atm_m.node_tree
_at.nodes.clear()
_fr = _at.nodes.new('ShaderNodeFresnel'); _fr.inputs['IOR'].default_value = 1.5
_em = _at.nodes.new('ShaderNodeEmission'); _em.inputs['Color'].default_value = srgb('#7FC8F0'); _em.inputs['Strength'].default_value = 1.4
_tp = _at.nodes.new('ShaderNodeBsdfTransparent')
_mx = _at.nodes.new('ShaderNodeMixShader')
_ou = _at.nodes.new('ShaderNodeOutputMaterial')
_at.links.new(_fr.outputs['Fac'], _mx.inputs['Factor'])
_at.links.new(_tp.outputs['BSDF'], _mx.inputs[1])
_at.links.new(_em.outputs['Emission'], _mx.inputs[2])
_at.links.new(_mx.outputs['Shader'], _ou.inputs['Surface'])
sph('Atmosfer', (0, 70, Z0 - 112), 101.8, atm_m, seg=128)
sph('Ay', (9.5, 70, Z0 + 5.0), 1.4, pbr('AyM', '#F4F3FF', 0.9, emit=2.6, bump=0.2, bump_scale=20), seg=48)
random.seed(7)
starm = pbr('Yildiz', '#FFFFFF', 0.5, emit=8.0)
for i in range(170):
    a = random.uniform(-0.95, 0.95)
    e = random.uniform(-0.05, 0.75)
    d = 230
    sph('Y%d' % i, (d * math.sin(a), 130 + random.uniform(0, 30), Z0 + d * math.sin(e) * 0.5 + 8),
        random.uniform(0.07, 0.16), starm, seg=6)

sat = empty('Uydu3B', (0, 0, Z0 + 0.4))
parts = {}
cell3 = bpy.data.materials.new('Hucre3')
cell3.use_nodes = True
_cn3 = cell3.node_tree.nodes
_ck3 = _cn3.new('ShaderNodeTexChecker'); _ck3.inputs['Scale'].default_value = 12
_ck3.inputs['Color1'].default_value = srgb('#1E2F8A'); _ck3.inputs['Color2'].default_value = srgb('#3A55C8')
_tc4 = _cn3.new('ShaderNodeTexCoord')
cell3.node_tree.links.new(_tc4.outputs['Object'], _ck3.inputs['Vector'])
cell3.node_tree.links.new(_ck3.outputs['Color'], _cn3['Principled BSDF'].inputs['Base Color'])
_cn3['Principled BSDF'].inputs['Roughness'].default_value = 0.22
_cn3['Principled BSDF'].inputs['Metallic'].default_value = 0.7
parts['body'] = box('SGovde', (0, 0, 0), (3.0, 1.0, 1.0), gold_foil, parent=sat, bevel=0.03)
parts['band'] = box('SSerit', (0, -0.505, 0), (3.02, 0.01, 0.16), silver, parent=sat)
parts['pl'] = box('SPanelL', (-2.4, 0, 0), (1.8, 0.05, 1.0), cell3, parent=sat, bevel=0.01)
parts['pr'] = box('SPanelR', (2.4, 0, 0), (1.8, 0.05, 1.0), cell3, parent=sat, bevel=0.01)
parts['ant'] = cyl('SAnten', (0, 0, 1.0), 0.03, 1.5, silver, parent=sat, verts=12)
parts['tip'] = sph('SAntenUc', (0, 0, 1.78), 0.1, mustard, parent=sat, seg=20)
parts['i1'] = box('SEns1', (-0.55, 0, 0.55), (0.5, 0.4, 0.14), black, parent=sat, bevel=0.01)
parts['i2'] = box('SEns2', (0.45, 0, 0.55), (0.5, 0.4, 0.14), indigo, parent=sat, bevel=0.01)
base_scale = {k: tuple(v.scale) for k, v in parts.items()}
t0 = CUT / FPS + 0.8
order = [('body', t0), ('band', t0 + 0.5), ('pl', t0 + 0.8), ('pr', t0 + 1.1), ('ant', t0 + 1.8), ('tip', t0 + 2.1), ('i1', t0 + 2.4), ('i2', t0 + 2.7)]
for name, sec in order:
    o = parts[name]
    s0 = base_scale[name]
    o.scale = tuple(0.0001 for _ in s0)
    o.keyframe_insert('scale', frame=1)
    o.keyframe_insert('scale', frame=f(sec) - 1)
    o.scale = tuple(v * 1.18 for v in s0)
    o.keyframe_insert('scale', frame=f(sec) + 6)
    o.scale = s0
    o.keyframe_insert('scale', frame=f(sec) + 11)
key(sat, 'rotation_euler', f(CUT / FPS), (0, 0, math.radians(-8)))
key(sat, 'rotation_euler', f(SECONDS), (0, 0, math.radians(16)))
sun = bpy.data.lights.new('Gunes', 'SUN')
sun.energy = 3.2
so = bpy.data.objects.new('Gunes', sun)
scene.collection.objects.link(so)
so.location = (0, 0, Z0 + 10)
so.rotation_euler = (math.radians(55), math.radians(8), math.radians(-32))

fill = area('UzayDolgu', (3.5, -9.0, Z0 + 3.5), (math.radians(80), 0, math.radians(15)), 900, 6.0, '#FFF1DA')
fill2 = area('UzayDolgu2', (-4.0, -10.0, Z0 - 2.0), (math.radians(95), 0, math.radians(-20)), 500, 6.0, '#CFE0FF')
bpy.ops.object.camera_add(location=(0.6, -13.5, Z0 + 1.4))
camB = bpy.context.object
camB.name = 'KameraB'
camB.data.lens = 40
lookB = empty('BakisB', (0, 0, Z0 - 0.5))
trb = camB.constraints.new('TRACK_TO')
trb.target = lookB
trb.track_axis = 'TRACK_NEGATIVE_Z'
trb.up_axis = 'UP_Y'
key(camB, 'location', f(CUT / FPS), (1.6, -14.8, Z0 + 1.6))
key(camB, 'location', f(SECONDS), (0.3, -12.0, Z0 + 1.1))

# ======================================================================
# Parlama geçişi + kamera değişimi
# ======================================================================
fm = bpy.data.materials.new('Parlama')
fm.use_nodes = True
ft = fm.node_tree
ft.nodes.clear()
em = ft.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = srgb('#F1F2FF'); em.inputs['Strength'].default_value = 1.2
tp = ft.nodes.new('ShaderNodeBsdfTransparent')
mx = ft.nodes.new('ShaderNodeMixShader')
fo = ft.nodes.new('ShaderNodeOutputMaterial')
ft.links.new(tp.outputs['BSDF'], mx.inputs[1])
ft.links.new(em.outputs['Emission'], mx.inputs[2])
ft.links.new(mx.outputs['Shader'], fo.inputs['Surface'])
ffac = mx.inputs['Fac']
for fr, v in ((1, 0.0), (CUT - 16, 0.0), (CUT, 1.0), (CUT + 16, 0.0), (FPS * SECONDS, 0.0)):
    ffac.default_value = v
    ffac.keyframe_insert('default_value', frame=fr)
for cam in (camA, camB):
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    pl = bpy.context.object
    pl.name = 'Parlama_' + cam.name
    pl.parent = cam
    pl.location = (0, 0, -0.4)
    assign(pl, fm)
m1 = scene.timeline_markers.new('A', frame=1)
m1.camera = camA
m2 = scene.timeline_markers.new('B', frame=CUT)
m2.camera = camB
scene.camera = camA

# ======================================================================
# ÇIKTI
# ======================================================================
def video_settings():
    try:
        scene.render.image_settings.media_type = 'VIDEO'
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.ffmpeg.constant_rate_factor = 'HIGH'
        scene.render.ffmpeg.audio_codec = 'NONE'
    except Exception as e:
        print('video ayarı atlandı:', e)

if MODE == 'preview':
    out_dir = args[1]
    scene.cycles.samples = int(__import__('os').environ.get('PREV_SAMPLES', '24'))
    scene.render.resolution_percentage = int(__import__('os').environ.get('PREV_PCT', '50'))
    for fr in [int(a) for a in args[2:]]:
        scene.frame_set(fr)
        scene.render.filepath = out_dir + '\\f%04d.png' % fr
        bpy.ops.render.render(write_still=True)
    print('PREVIEW_OK')
elif MODE == 'save':
    scene.cycles.samples = 48
    scene.render.use_persistent_data = True
    scene.render.filepath = '//..\\assets\\intro_render'
    video_settings()
    bpy.ops.wm.save_as_mainfile(filepath=args[1])
    print('SAVE_OK')
else:
    scene.cycles.samples = int(args[2]) if len(args) > 2 else 48
    scene.render.use_persistent_data = True
    scene.render.filepath = args[1]
    if len(args) > 3:
        _log = args[3]
        def _progress(sc, *a):
            with open(_log, 'a') as fh:
                fh.write(str(sc.frame_current) + chr(10))
        bpy.app.handlers.render_post.append(_progress)
    video_settings()
    bpy.ops.render.render(animation=True)
    print('RENDER_OK')
