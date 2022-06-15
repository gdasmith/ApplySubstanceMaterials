bl_info = {
	# required
	'name': 'Apply Substance Output Materials',
	'blender': (3, 00, 0),
	'category': 'Object',
	# optional
	'version': (1, 6, 2),
}

import bpy
import glob

from bpy.props import (StringProperty, PointerProperty)
from bpy.types import (Panel, Operator,  AddonPreferences, PropertyGroup)

#----------	
#To do:
#0. Add PBR output materials to the relevant section below
#1. Label the nodes correctly
#2. Layout the nodes nicely if possible (not badly overlapping)
#----------

#Setting up the UI and registering the addon

class MyProperties(PropertyGroup):
	path : StringProperty(
		name="",
		description="Path to Directory",
		default="",
		maxlen=1024,
		subtype='DIR_PATH')

class ApplySubstanceMaterialsUI(bpy.types.Panel):
	bl_idname = 'VIEW3D_PT_ApplySubstanceMaterial'
	bl_label = 'Apply Substance Outputs'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'

	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		col.prop(scn.my_tool, "path", text="")
		layout.operator(RUNAPPLY_OT_func_1.bl_idname)

#The main process
class RUNAPPLY_OT_func_1(bpy.types.Operator):		
	bl_idname = "runapply.func_1"
	bl_label = "Apply Substance Textures"
	def execute(self, context):
		#----
		#Use selects the directory using the folder selector. This is transferred to the script here.
		myDir = bpy.data.scenes["Scene"].my_tool.path
		print(myDir)
		#-----

		myFiles=[]

		#Create a list of all the image files in the directory -- list could be extended but more likely than not to be png files
		for x in glob.glob(myDir + "/*.png"):
			myFiles.append(x)
		for x in glob.glob(myDir + "/*.tiff"):
			myFiles.append(x)
		for x in glob.glob(myDir + "/*.tif"):
			myFiles.append(x)
		for x in glob.glob(myDir + "/*.psd"):
			myFiles.append(x)	
		for x in glob.glob(myDir + "/*.exr"):
			myFiles.append(x)	

		#tidy the list by removing the file path
		for x in range(len(myFiles)):
			myFiles[x] = myFiles[x].replace(myDir,"")
			print(len(myFiles))

		#----
		#Establish how many materials the current object has and create a list of names
		num_mat = len(bpy.context.active_object.data.materials)
		#Declare empty list to contain material names
		materialsList = []
		#Create a list of all object materials
		x = 0
		while x < num_mat:
			bpy.context.object.active_material_index = x
			mat_name = bpy.context.object.active_material.name
			materialsList.append(mat_name)
			x = x + 1

		#For each material, assign a texture to one of the types of texture (colour, normal, etc.). Not all materials will have all textures.
		for i in range(len(materialsList)):
			#This currentMaterial is the material name
			bpy.context.object.active_material_index = i
			currentMaterial = bpy.context.object.active_material.name
			#loop through texture list and create a list of only those textures with matching names
			textureList = []
			for x in range(len(myFiles)):
				if currentMaterial in myFiles[x]:
					textureList.append(myFiles[x])
			#set texture type variables to empty string so they can be included/excluded as necessary
			normal = colour = height = opacity = rough = emissive = metal = reflection = ""	
			for j in range(len(textureList)):
				#Period added after the key word to reduce chance of picking up a descriptive word from the name (e.g. metallic)
				if "Normal." in textureList[j]:
					normal = textureList[j]
				if "Base_Color." in textureList[j]:
					colour = textureList[j]
				if "BaseColor." in textureList[j]:
					colour = textureList[j]
				if "Height." in textureList[j]:
					height = textureList[j]
				if "Opacity." in textureList[j]:
					opacity = textureList[j]
				if "opacity." in textureList[j]:
					opacity = textureList[j]
				if "Roughness." in textureList[j]:
					rough = textureList[j]
				if "Emissive." in textureList[j]:
					emissive = textureList[j]
				if "Metallic." in textureList[j]:
					metal = textureList[j]
				if "Reflection." in textureList[j]:
					reflection = textureList[j]
			
			# Use these textures to set up the node groups, based on whether the textures exist
			#Select the principled shader for the material (should only be one shader)
			node_tree = bpy.context.object.active_material.node_tree
			nodes = node_tree.nodes
			links = node_tree.links
			principled_bsdf = nodes.get("Principled BSDF")
					
			#Add textures and links to the principled shader
			#Colour
			if colour != "":
				colourTex = nodes.new('ShaderNodeTexImage')
				colourTex.image = bpy.data.images.load(myDir + colour)
				links.new(principled_bsdf.inputs["Base Color"], colourTex.outputs["Color"])
			#Height
			if height != "":
				heightTex = nodes.new('ShaderNodeTexImage')
				heightTex.image = bpy.data.images.load(myDir + height)
			
			#Metallic
			if metal != "":
				metallicTex = nodes.new('ShaderNodeTexImage')
				metallicTex.image = bpy.data.images.load(myDir + metal)
				metallicTex.image.colorspace_settings.name = "Non-Color"
				links.new(principled_bsdf.inputs["Metallic"], metallicTex.outputs["Color"])
			#Normal
			if normal != "":
				normalTex = nodes.new('ShaderNodeTexImage')
				normalTex.image = bpy.data.images.load(myDir + normal)
				normalTex.image.colorspace_settings.name = "Non-Color"
				Normal_map = nodes.new('ShaderNodeNormalMap')
				Bump_map = nodes.new('ShaderNodeBump')
				links.new(Normal_map.inputs["Color"], normalTex.outputs["Color"])
				links.new(Bump_map.inputs["Height"], heightTex.outputs["Color"])
				links.new(Normal_map.outputs["Normal"], Bump_map.inputs["Normal"])
				links.new(principled_bsdf.inputs["Normal"], Bump_map.outputs["Normal"])
			#Roughness
			if rough != "":
				roughTex = nodes.new('ShaderNodeTexImage')
				roughTex.image = bpy.data.images.load(myDir + rough)
				roughTex.image.colorspace_settings.name = "Non-Color"
				links.new(principled_bsdf.inputs["Roughness"], roughTex.outputs["Color"])
				#Opacity
			if opacity != "":
				opacityTex = nodes.new('ShaderNodeTexImage')
				opacityTex.image = bpy.data.images.load(myDir + opacity)
				opacityTex.image.colorspace_settings.name = "Non-Color"
				links.new(principled_bsdf.inputs["Alpha"], opacityTex.outputs["Color"])
				#Emission
			if emissive != "":
				emissionTex = nodes.new('ShaderNodeTexImage')
				emissionTex.image = bpy.data.images.load(myDir + emissive)
				links.new(principled_bsdf.inputs["Emission"], emissionTex.outputs["Color"])
				
			#Reflection -- commented out for now, not sure if this would be used as a Substance output
			#if reflection != "":
			#	reflectTex = nodes.new('ShaderNodeTexImage')
			#	reflectTex.image = bpy.data.images.load(myDir + reflection)
			#	reflectTex.image.colorspace_settings.name = "Non-Color"
		return {'FINISHED'} 
		
CLASSES = [MyProperties,ApplySubstanceMaterialsUI,RUNAPPLY_OT_func_1]


def register():
	print('registered') # just for debug
	for myClass in CLASSES:
		bpy.utils.register_class(myClass)
	bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)
		
def unregister():
	print('unregistered') # just for debug
	for myClass in CLASSES:
		bpy.utils.unregister_class(myClass)
	del bpy.types.Scene.my_tool
		
if __name__== '__main__':
	register()	
	