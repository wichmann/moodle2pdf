pyinstaller --noconfirm ^
    --log-level=WARN ^
    --clean ^
	--windowed ^
	--icon=".\res\moodle.ico" ^
	--onefile ^
	--add-data="moodleeditor.ui;." ^
	--add-data="res;res\." ^
	--add-data="config.toml;." ^
    moodleeditor.py
