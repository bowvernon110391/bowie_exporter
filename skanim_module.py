import copy

import bpy
from mathutils import *

from . import helper
from . import skel_module

SKANIM_VERSION = 1


class SkAnim:
    class Action:

        class Keyframe:
            def __init__(self):
                # keyframe, contain bone id, positional and rotational data
                self.time = 0.0
                # key = bone_id, value = array of Transform
                self.bone_pose = {}

        def __init__(self):
            # action name
            self.name = ""
            # keyframe data for this action, it's 2 dimensional array
            # it will be bones_per_keyframe * num_keyframe
            self.num_keyframe = 0
            self.keyframes = []

    def __init__(self):
        # number of action this armature has
        self.num_action = 0
        # all keyframe must have similar number of bones, or error would occur
        self.bones_per_keyframe = 0
        # store action data here
        self.actions = []

        # helper
        self.helper_dict = None

        self.last_action = None
        self.last_keyframe = None
        self.last_transform = None

    def add_action(self, name, numkeys):
        ac = SkAnim.Action()
        ac.name = name
        ac.num_keyframe = numkeys
        self.actions.append(ac)
        self.last_action = self.actions[len(self.actions) - 1]

    def add_keyframe(self, time, bpk):
        k = SkAnim.Action.Keyframe()

        k.time = time
        self.last_action.keyframes.append(k)
        self.last_keyframe = self.last_action.keyframes[len(self.last_action.keyframes) - 1]

    def add_bone_pose(self, id):
        self.last_keyframe.bone_pose[id] = skel_module.Skeleton.Bone.Transform()
        self.last_transform = self.last_keyframe.bone_pose[id]

    def build_from_context(self, ctx):
        ob = ctx.object
        sc = ctx.scene

        if ob.type == 'ARMATURE':
            bone_ids = helper.build_bone_ids(ob.data)
            self.helper_dict = bone_ids

            # the number of usable bones
            bone_len = len(bone_ids)
            self.bones_per_keyframe = bone_len

            print("BONE_COUNT: %d" % len(bone_ids))
            acs = bpy.data.actions

            self.num_action = len(acs)

            # for each action
            for ac in acs:
                # check
                print("before: %s" % ob.animation_data.action.name)
                # set animation data
                ob.animation_data.action = ac

                print("after: %s" % ob.animation_data.action.name)

                # create action
                ac_data = SkAnim.Action()

                print(ac.name)
                ac_data.name = ac.name

                # grab keyframe time
                kfs = ac.fcurves[0].keyframe_points

                ac_data.num_keyframe = len(kfs)

                # for each keyframe
                for i, kf in enumerate(kfs):
                    # create new key frame
                    kf_data = SkAnim.Action.Keyframe()

                    print("\t%d: time %f" % (i, kf.co.x))
                    print(sc)

                    kf_data.time = kf.co.x

                    # set scene frame to keyframe time
                    sc.frame_set(kf_data.time)
                    # now iterate over each posebone,
                    # grabbing data on the way

                    # for each pose bone
                    for b in ob.pose.bones:
                        # skip ik bones
                        if not helper.is_valid_bone(b):
                            continue

                        # good to go
                        head = b.head
                        tail = b.tail
                        rot = b.matrix.to_quaternion()

                        bone_transform = skel_module.Skeleton.Bone.Transform()
                        bone_transform.head = head.copy()
                        bone_transform.tail = tail.copy()
                        bone_transform.rot = rot.copy()

                        kf_data.bone_pose[bone_ids[b.name]] = copy.copy(bone_transform)
                        if bone_ids[b.name] == 12:
                            print("%d: %.4f %.4f %.4f" % (bone_ids[b.name], head.x, head.y, head.z))
                            # print("\t\t%s(%d) | %f %f %f | %f %f %f | %f %f %f %f" % (b.name, bone_ids[b.name],
                            #                                                           head.x, head.y, head.z,
                            #                                                           tail.x, tail.y, tail.z,
                            #                                                           rot.x, rot.y, rot.z, rot.w) )
                    # let's add keyframe data
                    ac_data.keyframes.append(copy.copy(kf_data))
                # let's add to action
                self.actions.append(copy.copy(ac_data))
            # we succeeds
            return True
        # not an armature
        return False

    def log(self):
        file = open("D:\\log.txt", "w")

        fw = file.write

        for ac in self.actions:
            fw("%s: %d\n" % (ac.name, ac.num_keyframe))
            for kf in ac.keyframes:
                fw("\t%f: " % kf.time)
                t = kf.bone_pose[12]
                fw("%f %f %f\n" % (t.head.x, t.head.y, t.head.z))

        file.close()

        # def build_from_context2(self, ctx):
        #     ob = ctx.object
        #     sc = ctx.scene
        #
        #     if ob.type == 'ARMATURE':
        #         bone_ids = helper.build_bone_ids(ob.data)
        #         self.helper_dict = bone_ids
        #
        #         # the number of usable bones
        #         bone_len = len(bone_ids)
        #         self.bones_per_keyframe = bone_len
        #
        #         print("BONE_COUNT: %d" % len(bone_ids))
        #         acs = bpy.data.actions
        #
        #         self.num_action = len(acs)
        #
        #         # for each action
        #         for ac in acs:
        #             # check
        #             print("before: %s" % ob.animation_data.action.name)
        #             # set animation data
        #             ob.animation_data.action = ac
        #
        #             print("after: %s" % ob.animation_data.action.name)
        #
        #             print(ac.name)
        #
        #
        #             # grab keyframe time
        #             kfs = ac.fcurves[0].keyframe_points
        #
        #             # create action
        #             self.add_action(ac.name, len(kfs))
        #
        #             # for each keyframe
        #             for i, kf in enumerate(kfs):
        #                 # create new key frame
        #                 # kf_data = SkAnim.Action.Keyframe()
        #                 self.add_keyframe(kf.co.x, bone_len)
        #
        #                 print("\t%d: time %f" % (i, kf.co.x) )
        #
        #                 # set scene frame to keyframe time
        #                 sc.frame_set(kf.co.x)
        #                 # now iterate over each posebone,
        #                 # grabbing data on the way
        #
        #                 # for each pose bone
        #                 for b in ob.pose.bones:
        #                     # skip ik bones
        #                     if not helper.is_valid_bone(b):
        #                         continue
        #
        #                     # good to go
        #                     head = b.head
        #                     tail = b.tail
        #                     rot = b.matrix.to_quaternion()
        #
        #                     bone_transform = skel_module.Skeleton.Bone.Transform()
        #                     bone_transform.head = head
        #                     bone_transform.tail = tail
        #                     bone_transform.rot = rot
        #
        #                     self.add_bone_pose(bone_ids[b.name])
        #
        #                     self.last_transform.head = head
        #                     self.last_transform.tail = tail
        #                     self.last_transform.rot = rot
        #
        #                     # kf_data.bone_pose[ bone_ids[b.name] ] = bone_transform
        #                     if bone_ids[b.name] == 12:
        #                         print("%d: %.4f %.4f %.4f" % (bone_ids[b.name], head.x, head.y, head.z) )
        #                     # print("\t\t%s(%d) | %f %f %f | %f %f %f | %f %f %f %f" % (b.name, bone_ids[b.name],
        #                     #                                                           head.x, head.y, head.z,
        #                     #                                                           tail.x, tail.y, tail.z,
        #                     #                                                           rot.x, rot.y, rot.z, rot.w) )
        #                 # let's add keyframe data
        #             # let's add to action
        #         # we succeeds
        #         return True
        #     # not an armature
        #     return False
        #


def write_anim_data_ascii(filename, skanim):
    file = open(filename, "w")

    fw = file.write

    fw("num_actions: %d , " % skanim.num_action)
    fw("bone_per_keyframe: %d" % skanim.bones_per_keyframe)
    fw("\n\n")

    for ac_data in skanim.actions:
        fw("\taction_name: %s , kf_count: %d\n" % (ac_data.name, ac_data.num_keyframe))
        # write keyframe data
        for kf_data in ac_data.keyframes:
            fw("\t\t@time %f\n" % kf_data.time)
            for bp in kf_data.bone_pose:
                b = kf_data.bone_pose[bp]
                fw("\t\t\t%d: %f %f %f | %f %f %f | %f %f %f %f\n" % (bp, b.head.x, b.head.y, b.head.z,
                                                                      b.tail.x, b.tail.y, b.tail.z,
                                                                      b.rot.x, b.rot.y, b.rot.z, b.rot.w))
    file.close()


def write_anim_data(filename, skanim):
    file = open(filename, "wb")

    fw = file.write

    # write header [ version, bone_per_kf ] = 2 bytes
    header = [SKANIM_VERSION, skanim.bones_per_keyframe]
    fw(helper.make_buffer('B', header))

    # next, number of actions: ushort -> 2 bytes
    header = [skanim.num_action]
    fw(helper.make_buffer('H', header))

    # write down each action data
    for ac_data in skanim.actions:
        # fw("\taction_name: %s , kf_count: %d\n" % (ac_data.name, ac_data.num_keyframe) )
        ac_name = ac_data.name
        # pad em 32 bytes
        while len(ac_name) < 32:
            ac_name += chr(0)
        # write action name -> 32 bytes
        fw(ac_name.encode('utf-8'))
        # write num keyframe : ushort -> 2 bytes
        tmp = [ac_data.num_keyframe]
        fw(helper.make_buffer('H', tmp))
        # write keyframe data
        for kf_data in ac_data.keyframes:
            # write time : float -> 4 bytes
            tmp = [kf_data.time]
            fw(helper.make_buffer('f', tmp))
            # write data for each pose bone, it's already sorted
            for bp in kf_data.bone_pose:
                bdata = kf_data.bone_pose[bp]

                # first is the bone id
                tmp = [bp]
                fw(helper.make_buffer('B', tmp))

                # then the transformation data
                tmp = [
                    bdata.head.x, bdata.head.y, bdata.head.z,
                    bdata.tail.x, bdata.tail.y, bdata.tail.z,
                    bdata.rot.x, bdata.rot.y, bdata.rot.z, bdata.rot.w
                ]
                fw(helper.make_buffer('f', tmp))
                # fw("\t\t@time %f\n" % kf_data.time)
                # for bp in kf_data.bone_pose:
                #     b = kf_data.bone_pose[bp]
                #     fw("\t\t\t%d: %f %f %f | %f %f %f | %f %f %f %f\n" % (bp, b.head.x, b.head.y, b.head.z,
                #                                                           b.tail.x, b.tail.y, b.tail.z,
                #                                                           b.rot.x, b.rot.y, b.rot.z, b.rot.w) )

    file.close()


def export_anim_data(e, ctx):
    skanim = SkAnim()
    if not skanim.build_from_context(ctx):
        e.report({'ERROR'}, "You must be doing something wrong. Check console")
    else:
        write_anim_data(e.filepath, skanim)
        skanim.log()
        e.report({'INFO'}, "Written anim data to: %s" % e.filepath)


# def test_action():
#     print(bpy.context.object.type)
#     for ac in bpy.data.actions:
#         print(ac.name)
#
# print("Printing action names....")
# test_action()

# test it

testAnim = SkAnim()
testAnim.build_from_context(bpy.context)
testAnim.log()
