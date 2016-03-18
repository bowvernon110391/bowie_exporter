import array
import sys


def make_buffer(format, data):
    buf = array.array(format, data)
    if sys.byteorder != 'little':
        buf.byteswap()
    return buf


def is_valid_bone(b):
    if "ik." in b.name:
        return False
    return True


def get_bone_id(ob, name):
    bones = ob.bones

    c = 0
    for i, b in enumerate(bones):
        if not is_valid_bone(b):
            continue
        if name == b.name:
            return c
        c += 1
    return -1


def build_bone_ids(ob):
    if ob is None:
        print("no skeleton selected")
    else:
        bones = ob.bones
        boneid = {}

        c = 0
        for i, b in enumerate(bones):
            # skip if bone is ik bone
            if not is_valid_bone(b):
                continue
            boneid[b.name] = c
            c += 1

        return boneid
    return None


class BoneIds:
    def __init__(self, ob):
        self.ids = {}
        self.ob = ob
        self.lookup = build_bone_ids(ob)

    def get_my_id(self, name):
        c = 0
        for b in self.ob.bones:
            if not is_valid_bone(b):
                continue
            if b.name == name:
                return c
            c += 1
        return -1

    def get_my_name(self, b_id):
        for name in self.lookup:
            if b_id == self.lookup[name]:
                return name
        return "None"
