extends Node

func run(m: Node) -> void:
	var ui: GameUI = m.ui
	await get_tree().create_timer(1.0, true, false, true).timeout
	ui.open_menu(QuestLogMenu.new())
	for i in 6:
		await get_tree().create_timer(0.25, true, false, true).timeout
		var cm: MenuPanel = ui.current_menu
		printerr("PAUSE t=%.2f paused=%s ui_mode=%d menu_mode=%d can_process=%s panel_alpha=%.2f fps=%d" % [
			i * 0.25, get_tree().paused, ui.process_mode, cm.process_mode, cm.can_process(), cm.panel.modulate.a, Engine.get_frames_per_second()])
	get_tree().quit()
