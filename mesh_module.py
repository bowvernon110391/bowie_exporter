import bpy
from mathutils import *

from . import helper

MESH_VERSION = 1

class MyVertex:
    def __init__(self):
        self.pos = Vector()
        self.normal = Vector()
        self.uv = Vector([0, 0])
        self.bone_ids = Vector([0, 0, 0, 0])
        self.bone_ws = Vector([0, 0, 0, 0])

    def copy(self):
        r = MyVertex()
        r.pos = self.pos.copy()
        r.normal = self.normal.copy()
        r.uv = self.uv.copy()
        r.bone_ids = self.bone_ids.copy()
        r.bone_ws = self.bone_ws.copy()
        return r

    def equal(self, v):
        if v.pos != self.pos:
            return False
        if v.normal != self.normal:
            return False
        if v.uv != self.uv:
            return False
        if v.bone_ids != v.bone_ids:
            return False
        if v.bone_ws != v.bone_ws:
            return False
        return True


class MyMesh:
    def __init__(self):
        self.vertices = []
        self.group_tris = {}
        self.group_matname = {}
        self.has_weights = False

    def build_separate_mesh(self, parent_mesh, mesh_id):
        # this will build a separate mesh based on id
        if not isinstance(parent_mesh, MyMesh):
            print("Parent is invalid mesh")
            return False

        # safe to do it
        if mesh_id < 0 or mesh_id >= len(parent_mesh.group_tris):
            # invalid mesh id
            print("Invalid mesh id from parent mesh!")
            return False

        # perfectly safe
        verts = parent_mesh.vertices
        grp_tris = parent_mesh.group_tris[mesh_id]
        grp_name = parent_mesh.group_matname[mesh_id]

        # also copy attributes
        self.has_weights = parent_mesh.has_weights

        # mustnt be empty mesh
        if len(grp_tris) < 3 or len(verts) < 3:
            print("I can't even. Man you're dumb!!")
            return False

        # allocate self data
        self.group_matname[0] = grp_name
        self.group_tris[0] = []

        # find base index
        base_index = grp_tris[0]
        for ti in grp_tris:
            if ti < base_index:
                base_index = ti

        # good, now copy vertices and adjust offset
        for ti in grp_tris:
            v_idx = self.get_vertex_id(verts[ti])
            self.group_tris[0].append(v_idx)
        # reach here, good
        return True

    def add_vertex(self, v):
        self.vertices.append(v)

    def get_vertex_id(self, v):
        for i in range(len(self.vertices)):
            if v.equal(self.vertices[i]):
                return i
        # if we reach here it means no such vertex
        # -add it and return its index
        self.vertices.append(v)
        return len(self.vertices) - 1

    def read_from_object(self, ob):
        lf = open("D:\\bone_id.txt", "w")
        # return false if something's wrong
        if ob.type != 'MESH':
            print("Selected object is not a mesh!")
            return False

        mesh = ob.data
        verts = mesh.vertices
        tris = mesh.polygons
        mats = mesh.materials
        groups = None
        skel = None

        # if it has weights, there should be an armature
        if len(ob.vertex_groups) > 0:
            self.has_weights = True
            groups = ob.vertex_groups

        if self.has_weights:
            if len(bpy.data.armatures) < 1:
                return False

        from . import skel_module
        skel = skel_module.Skeleton()
        skel.build_from_armature(bpy.data.armatures[0])
        # build consistent bone indices

        # resize group_data to hold unordered shit
        for c in range(0, len(mats)):
            self.group_tris[c] = []
            self.group_matname[c] = mats[c].name

            # check uv
        if len(mesh.uv_layers) < 1:
            print("No uv layers. Mission aborted..")
            return False

        uvs = mesh.uv_layers[0].data

        for t in tris:
            idx_count = len(t.vertices)
            mat_id = t.material_index
            if idx_count != 3:
                print("Mesh is not triangulated properly. Mission aborted..")
                return False
            # print("mat: %d(%s) | " % (t.material_index, mats[t.material_index].name))
            grp_tris = self.group_tris[mat_id]
            for ti in range(0, 3):
                # this will hold em all data
                new_vertex = MyVertex()
                # grab vertex index
                v_idx = t.vertices[ti]
                v_data = verts[v_idx]
                # strip vertex data
                # -position
                v_pos = v_data.co.copy()
                # correct position data
                v_pos = helper.correct_pos_opengl(v_pos)
                # -normal
                v_nor = v_data.normal.copy()
                # -uv
                uv_idx = t.loop_indices[ti]
                uv_data = uvs[uv_idx].uv
                # -bone weights if there's one
                # -make default first
                bone_ids = Vector([0, 0, 0, 0])
                bone_ws = Vector([0, 0, 0, 0])
                if self.has_weights:
                    # copy it
                    # print("\tbone_count: %d" % len(v_data.groups), end=" ")

                    for gi in range(0, len(v_data.groups)):
                        g_idx = v_data.groups[gi].group
                        # group name == bone name
                        b_name = groups[g_idx].name
                        g_w = v_data.groups[gi].weight
                        # test it
                        r_id = skel.get_bone_id(b_name)

                        print("%s -> %d" % (b_name, r_id))
                        lf.write("%s -> %d\n" % (b_name, r_id))

                        bone_ids[gi] = r_id
                        bone_ws[gi] = g_w
                # now vertex data is complete
                new_vertex.pos = v_pos.copy()
                new_vertex.normal = v_nor.copy()
                new_vertex.uv = uv_data.copy()
                new_vertex.bone_ids = bone_ids.copy()
                new_vertex.bone_ws = bone_ws.copy()

                new_vertex_id = self.get_vertex_id(new_vertex)
                # print(new_vertex_id)
                # add to grp_tris
                grp_tris.append(new_vertex_id)

        # done. return TRUE
        lf.close()
        return True


def export_mesh(self, ctx):
    mesh = MyMesh()
    ob = ctx.object
    # print(ob.type)
    if mesh.read_from_object(ob):
        self.report({'INFO'}, "Reading mesh done")
        write_mesh(self.filepath, mesh)
    else:
        self.report({'ERROR'}, "Something's wrong. Check console window!")


def write_mesh_ascii(filename, mesh):
    file = open(filename, "w")

    fw = file.write

    # write vcount
    fw("vcount: %d\n" % len(mesh.vertices))
    # write group count?
    fw("group: %d\n" % len(mesh.group_tris))
    # tell em if it's weighted or not
    if mesh.has_weights:
        fw("weighted: 1\n")
    else:
        fw("weighted: 0\n")

    # write index count
    icount = 0
    for i in range(0, len(mesh.group_tris)):
        icount += len(mesh.group_tris[i])
    fw("icount: %d\n" % icount)

    # write vertices data right below that
    v_idx = 0
    for v in mesh.vertices:
        # write data that must be there
        fw("%d: %.6f %.6f %.6f | %.6f %.6f %.6f | %.6f %.6f" % (v_idx, v.pos.x, v.pos.y, v.pos.z,
                                                                v.normal.x, v.normal.y, v.normal.z,
                                                                v.uv.x, v.uv.y))
        v_idx += 1

        if mesh.has_weights:
            fw(" | %d %d %d %d | %.6f %.6f %.6f %.6f" % (v.bone_ids[0], v.bone_ids[1], v.bone_ids[2], v.bone_ids[3],
                                                         v.bone_ws[0], v.bone_ws[1], v.bone_ws[2], v.bone_ws[3]))

        fw("\n")

    # write group data after vertices
    icount = 0
    for i in range(0, len(mesh.group_tris)):
        fw("%s : %d, %d\n" % (mesh.group_matname[i], icount, len(mesh.group_tris[i])))
        icount += len(mesh.group_tris[i])

    # then straight out write indices
    icount = 0
    for i in range(0, len(mesh.group_tris)):
        for v_idx in mesh.group_tris[i]:
            fw("%d: %d\n" % (icount, v_idx))
            icount += 1

    file.close()


def write_mesh(filename, mesh):
    file = open(filename, "wb")

    fw = file.write
    # first, header
    # header = [version, vert_format_id] -> 2 bytes
    vformat = 0
    if mesh.has_weights:
        vformat = 1

    header = [MESH_VERSION, vformat]
    fw(helper.make_buffer('B', header))

    # mesh_info = [vcount, icount, num_goup]  ->  6 bytes
    vcount = len(mesh.vertices)
    icount = 0
    for i in range(0, len(mesh.group_tris)):
        icount += len(mesh.group_tris[i])

    gcount = len(mesh.group_tris)

    mesh_info = [vcount, icount, gcount]
    fw(helper.make_buffer('H', mesh_info))

    # next, write vertices. depending on how it's stored
    for v in mesh.vertices:

        # first write all common vertex data
        fw(helper.make_buffer('f', v.pos))
        fw(helper.make_buffer('f', v.normal))
        fw(helper.make_buffer('f', v.uv))
        # add bone data if exists
        if mesh.has_weights:
            bone_ids = [int(v.bone_ids[0]), int(v.bone_ids[1]), int(v.bone_ids[2]), int(v.bone_ids[3])]
            fw(helper.make_buffer('B', bone_ids))
            fw(helper.make_buffer('f', v.bone_ws))

    # now, write group data
    icount = 0
    for i in range(0, len(mesh.group_tris)):
        # first, write group name  ->  32 bytes
        grp_name = mesh.group_matname[i]
        # pad till 32 bytes
        while len(grp_name) < 32:
            grp_name += chr(0)

        fw(grp_name.encode('utf-8'))
        # then, index data
        # index_data = [start, len]
        index_data = [icount, len(mesh.group_tris[i])]
        fw(helper.make_buffer('H', index_data))

        # advance index start
        icount += index_data[1]

    # finally, write the real index
    for i in range(0, len(mesh.group_tris)):
        fw(helper.make_buffer('H', mesh.group_tris[i]))

    file.close()
