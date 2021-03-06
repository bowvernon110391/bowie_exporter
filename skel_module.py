from bpy.types import Armature
from mathutils import *

from . import helper

SKEL_FILE_VERSION = 1


class Skeleton:
    class Bone:

        class Transform:
            def __init__(self):
                self.head = Vector()
                self.tail = Vector()
                self.rot = Quaternion()

        def __init__(self):
            self.local = self.Transform()
            self.name = ""
            self.parent_name = ""
            self.parent_id = -1

    def __init__(self):
        self.bones = []

    def build_from_armature(self, ob):
        if not isinstance(ob, Armature):
            return False

        # it's armature, safe to say
        bone_ids = helper.build_bone_ids(ob)
        # now we iterate only valid bones
        for b in ob.bones:
            # skip invalid bones
            if not helper.is_valid_bone(b):
                continue
            # it's valid, write down
            new_bone = self.Bone()
            new_bone.name = b.name

            # shall we correct?
            need_correction = False

            if b.parent is not None:
                # if parent is ik bone, ignore. But we must
                # set its transform to absolute!!!
                # and we need to correct em!!
                if not helper.is_valid_bone(b.parent):
                    new_bone.parent_name = "null"
                    need_correction = True

                    # transform by parent
                    new_bone.local.head = b.parent.matrix * b.head + b.parent.tail
                    new_bone.local.tail = b.parent.matrix * b.tail + b.parent.tail
                    new_bone.local.rot = b.parent.matrix.to_quaternion() * b.matrix.to_quaternion()
                else:
                    new_bone.parent_name = b.parent.name
                    new_bone.parent_id = bone_ids[new_bone.parent_name]

                    new_bone.local.head = b.head.copy()
                    new_bone.local.tail = b.tail.copy()
                    new_bone.local.rot = b.matrix.to_quaternion().copy()
            else:
                new_bone.parent_name = "null"
                need_correction = True

                new_bone.local.head = b.head.copy()
                new_bone.local.tail = b.tail.copy()
                new_bone.local.rot = b.matrix.to_quaternion().copy()


            # correct em if they need em
            if need_correction:
                new_bone.local.head = helper.correct_pos_opengl(new_bone.local.head)
                new_bone.local.tail = helper.correct_pos_opengl(new_bone.local.tail)
                new_bone.local.rot = helper.correct_rot_opengl(new_bone.local.rot)
            # log em
            print("==============")
            print(new_bone.name)
            print(new_bone.parent_name)
            print(new_bone.parent_id)
            print("head:")
            print(new_bone.local.head)
            print("tail:")
            print(new_bone.local.tail)
            print(new_bone.local.rot)
            print("==============")
            # add em
            self.bones.append(new_bone)

        return True

    def get_bone_id(self, name):
        for i, b in enumerate(self.bones):
            if name == b.name:
                return i
        return -1


def write_skeleton(filename, skel):
    # write skeleton in ascii plain text
    f = open(filename, "w")

    fw = f.write

    for b in skel.bones:
        fw("%s|%s|%d|" % (b.name, b.parent_name, b.parent_id))
        fw("head: %.6f %.6f %.6f|" % (b.local.head.x, b.local.head.y, b.local.head.z))
        fw("tail: %.6f %.6f %.6f|" % (b.local.tail.x, b.local.tail.y, b.local.tail.z))
        fw("rot: %.6f %.6f %.6f %.6f" % (b.local.rot.w, b.local.rot.x, b.local.rot.y, b.local.rot.z))
        fw("\n")

    f.close()


def write_skeleton_bin(filename, skel):
    # write in binary
    f = open(filename, "wb")

    # local.header[version, num_bones] = 2 bytes
    header = [
        SKEL_FILE_VERSION,
        len(skel.bones)
    ]

    f.write(helper.make_buffer('B', header))

    # now write bone data
    for b in skel.bones:
        bone_name = b.name
        bone_parent_name = b.parent_name
        # pad em to 32 char
        while len(bone_name) < 32:
            bone_name += chr(0)

        while len(bone_parent_name) < 32:
            bone_parent_name += chr(0)
        # write bone name and parent name = 64 bytes
        f.write(bone_name.encode('utf-8'))
        f.write(bone_parent_name.encode('utf-8'))

        # write bone parent id = 1 byte
        bone_parent_id = [b.parent_id]
        f.write(helper.make_buffer('b', bone_parent_id))

        # write bone local.head.xyz + local.tail.xyz + local.rot.xyzw
        bone_transform = [
            b.local.head.x, b.local.head.y, b.local.head.z,
            b.local.tail.x, b.local.tail.y, b.local.tail.z,
            b.local.rot.x, b.local.rot.y, b.local.rot.z, b.local.rot.w
        ]
        f.write(helper.make_buffer('f', bone_transform))

    f.close()


def export_skeleton(e, ctx):
    skel = Skeleton()
    if not skel.build_from_armature(ctx.object.data):
        e.report({'ERROR'}, "Skeleton traversal failed. Maybe you're dumb")
    else:
        write_skeleton_bin(e.filepath, skel)
        e.report({'INFO'}, "Just did something idk")
        e.report({'INFO'}, "saving to: %s" % e.filepath)
