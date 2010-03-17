all: main_ui.py edit_update_ui.py

main_ui.py: main.ui
	pyuic4 -o main_ui.py main.ui

edit_update_ui.py: edit_update.ui
	pyuic4 -o edit_update_ui.py edit_update.ui
