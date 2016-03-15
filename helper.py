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
