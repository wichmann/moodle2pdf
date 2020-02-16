
# Moodle2PDF & MoodleEditor

## Description

Creates a PDF file from Moodle glossar data exported into XML files. All XML files in the local directory will be converted. You can select if each XML file should be converted into a separate PDF or if all data from all files should be converted into one big PDF file.

## Usage

    ./moodle2pdf_cli.py

    ./moodle2pdf_gui.py

    ./moodleeditor.py

## License

moodle2pdf is released under the GNU General Public License v2 or newer.

Some icons are from the Breeze theme under Ubuntu Linux.

## Requirements

* BeautifulSoup4 for parsing the XML data
* Reportlab for creating PDF files
* Requests library for sending HTTP requests
