all: main_ui.py

main_ui.py: main.ui
	pyuic4 -o main_ui.py main.ui
