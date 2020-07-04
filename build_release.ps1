
# clear build directories
Remove-Item -LiteralPath "dist" -Force -Recurse
Remove-Item -LiteralPath "build" -Force -Recurse

# build all subprojects
cmd.exe /c "build_cli.bat"
cmd.exe /c "build_gui.bat"
cmd.exe /c "build_editor.bat"

# create directories for each project
mkdir dist\moodle2pdf_cli
mkdir dist\moodle2pdf_gui\translate\
mkdir dist\moodleeditor\translate\

# put config file and executable into directory
copy config.toml dist\moodle2pdf_cli
copy config.toml dist\moodle2pdf_gui
copy config.toml dist\moodleeditor
copy translate\*.qm dist\moodle2pdf_gui\translate\
copy translate\*.qm dist\moodleeditor\translate\
move dist\moodle2pdf_cli.exe dist\moodle2pdf_cli
move dist\moodle2pdf_gui.exe dist\moodle2pdf_gui
move dist\moodleeditor.exe dist\moodleeditor

# zip each directory
Compress-Archive -Path dist\moodle2pdf_cli -DestinationPath dist\moodle2pdf_cli.zip
Compress-Archive -Path dist\moodle2pdf_gui -DestinationPath dist\moodle2pdf_gui.zip
Compress-Archive -Path dist\moodleeditor -DestinationPath dist\moodleeditor.zip
