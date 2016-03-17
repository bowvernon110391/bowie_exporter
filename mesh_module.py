import bpy
from mathutils import *

from . import helper


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
        # return false if something's wrong
        if ob.type != 'MESH':
            print("Selected object is not a mesh!")
            return False

        mesh = ob.data
        verts = mesh.vertices
        tris = mesh.polygons
        mats = mesh.materials
        groups = None

        # if it has weights, there should be an armature
        if len(ob.vertex_groups) > 0:
            self.has_weights = True
            groups = ob.vertex_groups

        if self.has_weights:
            if len(bpy.data.armatures) < 1:
                return False
        # build consistent bone indices
        bone_ref_ids = {}
        if self.has_weights:
            bone_ref_ids = helper.build_bone_ids(bpy.data.armatures[0])

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
                v_pos = v_data.co
                # -normal
                v_nor = v_data.normal
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
                        g_idx = v_data.groups[gi].group;
                        # group name == bone name
                        b_name = groups[g_idx].name
                        g_w = v_data.groups[gi].weight;
                        bone_ids[gi] = bone_ref_ids[b_name]
                        bone_ws[gi] = g_w
                # now vertex data is complete
                new_vertex.pos = v_pos
                new_vertex.normal = v_nor
                new_vertex.uv = uv_data
                new_vertex.bone_ids = bone_ids
                new_vertex.bone_ws = bone_ws

                new_vertex_id = self.get_vertex_id(new_vertex)
                # print(new_vertex_id)
                # add to grp_tris
                grp_tris.append(new_vertex_id)


def export_mesh(self, ctx):
    mesh = MyMesh()
    ob = ctx.object
    print(ob.type)
    if mesh.read_from_object(ob):
        self.report({'INFO'}, "Reading mesh done")
        write_mesh_ascii(self.filepath, mesh)
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
    for grp in mesh.group_tris:
        icount += len(grp)
    fw("icount: %d\n" % icount)

    # write vertices data right below that
    for v in mesh.vertices:
        # write data that must be there
        fw("%.6f %.6f %.6f | %.6f %.6f %.6f | %.6f %.6f" % (v.pos.x, v.pos.y, v.pos.z,
                                                            v.normal.x, v.normal.y, v.normal.z,
                                                            v.uv.x, v.uv.y))
        if mesh.has_weights:
            fw(" | %d %d %d %d | %.6f %.6f %.6f %.6f" % (v.bone_ids[0], v.bone_ids[1], v.bone_ids[2], v.bone_ids[3],
                                                         v.bone_ws[0], v.bone_ws[1], v.bone_ws[2], v.bone_ws[3]))

        fw("\n")

    file.close()
