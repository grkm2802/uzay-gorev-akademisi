# Misyon Akademisi giriş animasyonu (Blender 5.1, arka planda çalışır, Cycles + OptiX)
#
# Önizleme kareleri:  blender -b -P intro_scene.py -- preview OUT_DIR 1 60 120
# Tam video (mp4):     blender -b -P intro_scene.py -- render OUT_MP4
#
# Yüz yok: profesör hep arkadan görünür. Videoda yazı yok; yazılar sitede eklenir.
import sys, math, random
import bpy
from mathutils import Vector

FPS = 24
SECONDS = 18
CUT = 312          # kare: parlama, laboratuvardan uzaya geçiş (13 sn)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = args[0] if args else 'preview'

# ---------- Sahneyi sıfırla ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FPS * SECONDS
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.engine = 'CYCLES'
scene.view_settings.view_transform = 'Standard'
scene.cycles.use_denoising = True

# GPU (OptiX); olmazsa CPU
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

# ---------- Palet (siteyle uyumlu) ----------
C = {
    'indigo': '#33367F', 'indigo_dark': '#1E2150', 'wall': '#3F4396', 'floor': '#222552',
    'card': '#F1F2FF', 'mustard': '#FFC83D', 'violet': '#7C5CFF', 'board': '#1B2145',
    'jacket': '#7A6038', 'trousers': '#23264F', 'hair': '#EDEDF5', 'skin': '#D8A67E',
    'wood': '#B5834F', 'cell': '#4A55D8', 'earth': '#2E9BC4', 'limb': '#7FD6E6',
}

def hex2rgb(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)

_mats = {}
def mat(name, color, rough=0.85, emit=0.0):
    key = (name, color, rough, emit)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hex2rgb(color)
    b.inputs['Roughness'].default_value = rough
    if emit > 0:
        b.inputs['Emission Color'].default_value = hex2rgb(color)
        b.inputs['Emission Strength'].default_value = emit
    _mats[key] = m
    return m

def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)
    return o

def box(name, loc, size, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    if parent:
        o.parent = parent
    return assign(o, m)

def cyl(name, loc, radius, depth, m, rot=(0, 0, 0), parent=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if parent:
        o.parent = parent
    return assign(o, m)

def sph(name, loc, radius, m, scale=(1, 1, 1), parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if parent:
        o.parent = parent
    bpy.ops.object.shade_smooth()
    return assign(o, m)

def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    return o

def key(o, prop, frame, value):
    setattr(o, prop, value)
    o.keyframe_insert(prop, frame=frame)

def f(sec):  # saniye -> kare
    return int(round(sec * FPS)) + 1

# ---------- Dünya (gökyüzü gradyanı; uzay sahnesinde arka plan) ----------
w = bpy.data.worlds.new('Gok')
w.use_nodes = True
scene.world = w
nt = w.node_tree
nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord')
sp = nt.nodes.new('ShaderNodeSeparateXYZ')
mr = nt.nodes.new('ShaderNodeMapRange')
mr.inputs['From Min'].default_value = -0.25
mr.inputs['From Max'].default_value = 0.55
cr = nt.nodes.new('ShaderNodeValToRGB')
cr.color_ramp.elements[0].color = hex2rgb('#2B2E86')
cr.color_ramp.elements[1].color = hex2rgb('#6A70E0')
bg = nt.nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.0
out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(tc.outputs['Generated'], sp.inputs['Vector'])
nt.links.new(sp.outputs['Z'], mr.inputs['Value'])
nt.links.new(mr.outputs['Result'], cr.inputs['Fac'])
nt.links.new(cr.outputs['Color'], bg.inputs['Color'])
nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

# ======================================================================
# KORİDOR + LABORATUVAR  (y ekseni boyunca; kapı y=0 düzleminde)
# ======================================================================
wall = mat('Duvar', C['wall'])
dark = mat('Koyu', C['indigo_dark'])
floor_m = mat('Zemin', C['floor'], 0.6)
card = mat('Acik', C['card'])
must = mat('Hardal', C['mustard'], 0.5)
wood = mat('Ahsap', C['wood'], 0.7)

# koridor (y -9 .. 0), oda (y 0 .. 11)
box('Zemin', (0, 1, -0.05), (9, 22, 0.1), floor_m)
box('Tavan', (0, 1, 3.2), (9, 22, 0.1), dark)
# koridor duvarları
box('KoridorSol', (-1.4, -4.5, 1.6), (0.1, 9, 3.2), wall)
box('KoridorSag', (1.4, -4.5, 1.6), (0.1, 9, 3.2), wall)
box('KoridorArka', (0, -9.05, 1.6), (2.9, 0.1, 3.2), wall)
# kapının olduğu duvar (y=0), ortada 1.0 x 2.1 boşluk
box('DuvarSol', (-2.75, 0, 1.6), (2.5, 0.2, 3.2), wall)      # x -4..-1.5 -> koridor genişliğine kadar
box('DuvarSag', (2.75, 0, 1.6), (2.5, 0.2, 3.2), wall)
box('DuvarSol2', (-0.95, 0, 1.6), (0.9, 0.2, 3.2), wall)     # kapı boşluğunun solu  (x -1.4 .. -0.5)
box('DuvarSag2', (0.95, 0, 1.6), (0.9, 0.2, 3.2), wall)
box('DuvarUst', (0, 0, 2.65), (1.0, 0.2, 1.1), wall)
# kapı kasası + kapı kanadı (menteşe x=-0.5)
frame_m = mat('Kasa', C['mustard'], 0.6)
box('KasaSol', (-0.52, 0, 1.05), (0.06, 0.24, 2.1), frame_m)
box('KasaSag', (0.52, 0, 1.05), (0.06, 0.24, 2.1), frame_m)
box('KasaUst', (0, 0, 2.13), (1.1, 0.24, 0.06), frame_m)
hinge = empty('Mentese', (-0.5, 0.0, 0))
door = box('Kapi', (0.5, 0, 1.05), (1.0, 0.06, 2.1), mat('Kapi', C['violet'], 0.5), parent=hinge)
door.location = (0.5, 0, 1.05)
key(hinge, 'rotation_euler', f(0), (0, 0, 0))
key(hinge, 'rotation_euler', f(1.2), (0, 0, 0))
key(hinge, 'rotation_euler', f(3.2), (0, 0, math.radians(108)))
# oda duvarları
box('OdaSol', (-4.0, 5.5, 1.6), (0.1, 11, 3.2), wall)
box('OdaSag', (4.0, 5.5, 1.6), (0.1, 11, 3.2), wall)
box('OdaArka', (0, 11.0, 1.6), (8.1, 0.1, 3.2), wall)

# karatahta (arka duvar) + tebeşir yörüngesi (çizilerek belirir)
box('Tahta', (0, 10.9, 1.6), (4.6, 0.04, 1.7), mat('Tahta', C['board'], 0.9))
box('TahtaCerceve', (0, 10.92, 1.6), (4.8, 0.02, 1.9), wood)
chalk = mat('Tebesir', C['mustard'], 0.9, emit=3.0)
bpy.ops.curve.primitive_bezier_circle_add(radius=1, location=(0.3, 10.86, 1.65), rotation=(math.radians(90), 0, 0))
orb = bpy.context.object
orb.name = 'Yorunge'
orb.scale = (1.5, 0.5, 1.0)
orb.rotation_euler = (math.radians(90), math.radians(12), 0)
orb.data.bevel_depth = 0.018
orb.data.use_fill_caps = True
orb.data.materials.append(chalk)
orb.data.bevel_factor_start = 0.0
for fr, v in ((f(2.5), 0.0), (f(8.0), 1.0)):
    orb.data.bevel_factor_end = v
    orb.data.keyframe_insert('bevel_factor_end', frame=fr)
sph('Gezegen', (0.3, 10.86, 1.65), 0.28, mat('GezegenT', C['earth'], 0.8, emit=0.6), scale=(1, 0.12, 1))
sph('Uydu', (1.7, 10.86, 1.78), 0.07, chalk, scale=(1, 0.2, 1))

# pencere (sol duvar) + gün batımı ışığı
win = box('Pencere', (-3.93, 5.5, 1.7), (0.02, 3.6, 1.5), mat('Pencere', '#FFAE5C', 0.4, emit=7.0))
box('PencereCerceve', (-3.95, 5.5, 1.7), (0.02, 3.8, 1.7), frame_m)
for yy in (4.3, 5.5, 6.7):
    box('Kayit', (-3.91, yy, 1.7), (0.03, 0.05, 1.5), frame_m)

# raf ve roket maketleri (sağ duvar)
box('Raf', (3.7, 6.5, 1.5), (0.5, 3.0, 0.05), wood)
for i, yy in enumerate((5.4, 6.1, 6.9, 7.6)):
    h = 0.45 + 0.1 * (i % 2)
    cyl('Roket%d' % i, (3.7, yy, 1.55 + h / 2), 0.07, h, card, verts=20)
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.16, location=(3.7, yy, 1.55 + h + 0.08), vertices=20)
    assign(bpy.context.object, must)

# masa + uydu maketi
box('Masa', (2.6, 5.2, 0.72), (1.7, 0.9, 0.06), wood)
for sx in (-0.8, 0.8):
    for sy in (-0.4, 0.4):
        box('Ayak', (2.6 + sx, 5.2 + sy, 0.36), (0.06, 0.06, 0.72), dark)
cyl('MaketStand', (2.6, 5.2, 0.79), 0.05, 0.08, dark, verts=16)
model = empty('UyduMaketi', (2.6, 5.2, 0.9))
box('MaketGovde', (0, 0, 0), (0.36, 0.12, 0.12), card, parent=model)
cell_m = mat('Hucre', C['cell'], 0.35)
box('MaketPanelL', (-0.32, 0, 0), (0.26, 0.012, 0.10), cell_m, parent=model)
box('MaketPanelR', (0.32, 0, 0), (0.26, 0.012, 0.10), cell_m, parent=model)
cyl('MaketAnten', (0, 0, 0.12), 0.004, 0.18, card, parent=model, verts=8)
sph('MaketAntenUc', (0, 0, 0.21), 0.012, must, parent=model, seg=12)
key(model, 'rotation_euler', f(0), (0, 0, 0))
key(model, 'rotation_euler', f(13), (0, 0, math.radians(120)))
# masa lambası
cyl('LambaGovde', (2.15, 5.5, 0.93), 0.015, 0.4, must, verts=8)
sph('Lamba', (2.15, 5.5, 1.16), 0.07, mat('LambaI', '#FFB347', 0.3, emit=1.4))

# halı
box('Hali', (0.3, 8.6, 0.01), (2.8, 2.0, 0.02), mat('Hali', C['violet'], 0.95))

# ======================================================================
# PROFESÖR (arkadan, yüzsüz)
# ======================================================================
prof = empty('Profesor', (0.8, 9.2, 0))
jacket = mat('Ceket', C['jacket'], 0.95)
trous = mat('Pantolon', C['trousers'], 0.9)
skin = mat('Ten', C['skin'], 0.7)
hair = mat('Sac', C['hair'], 0.95)
for sx in (-0.11, 0.11):
    cyl('Bacak', (sx, 0, 0.42), 0.075, 0.84, trous, parent=prof, verts=16)
    box('Ayakkabi', (sx, 0.05, 0.04), (0.14, 0.26, 0.08), dark, parent=prof)
box('Govde', (0, 0, 1.12), (0.46, 0.26, 0.62), jacket, parent=prof)
cyl('Boyun', (0, 0, 1.47), 0.05, 0.1, skin, parent=prof, verts=12)
sph('Kafa', (0, 0, 1.64), 0.12, skin, scale=(1, 1, 1.08), parent=prof)
sph('SacArka', (0, -0.015, 1.68), 0.135, hair, scale=(1, 1, 0.98), parent=prof)   # arkadan beyaz saç
sph('KulakL', (-0.125, 0, 1.64), 0.03, skin, scale=(0.5, 1, 1), parent=prof, seg=12)
sph('KulakR', (0.125, 0, 1.64), 0.03, skin, scale=(0.5, 1, 1), parent=prof, seg=12)
# sol kol (aşağıda)
box('SolKol', (-0.28, 0, 1.15), (0.1, 0.12, 0.56), jacket, parent=prof)
sph('SolEl', (-0.28, 0, 0.84), 0.055, skin, parent=prof, seg=12)
# sağ kol: omuz ekseni etrafında döner (y ekseni = öne bakan eksen)
shoulder = empty('SagOmuz', (0.28, 0, 1.4), parent=prof)
arm = box('SagKol', (0, 0, -0.26), (0.1, 0.12, 0.56), jacket, parent=shoulder)
sph('SagEl', (0, 0, -0.58), 0.055, skin, parent=shoulder, seg=12)
key(shoulder, 'rotation_euler', f(0), (0, 0, 0))
key(shoulder, 'rotation_euler', f(5.8), (0, 0, 0))
key(shoulder, 'rotation_euler', f(6.7), (0, math.radians(-155), 0))   # kolu kaldırır
key(shoulder, 'rotation_euler', f(7.1), (0, math.radians(-140), 0))   # el sallar
key(shoulder, 'rotation_euler', f(7.5), (0, math.radians(-160), 0))
key(shoulder, 'rotation_euler', f(7.9), (0, math.radians(-145), 0))
key(shoulder, 'rotation_euler', f(9.0), (0, math.radians(-90), 0))    # masadaki uyduyu işaret eder
key(shoulder, 'rotation_euler', f(12.8), (0, math.radians(-90), 0))

# ======================================================================
# IŞIKLAR (laboratuvar)
# ======================================================================
def area(name, loc, rot, energy, size, color='#FFFFFF'):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    L = bpy.context.object
    L.name = name
    L.data.energy = energy
    L.data.size = size
    L.data.color = hex2rgb(color)[:3]
    return L

area('KoridorIsik', (0, -4.0, 3.0), (0, 0, 0), 230, 2.5, '#DCE0FF')
area('OdaIsik1', (0, 3.0, 3.1), (0, 0, 0), 700, 3.0, '#FFF1D6')
area('OdaIsik2', (0, 8.0, 3.1), (0, 0, 0), 700, 3.0, '#FFF1D6')
area('PencereIsik', (-3.3, 5.5, 1.8), (0, math.radians(90), 0), 900, 3.2, '#FFA95A')
area('KapiIsik', (0, 0.4, 2.6), (math.radians(90), 0, 0), 120, 1.0, '#FFE2B0')

# ======================================================================
# KAMERA A (laboratuvar yürüyüşü)
# ======================================================================
bpy.ops.object.camera_add(location=(0, -5.5, 1.65))
camA = bpy.context.object
camA.name = 'KameraA'
camA.data.lens = 26
look = empty('Bakis', (0, 2, 1.5))
tr = camA.constraints.new('TRACK_TO')
tr.target = look
tr.track_axis = 'TRACK_NEGATIVE_Z'
tr.up_axis = 'UP_Y'

path = [  # (saniye, kamera konumu, bakış noktası)
    (0.0, (0, -5.6, 1.65), (0, 2.0, 1.55)),
    (1.2, (0, -4.9, 1.65), (0, 2.0, 1.55)),
    (3.6, (0, -1.6, 1.65), (0, 6.0, 1.55)),
    (5.4, (0, 2.0, 1.65), (0.6, 9.5, 1.6)),
    (7.4, (0.2, 4.2, 1.62), (0.8, 9.2, 1.65)),
    (9.2, (0.9, 4.5, 1.55), (1.9, 6.4, 1.1)),
    (11.0, (1.9, 4.3, 1.2), (2.6, 5.2, 0.9)),
    (13.0, (2.35, 4.75, 0.94), (2.6, 5.2, 0.9)),
]
for sec, cp, lp in path:
    key(camA, 'location', f(sec), cp)
    key(look, 'location', f(sec), lp)

# ======================================================================
# UZAY SAHNESİ (z = 2000'de), KAMERA B
# ======================================================================
Z0 = 2000.0
earth = sph('Dunya', (0, 70, Z0 - 112), 100, mat('DunyaM', '#0E4C8A', 0.8, emit=0.0), seg=96)
atm_m = bpy.data.materials.new('AtmosferM')
atm_m.use_nodes = True
_at = atm_m.node_tree
_at.nodes.clear()
_fr = _at.nodes.new('ShaderNodeFresnel')
_fr.inputs['IOR'].default_value = 1.6
_em = _at.nodes.new('ShaderNodeEmission')
_em.inputs['Color'].default_value = hex2rgb(C['limb'])
_em.inputs['Strength'].default_value = 1.5
_tp = _at.nodes.new('ShaderNodeBsdfTransparent')
_mx = _at.nodes.new('ShaderNodeMixShader')
_ou = _at.nodes.new('ShaderNodeOutputMaterial')
_at.links.new(_fr.outputs['Fac'], _mx.inputs['Fac'])
_at.links.new(_tp.outputs['BSDF'], _mx.inputs[1])
_at.links.new(_em.outputs['Emission'], _mx.inputs[2])
_at.links.new(_mx.outputs['Shader'], _ou.inputs['Surface'])
limb = sph('Atmosfer', (0, 70, Z0 - 112), 101.8, atm_m, seg=96)
sph('Ay', (9.5, 70, Z0 + 5.0), 1.4, mat('AyM', '#F4F3FF', 0.9, emit=3.0), seg=32)
random.seed(7)
star = mat('Yildiz', '#FFFFFF', 0.5, emit=6.0)
for i in range(120):
    a = random.uniform(-0.9, 0.9)
    e = random.uniform(0.0, 0.7)
    d = 220
    x = d * math.sin(a)
    z = Z0 + d * math.sin(e) * 0.5 + 8
    sph('Y%d' % i, (x, 120 + random.uniform(0, 30), z), random.uniform(0.07, 0.15), star, seg=6)

sat = empty('Uydu3B', (0, 0, Z0 + 0.4))
cell3 = bpy.data.materials.new('Hucre3')
cell3.use_nodes = True
_n = cell3.node_tree.nodes
_ck = _n.new('ShaderNodeTexChecker')
_ck.inputs['Scale'].default_value = 10
_ck.inputs['Color1'].default_value = hex2rgb('#4A55D8')
_ck.inputs['Color2'].default_value = hex2rgb('#6F7BFF')
_tc = _n.new('ShaderNodeTexCoord')
cell3.node_tree.links.new(_tc.outputs['Object'], _ck.inputs['Vector'])
cell3.node_tree.links.new(_ck.outputs['Color'], _n['Principled BSDF'].inputs['Base Color'])
_n['Principled BSDF'].inputs['Roughness'].default_value = 0.4
parts = {}
parts['body'] = box('SGovde', (0, 0, 0), (3.0, 1.0, 1.0), card, parent=sat)
parts['pl'] = box('SPanelL', (-2.4, 0, 0), (1.8, 0.06, 1.0), cell3, parent=sat)
parts['pr'] = box('SPanelR', (2.4, 0, 0), (1.8, 0.06, 1.0), cell3, parent=sat)
parts['band'] = box('SSerit', (0, -0.505, 0), (3.02, 0.01, 0.18), must, parent=sat)
parts['ant'] = cyl('SAnten', (0, 0, 1.0), 0.03, 1.5, card, parent=sat, verts=8)
parts['tip'] = sph('SAntenUc', (0, 0, 1.78), 0.09, must, parent=sat, seg=16)
parts['i1'] = box('SEns1', (-0.5, 0, 0.55), (0.5, 0.4, 0.12), must, parent=sat)
parts['i2'] = box('SEns2', (0.4, 0, 0.55), (0.5, 0.4, 0.12), must, parent=sat)
base_scale = {k: tuple(v.scale) for k, v in parts.items()}
# parça parça belirir (sitedeki şema ile aynı fikir)
t0 = CUT / FPS + 0.7
order = [('body', t0), ('band', t0 + 0.4), ('pl', t0 + 0.6), ('pr', t0 + 0.9), ('ant', t0 + 1.5), ('tip', t0 + 1.8), ('i1', t0 + 2.1), ('i2', t0 + 2.35)]
for name, sec in order:
    o = parts[name]
    s = base_scale[name]
    o.scale = tuple(0.0001 for _ in s)
    o.keyframe_insert('scale', frame=1)
    o.keyframe_insert('scale', frame=f(sec) - 1)
    o.scale = tuple(v * 1.18 for v in s)
    o.keyframe_insert('scale', frame=f(sec) + 6)
    o.scale = s
    o.keyframe_insert('scale', frame=f(sec) + 11)
key(sat, 'rotation_euler', f(CUT / FPS), (0, 0, math.radians(-8)))
key(sat, 'rotation_euler', f(SECONDS), (0, 0, math.radians(14)))
sun = bpy.data.lights.new('Gunes', 'SUN')
sun.energy = 3.5
so = bpy.data.objects.new('Gunes', sun)
scene.collection.objects.link(so)
so.location = (0, 0, Z0 + 10)
so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

bpy.ops.object.camera_add(location=(0.6, -13.5, Z0 + 1.4))
camB = bpy.context.object
camB.name = 'KameraB'
camB.data.lens = 40
lookB = empty('BakisB', (0, 0, Z0 - 0.5))
trb = camB.constraints.new('TRACK_TO')
trb.target = lookB
trb.track_axis = 'TRACK_NEGATIVE_Z'
trb.up_axis = 'UP_Y'
key(camB, 'location', f(CUT / FPS), (1.4, -14.5, Z0 + 1.6))
key(camB, 'location', f(SECONDS), (0.4, -12.2, Z0 + 1.2))

# ======================================================================
# PARLAMA GEÇİŞİ (iki kameraya bağlı beyaz düzlem, ortak malzeme)
# ======================================================================
fm = bpy.data.materials.new('Parlama')
fm.use_nodes = True
ft = fm.node_tree
ft.nodes.clear()
em = ft.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = hex2rgb('#F1F2FF')
em.inputs['Strength'].default_value = 1.0
tp = ft.nodes.new('ShaderNodeBsdfTransparent')
mx = ft.nodes.new('ShaderNodeMixShader')
fo = ft.nodes.new('ShaderNodeOutputMaterial')
ft.links.new(tp.outputs['BSDF'], mx.inputs[1])
ft.links.new(em.outputs['Emission'], mx.inputs[2])
ft.links.new(mx.outputs['Shader'], fo.inputs['Surface'])
fac = mx.inputs['Fac']
for fr, v in ((1, 0.0), (CUT - 14, 0.0), (CUT, 1.0), (CUT + 14, 0.0), (FPS * SECONDS, 0.0)):
    fac.default_value = v
    fac.keyframe_insert('default_value', frame=fr)
for cam in (camA, camB):
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    pl = bpy.context.object
    pl.name = 'Parlama_' + cam.name
    pl.parent = cam
    pl.location = (0, 0, -0.4)
    assign(pl, fm)

# kamera geçişi (zaman çizelgesi işaretleri)
m1 = scene.timeline_markers.new('A', frame=1)
m1.camera = camA
m2 = scene.timeline_markers.new('B', frame=CUT)
m2.camera = camB
scene.camera = camA

# ======================================================================
# ÇIKTI
# ======================================================================
if MODE == 'preview':
    out_dir = args[1]
    scene.cycles.samples = 12
    scene.render.resolution_percentage = 50
    for fr in [int(a) for a in args[2:]]:
        scene.frame_set(fr)
        scene.render.filepath = out_dir + '\\f%04d.png' % fr
        bpy.ops.render.render(write_still=True)
    print('PREVIEW_OK')
elif MODE == 'save':
    # Blender penceresinde açıp düzenlemek için .blend olarak kaydet; Render > Render Animation ile video çıkar
    scene.cycles.samples = 36
    scene.render.filepath = '//..\assets\intro_render'
    try:
        scene.render.image_settings.media_type = 'VIDEO'
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.ffmpeg.audio_codec = 'NONE'
    except Exception as e:
        print('video ayarı atlandı:', e)
    bpy.ops.wm.save_as_mainfile(filepath=args[1])
    print('SAVE_OK')
else:
    scene.cycles.samples = int(args[2]) if len(args) > 2 else 48
    scene.render.filepath = args[1]
    if len(args) > 3:   # ilerleme kaydı: her kare bitince bir satır
        _log = args[3]
        def _progress(sc, *a):
            with open(_log, 'a') as fh:
                fh.write(str(sc.frame_current) + chr(10))
        bpy.app.handlers.render_post.append(_progress)
    try:
        scene.render.image_settings.media_type = 'VIDEO'
    except Exception as e:
        print('media_type yok:', e)
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.audio_codec = 'NONE'
    bpy.ops.render.render(animation=True)
    print('RENDER_OK')
