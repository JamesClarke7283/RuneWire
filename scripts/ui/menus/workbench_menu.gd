class_name WorkbenchMenu
extends CraftingMenu
## The Artificer's Workbench screen: a CraftingMenu fixed to the "workbench" station (craft gadgets,
## components and guns; upgrade and salvage weapons).


func _init() -> void:
	super._init()
	station = "workbench"
