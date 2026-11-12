"""
Siaga Bencana - Generator Asset Environment (Blender 3.6+ / 4.x)

Membuat model low-poly flat-color untuk 5 kategori:
  Buildings, Vegetation, Infrastructure, Props, Signage
lalu (opsional) mengekspornya sebagai FBX langsung ke folder Unity:
  <UNITY_ROOT>/Assets/_Project/Art/Models/<Kategori>/<Nama>.fbx   (penamaan tim: SM_<Nama>_<NN>)

CARA PAKAI
  A) Di Blender: tab Scripting > Open file ini > ubah UNITY_ROOT > Run Script.
  B) Lewat terminal (tanpa membuka Blender):
       blender -b -P siaga_asset_generator.py -- --unity-root "C:\\path\\game-siaga-bencana"
       blender -b -P siaga_asset_generator.py -- --only Vegetation
       blender -b -P siaga_asset_generator.py -- --asset SM_House_01
       blender -b -P siaga_asset_generator.py -- --no-export      (hanya preview)

Konvensi: 1 unit = 1 meter, pivot di tengah-bawah model, sisi depan = -Y (Blender).
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

# =====================================================================
# KONFIGURASI (ubah sesuai komputer Anda)
# =====================================================================
UNITY_ROOT = r"C:\Users\patan\OneDrive\Dokumen\Folder Baru\OneDrive\Dokumen\Semester 5\project-game\game-siaga-bencana"
EXPORT_FBX = True
SAVE_BLEND = True
BLEND_FILE = os.path.join("SourceAssets", "Blender", "SM_Environment_Pack.blend")  # relatif ke UNITY_ROOT
MODELS_SUBPATH = os.path.join("Assets", "_Project", "Art", "Models")
COLLECTION_NAME = "SiagaAssets"
PREVIEW_GAP = 3.0  # jarak antar asset di viewport (tidak memengaruhi FBX)

# =====================================================================
# PALET WARNA (flat color) -> material "M_Env_<nama>"
# =====================================================================
PALETTE = {
    "Wall_Cream": (0.93, 0.86, 0.70),
    "Wall_Blue":  (0.45, 0.65, 0.82),
    "Wall_Grey":  (0.70, 0.70, 0.72),
    "Roof_Red":   (0.60, 0.18, 0.14),
    "Roof_Dark":  (0.28, 0.28, 0.33),
    "Door_Wood":  (0.40, 0.24, 0.12),
    "Glass":      (0.50, 0.78, 0.95),
    "Concrete":   (0.60, 0.60, 0.58),
    "Curb":       (0.42, 0.42, 0.42),
    "Asphalt":    (0.16, 0.16, 0.18),
    "Line_White": (0.95, 0.95, 0.95),
    "Grass":      (0.28, 0.62, 0.22),
    "Leaf_Dark":  (0.12, 0.42, 0.18),
    "Leaf_Light": (0.32, 0.68, 0.28),
    "Trunk":      (0.38, 0.24, 0.13),
    "Flower":     (0.85, 0.25, 0.40),
    "Rock":       (0.45, 0.45, 0.47),
    "Metal":      (0.33, 0.35, 0.38),
    "Trash_Green": (0.12, 0.42, 0.22),
    "Lamp":       (1.00, 0.95, 0.70),
    "Sign_Green": (0.03, 0.50, 0.22),
    "Sign_Blue":  (0.08, 0.32, 0.72),
    "Sign_Yellow": (1.00, 0.78, 0.08),
    "Sign_White": (0.97, 0.97, 0.97),
}


def get_material(name):
    full = "M_Env_" + name
    mat = bpy.data.materials.get(full)
    if mat:
        return mat
    mat = bpy.data.materials.new(full)
    mat.use_nodes = True
    r, g, b = PALETTE[name]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = (r, g, b, 1.0)
    return mat


# =====================================================================
# MESH BUILDER (bmesh) - semua bentuk dibuat dari primitif sederhana
# =====================================================================
class Builder:
    def __init__(self, name, seed=0):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []
        self.rng = random.Random(seed)

    # --- material ---
    def _paint(self, faces, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        idx = self.mats.index(mat)
        for f in faces:
            f.material_index = idx

    def _paint_verts(self, verts, mat):
        self._paint({f for v in verts for f in v.link_faces}, mat)

    # --- primitif ---
    def box(self, mat, size, base, rot_z=0.0):
        """Kotak. base = titik tengah-bawah (x, y, z)."""
        sx, sy, sz = size
        bx, by, bz = base
        m = (Matrix.Translation((bx, by, bz + sz / 2))
             @ Matrix.Rotation(rot_z, 4, "Z")
             @ Matrix.Diagonal((sx, sy, sz, 1.0)))
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._paint_verts(res["verts"], mat)

    def cyl(self, mat, base, r1, r2, h, segs=8, tilt=(0.0, 0.0)):
        """Silinder/kerucut (r2=0 -> kerucut). base = tengah-bawah. tilt = (rotX, rotY) rad."""
        rot = Euler((tilt[0], tilt[1], 0.0), "XYZ").to_matrix().to_4x4()
        m = Matrix.Translation(base) @ rot @ Matrix.Translation((0, 0, h / 2))
        res = bmesh.ops.create_cone(
            self.bm, cap_ends=True, cap_tris=False, segments=segs,
            radius1=r1, radius2=r2, depth=h, matrix=m)
        self._paint_verts(res["verts"], mat)

    def blob(self, mat, center, radius, scale=(1, 1, 1), subdiv=2, jitter=0.0):
        """Bola low-poly (icosphere) untuk daun, semak, batu."""
        m = (Matrix.Translation(center)
             @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)))
        res = bmesh.ops.create_icosphere(
            self.bm, subdivisions=subdiv, radius=radius, matrix=m)
        verts = res["verts"]
        if jitter:
            for v in verts:
                v.co += Vector((self.rng.uniform(-jitter, jitter),
                                self.rng.uniform(-jitter, jitter),
                                self.rng.uniform(-jitter, jitter)))
        self._paint_verts(verts, mat)

    def prism_xz(self, mat, pts, y0, y1):
        """Poligon di bidang XZ (daftar (x, z)) diekstrusi sepanjang Y dari y0 ke y1."""
        bm = self.bm
        front = [bm.verts.new((x, y0, z)) for x, z in pts]
        back = [bm.verts.new((x, y1, z)) for x, z in pts]
        faces = [bm.faces.new(front), bm.faces.new(back[::-1])]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((front[i], front[j], back[j], back[i])))
        self._paint(faces, mat)

    def arc_slab(self, mat, r_in, r_out, angle, segs, thick):
        """Pelat melengkung (untuk jalan tikungan). Pusat busur di (0,0)."""
        bm = self.bm
        ring = []
        for i in range(segs + 1):
            a = angle * i / segs
            c, s = math.cos(a), math.sin(a)
            ring.append((
                bm.verts.new((r_in * c, r_in * s, thick)),
                bm.verts.new((r_out * c, r_out * s, thick)),
                bm.verts.new((r_in * c, r_in * s, 0.0)),
                bm.verts.new((r_out * c, r_out * s, 0.0)),
            ))
        faces = []
        for i in range(segs):
            ti, to, bi, bo = ring[i]
            ti2, to2, bi2, bo2 = ring[i + 1]
            faces.append(bm.faces.new((ti, to, to2, ti2)))    # atas
            faces.append(bm.faces.new((bi, bi2, bo2, bo)))    # bawah
            faces.append(bm.faces.new((to, bo, bo2, to2)))    # sisi luar
            faces.append(bm.faces.new((ti, ti2, bi2, bi)))    # sisi dalam
        a = ring[0]
        faces.append(bm.faces.new((a[0], a[2], a[3], a[1])))
        b = ring[segs]
        faces.append(bm.faces.new((b[0], b[1], b[3], b[2])))
        self._paint(faces, mat)

    def snap_to_ground(self):
        """Geser model agar titik terendah tepat di z = 0."""
        min_z = min(v.co.z for v in self.bm.verts)
        for v in self.bm.verts:
            v.co.z -= min_z

    def build(self, collection):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in self.mats:
            mesh.materials.append(get_material(m))
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(obj)
        return obj


# =====================================================================
# 1. BANGUNAN  (SM_House / SM_Building / SM_School)
# =====================================================================
def gen_rumah(name, w, d, h, wall, roof, porch):
    """Rumah eksterior (rumah tetangga / latar). Interior rumah pemain tetap dari greybox."""
    b = Builder(name)
    b.box(wall, (w, d, h), (0, 0, 0))

    ov, rh = 0.5, 2.0  # overhang atap & tinggi atap
    b.prism_xz(roof, [(-w / 2 - ov, h), (w / 2 + ov, h), (0, h + rh)],
               -d / 2 - ov, d / 2 + ov)

    # pintu & jendela depan (sisi -Y)
    b.box("Door_Wood", (1.0, 0.12, 2.1), (0, -d / 2, 0))
    for sx in (-1, 1):
        b.box("Glass", (1.2, 0.12, 1.0), (sx * w / 3, -d / 2, 1.0))
    # jendela samping
    for sx in (-1, 1):
        for y in (-d / 4, d / 4):
            b.box("Glass", (0.12, 1.2, 1.0), (sx * w / 2, y, 1.0))

    if porch:  # teras dengan 2 tiang
        b.box("Concrete", (3.2, 1.6, 0.15), (0, -d / 2 - 0.8, 0))
        for sx in (-1, 1):
            b.box("Concrete", (0.15, 0.15, 2.6), (sx * 1.4, -d / 2 - 1.45, 0.15))
        b.box(roof, (3.6, 1.9, 0.12), (0, -d / 2 - 0.95, 2.75))
    else:      # hanya anak tangga
        b.box("Concrete", (1.8, 0.8, 0.15), (0, -d / 2 - 0.4, 0))
    return b


def gen_gedung():
    b = Builder("SM_Building_01")
    W, D, floors, fh = 12.0, 12.0, 4, 3.5
    H = floors * fh
    b.box("Wall_Grey", (W, D, H), (0, 0, 0))
    b.box("Concrete", (W + 0.4, D + 0.4, 0.4), (0, 0, H))  # atap datar

    xs = (-4.5, -1.5, 1.5, 4.5)
    for f in range(floors):
        z = f * fh + 1.0
        for i, x in enumerate(xs):
            b.box("Glass", (1.8, 0.12, 1.5), (x, D / 2, z))            # belakang
            b.box("Glass", (0.12, 1.8, 1.5), (W / 2, x, z))            # kanan
            b.box("Glass", (0.12, 1.8, 1.5), (-W / 2, x, z))           # kiri
            if f == 0 and i in (1, 2):
                continue                                               # area pintu
            b.box("Glass", (1.8, 0.12, 1.5), (x, -D / 2, z))           # depan
    b.box("Glass", (2.4, 0.12, 2.6), (0, -D / 2, 0))                   # pintu kaca
    b.box("Concrete", (3.6, 1.2, 0.15), (0, -D / 2 - 0.6, 2.9))        # kanopi
    return b


def gen_sekolah():
    b = Builder("SM_School_01")
    L, D, H = 24.0, 8.0, 4.0
    b.box("Wall_Cream", (L, D, H), (0, 0, 0))
    b.box("Roof_Red", (L + 0.2, D + 0.2, 0.4), (0, 0, 3.6))            # list merah atas
    b.box("Concrete", (L + 0.6, D + 0.6, 0.3), (0, 0, H))              # atap datar

    for x in (-9, -6, -3, 3, 6, 9):
        b.box("Glass", (1.6, 0.12, 1.3), (x, -D / 2, 1.2))
        b.box("Glass", (1.6, 0.12, 1.3), (x, D / 2, 1.2))
    b.box("Door_Wood", (2.4, 0.12, 2.4), (0, -D / 2, 0))               # pintu ganda

    # selasar (koridor depan) + tiang
    b.box("Concrete", (L, 2.0, 0.15), (0, -D / 2 - 1.0, 3.2))
    for x in (-10, -6, -2, 2, 6, 10):
        b.box("Concrete", (0.25, 0.25, 3.2), (x, -D / 2 - 1.85, 0))
    b.box("Concrete", (L, 2.0, 0.12), (0, -D / 2 - 1.0, 0))            # lantai selasar
    return b


# =====================================================================
# 2. VEGETASI  (SM_Tree / SM_Bush / SM_Grass)
# =====================================================================
def gen_pohon_a():
    b = Builder("SM_Tree_01", seed=1)
    b.cyl("Trunk", (0, 0, 0), 0.28, 0.18, 2.8, segs=6)
    b.blob("Leaf_Dark", (0, 0, 3.8), 1.8, (1, 1, 0.9), 2, 0.12)
    b.blob("Leaf_Light", (0.7, 0.3, 4.6), 1.1, (1, 1, 0.9), 2, 0.10)
    b.blob("Leaf_Light", (-0.8, -0.4, 3.4), 1.0, (1, 1, 0.9), 2, 0.10)
    return b


def gen_pohon_b():
    b = Builder("SM_Tree_02")
    b.cyl("Trunk", (0, 0, 0), 0.20, 0.12, 1.8, segs=6)
    b.cyl("Leaf_Dark", (0, 0, 1.2), 1.60, 0.0, 2.2, segs=8)
    b.cyl("Leaf_Dark", (0, 0, 2.5), 1.25, 0.0, 2.0, segs=8)
    b.cyl("Leaf_Light", (0, 0, 3.8), 0.85, 0.0, 1.8, segs=8)
    return b


def gen_semak(name, flowers, seed):
    b = Builder(name, seed=seed)
    spots = [(0, 0, 0.35, 0.55), (0.55, 0.15, 0.30, 0.45),
             (-0.50, 0.20, 0.30, 0.45), (0.05, -0.50, 0.30, 0.42)]
    for x, y, z, r in spots:
        b.blob("Leaf_Dark", (x, y, z), r, (1, 1, 0.75), 1, 0.06)
    if flowers:
        for _ in range(6):
            a = b.rng.uniform(0, math.tau)
            rad = b.rng.uniform(0.1, 0.7)
            b.blob("Flower", (math.cos(a) * rad, math.sin(a) * rad, 0.62), 0.07, subdiv=1)
    b.snap_to_ground()
    return b


def gen_rumput():
    b = Builder("SM_Grass_01", seed=7)
    for i in range(14):
        a = b.rng.uniform(0, math.tau)
        rad = b.rng.uniform(0.0, 0.18)
        h = b.rng.uniform(0.35, 0.6)
        tilt = (b.rng.uniform(-0.35, 0.35), b.rng.uniform(-0.35, 0.35))
        mat = "Grass" if i % 2 == 0 else "Leaf_Light"
        b.cyl(mat, (math.cos(a) * rad, math.sin(a) * rad, 0), 0.035, 0.0, h,
              segs=3, tilt=tilt)
    return b


# =====================================================================
# 3. INFRASTRUKTUR  (SM_Road / SM_Sidewalk / SM_Fence)
# =====================================================================
def gen_jalan_lurus():
    b = Builder("SM_Road_Straight_01")
    b.box("Asphalt", (6.0, 10.0, 0.1), (0, 0, 0))
    for y in (-4, -2, 0, 2, 4):                       # marka putus-putus tengah
        b.box("Line_White", (0.15, 1.2, 0.012), (0, y, 0.1))
    for x in (-2.7, 2.7):                             # garis tepi
        b.box("Line_White", (0.12, 10.0, 0.012), (x, 0, 0.1))
    return b


def gen_jalan_tikungan():
    """Tikungan 90 derajat, lebar 6 m. Pivot = pusat busur (memudahkan snapping)."""
    b = Builder("SM_Road_Curve_01")
    b.arc_slab("Asphalt", 1.0, 7.0, math.pi / 2, 12, 0.1)
    return b


def gen_trotoar():
    b = Builder("SM_Sidewalk_01")
    b.box("Concrete", (1.5, 10.0, 0.15), (0, 0, 0))
    b.box("Curb", (0.2, 10.0, 0.2), (-0.65, 0, 0))    # kerb di sisi jalan
    for y in (-2.5, 0, 2.5):                          # sambungan paving
        b.box("Curb", (1.3, 0.03, 0.01), (0.1, y, 0.15))
    return b


def gen_pagar():
    """Satu segmen pagar 2 m (modular, bisa diulang di Unity)."""
    b = Builder("SM_Fence_01")
    b.box("Concrete", (2.0, 0.15, 0.3), (0, 0, 0))                    # dasar beton
    for sx in (-1, 1):
        b.box("Metal", (0.12, 0.12, 1.2), (sx * 0.94, 0, 0))          # tiang
    b.box("Metal", (2.0, 0.04, 0.05), (0, 0, 1.1))                    # rel atas
    b.box("Metal", (2.0, 0.04, 0.05), (0, 0, 0.4))                    # rel bawah
    for i in range(9):                                                # jeruji
        b.box("Metal", (0.03, 0.03, 0.8), (-0.8 + i * 0.2, 0, 0.35))
    return b


# =====================================================================
# 4. OBJEK LINGKUNGAN  (SM_Rock / SM_Trashbin / SM_PowerPole / SM_StreetLamp)
# =====================================================================
def gen_batu(name, radius, scale, seed, cluster=False):
    b = Builder(name, seed=seed)
    b.blob("Rock", (0, 0, 0), radius, scale, 1, radius * 0.18)
    if cluster:
        b.blob("Rock", (radius * 1.1, radius * 0.4, 0), radius * 0.6,
               (1.0, 0.8, 0.6), 1, radius * 0.1)
    b.snap_to_ground()
    return b


def gen_tempat_sampah():
    b = Builder("SM_Trashbin_01")
    b.cyl("Trash_Green", (0, 0, 0), 0.28, 0.34, 0.8, segs=10)
    b.cyl("Roof_Dark", (0, 0, 0.8), 0.37, 0.37, 0.06, segs=10)
    b.box("Roof_Dark", (0.12, 0.05, 0.05), (0, 0, 0.86))               # pegangan tutup
    return b


def gen_tiang_listrik():
    b = Builder("SM_PowerPole_01")
    b.cyl("Concrete", (0, 0, 0), 0.12, 0.08, 8.0, segs=8)
    b.box("Metal", (1.6, 0.1, 0.1), (0, 0, 7.3))                       # palang
    for x in (-0.7, 0, 0.7):
        b.cyl("Metal", (x, 0, 7.4), 0.04, 0.04, 0.15, segs=6)          # isolator
    return b


def gen_tiang_lampu():
    b = Builder("SM_StreetLamp_01")
    b.cyl("Metal", (0, 0, 0), 0.10, 0.07, 5.0, segs=8)
    b.box("Metal", (0.9, 0.08, 0.08), (0.45, 0, 4.9))                  # lengan
    b.box("Lamp", (0.45, 0.22, 0.10), (0.85, 0, 4.82))                 # kepala lampu
    return b


# =====================================================================
# 5. OBJEK PENDUKUNG  (SM_Sign / SM_Signboard)
# =====================================================================
def _sign_pole(b, height, y=0.07):
    b.cyl("Metal", (0, y, 0), 0.04, 0.04, height, segs=6)


def gen_rambu_titik_kumpul():
    b = Builder("SM_Sign_AssemblyPoint_01")
    _sign_pole(b, 2.4)
    b.box("Sign_Green", (0.9, 0.06, 0.9), (0, 0, 1.5))
    b.box("Sign_White", (0.8, 0.02, 0.8), (0, -0.035, 1.55))           # bingkai putih
    b.box("Sign_Green", (0.7, 0.02, 0.7), (0, -0.045, 1.60))           # isi hijau
    for x in (-0.2, 0.0, 0.2):                                         # 3 figur orang
        b.box("Sign_White", (0.10, 0.02, 0.22), (x, -0.065, 1.72))
        b.blob("Sign_White", (x, -0.065, 2.05), 0.055, subdiv=1)
    return b


def gen_rambu_jalur_evakuasi():
    b = Builder("SM_Sign_EvacRoute_01")
    _sign_pole(b, 2.4)
    b.box("Sign_Green", (1.2, 0.06, 0.6), (0, 0, 1.8))
    b.box("Sign_White", (1.1, 0.02, 0.5), (0, -0.035, 1.85))
    b.box("Sign_Green", (1.0, 0.02, 0.4), (0, -0.045, 1.90))
    b.box("Sign_White", (0.5, 0.02, 0.10), (-0.10, -0.065, 2.05))      # batang panah
    b.prism_xz("Sign_White", [(0.15, 1.98), (0.15, 2.22), (0.40, 2.10)],
               -0.075, -0.055)                                          # kepala panah
    return b


def gen_papan_petunjuk():
    b = Builder("SM_Signboard_01")
    for sx in (-1, 1):
        b.box("Door_Wood", (0.10, 0.10, 2.4), (sx * 0.8, 0.10, 0))
    b.box("Sign_Blue", (2.0, 0.08, 0.9), (0, 0, 1.4))
    b.box("Sign_Yellow", (2.0, 0.10, 0.08), (0, 0, 2.3))                # list kuning atas
    b.box("Sign_White", (1.9, 0.02, 0.8), (0, -0.05, 1.45))
    b.box("Sign_Blue", (1.8, 0.02, 0.7), (0, -0.06, 1.50))
    b.box("Sign_White", (0.9, 0.02, 0.12), (-0.20, -0.07, 1.79))
    b.prism_xz("Sign_White", [(0.25, 1.65), (0.25, 2.05), (0.65, 1.85)],
               -0.08, -0.06)
    return b


# =====================================================================
# KATALOG: folder Unity -> daftar (fungsi pembuat)
# =====================================================================
CATALOG = {
    "Buildings": [
        lambda: gen_rumah("SM_House_01", 8.0, 10.0, 3.0, "Wall_Cream", "Roof_Red", False),
        lambda: gen_rumah("SM_House_02", 7.0, 8.0, 3.0, "Wall_Blue", "Roof_Dark", True),
        gen_gedung,
        gen_sekolah,
    ],
    "Vegetation": [
        gen_pohon_a,
        gen_pohon_b,
        lambda: gen_semak("SM_Bush_01", False, 3),
        lambda: gen_semak("SM_Bush_02", True, 4),
        gen_rumput,
    ],
    "Infrastructure": [
        gen_jalan_lurus,
        gen_jalan_tikungan,
        gen_trotoar,
        gen_pagar,
    ],
    "Props": [
        lambda: gen_batu("SM_Rock_01", 0.40, (1.0, 0.8, 0.6), 11),
        lambda: gen_batu("SM_Rock_02", 0.60, (1.2, 0.9, 0.7), 12),
        lambda: gen_batu("SM_Rock_03", 0.90, (1.0, 0.9, 0.7), 13, cluster=True),
        gen_tempat_sampah,
        gen_tiang_listrik,
        gen_tiang_lampu,
    ],
    "Signage": [
        gen_rambu_titik_kumpul,
        gen_rambu_jalur_evakuasi,
        gen_papan_petunjuk,
    ],
}


# =====================================================================
# EXPORT & SCENE
# =====================================================================
def fresh_collection():
    col = bpy.data.collections.get(COLLECTION_NAME)
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        col = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(col)
    return col


def export_fbx(obj, folder):
    os.makedirs(folder, exist_ok=True)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(folder, obj.name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
    )


def run(only=None, export=True, asset=None):
    col = fresh_collection()
    models_root = os.path.join(UNITY_ROOT, MODELS_SUBPATH)
    cursor_y = 0.0
    total = 0

    for category, makers in CATALOG.items():
        if only and category.lower() != only.lower():
            continue

        objs = []
        for make in makers:
            builder = make()
            if asset and builder.name.lower() != asset.lower():
                builder.bm.free()
                continue
            objs.append(builder.build(col))                 # dibuat di origin
        if not objs:
            continue

        if export:
            for obj in objs:
                export_fbx(obj, os.path.join(models_root, category))

        # susun untuk preview di viewport (setelah export)
        row_depth = max(o.dimensions.y for o in objs)
        cursor_x = 0.0
        for o in objs:
            o.location = (cursor_x + o.dimensions.x / 2,
                          cursor_y + row_depth / 2, 0.0)
            cursor_x += o.dimensions.x + PREVIEW_GAP
        cursor_y += row_depth + PREVIEW_GAP * 2
        total += len(objs)
        print(f"[Siaga] {category}: {len(objs)} asset")

    if SAVE_BLEND and export and not asset and not only:
        blend_path = os.path.join(UNITY_ROOT, BLEND_FILE)
        os.makedirs(os.path.dirname(blend_path), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)
        print(f"[Siaga] .blend disimpan: {blend_path}")

    print(f"[Siaga] Selesai: {total} asset.")


def main():
    global UNITY_ROOT
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--unity-root")
    p.add_argument("--only", help="Buildings | Vegetation | Infrastructure | Props | Signage")
    p.add_argument("--asset", help="Satu asset saja, contoh: SM_House_01")
    p.add_argument("--no-export", action="store_true")
    args = p.parse_args(argv)

    if args.unity_root:
        UNITY_ROOT = args.unity_root
    run(only=args.only, export=EXPORT_FBX and not args.no_export, asset="SM_House_01")


if __name__ == "__main__":
    main()