#!BPY
import bpy
from bpy.props import BoolProperty
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Bowie File Format Exporter",
    "author": "Bowie",
    "blender": (2, 7, 6),
    "version": (0, 0, 1),
    "location": "File > Import-Export",
    "description": "Export several bowie designed file (.mesh, .skel, .skanim)",
    "category": "Import-Export"
}

# Reload all of ems
if "bpy" in locals():
    import importlib

    if "skel_module" in locals():
        importlib.reload(skel_module)
    if "skanim_module" in locals():
        importlib.reload(skanim_module)


# MESH exporter
class MeshExporter(bpy.types.Operator, ExportHelper):
    bl_idname = "bowie_export.mesh"
    bl_label = "Bowie Mesh Exporter"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".mesh"

    export_mesh_per_material = BoolProperty(
        name="Split export per material",
        description="Will export the mesh into several files, named using its material",
        default=False
    )

    def execute(self, context):
        return {'FINISHED'}


# SKELETON exporter
class SkeletonExporter(bpy.types.Operator, ExportHelper):
    bl_idname = "bowie_export.skel"
    bl_label = "Bowie Skeleton Exporter"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".skel"

    def execute(self, context):
        from . import skel_module

        skel_module.export_skeleton(self, context)
        return {'FINISHED'}


# SKANIM exporter
class SkAnimExporter(bpy.types.Operator, ExportHelper):
    bl_idname = "bowie_export.skanim"
    bl_label = "Bowie Skeletal Animation Exporter"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".skanim"

    def execute(self, context):
        from . import skanim_module

        skanim_module.export_anim_data(self, context)
        return {'FINISHED'}


def menu_func_MESH(self, context):
    self.layout.operator(MeshExporter.bl_idname, text="Bowie Mesh Format(.mesh)")


def menu_func_SKEL(self, context):
    self.layout.operator(SkeletonExporter.bl_idname, text="Bowie Skeleton Format(.skel)")


def menu_func_SKANIM(self, context):
    self.layout.operator(SkAnimExporter.bl_idname, text="Bowie Skeletal Anim Format(.skanim)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_MESH)
    bpy.types.INFO_MT_file_export.append(menu_func_SKEL)
    bpy.types.INFO_MT_file_export.append(menu_func_SKANIM)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_MESH)
    bpy.types.INFO_MT_file_export.remove(menu_func_SKEL)
    bpy.types.INFO_MT_file_export.remove(menu_func_SKANIM)


if __name__ == "__main__":
    register()

print("my name is: %s" % __name__)
