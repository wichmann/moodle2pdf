pyinstaller --noconfirm  --log-level=WARN ^
    --clean --windowed ^
	--icon=".\res\moodle.ico" ^
	--onefile ^
	--hidden-import reportlab.graphics.barcode.common ^
	--hidden-import reportlab.graphics.barcode.code128 ^
	--hidden-import reportlab.graphics.barcode.code93 ^
	--hidden-import reportlab.graphics.barcode.code39 ^
	--hidden-import reportlab.graphics.barcode.usps ^
	--hidden-import reportlab.graphics.barcode.usps4s ^
	--hidden-import reportlab.graphics.barcode.qr ^
	--hidden-import reportlab.graphics.barcode.widgets ^
	--hidden-import reportlab.graphics.barcode.eanbc ^
	--hidden-import reportlab.graphics.barcode.ecc200datamatrix ^
	--hidden-import reportlab.graphics.barcode.fourstate ^
	--hidden-import reportlab.graphics.barcode.lto ^
	--add-data="moodle2pdf.ui;." ^
	--add-data="res;res\." ^
	--add-data="config.toml;." ^
	--exclude-module tkinter ^
	--exclude-module PyQt5.QtDesigner ^
	--exclude-module PyQt5.QtMultimedia ^
	--exclude-module PyQt5.QtMultimediaWidgets ^
	--exclude-module PyQt5.QtNetwork ^
	--exclude-module PyQt5.QtBluetooth ^
	--exclude-module PyQt5.QtPrintSupport ^
	--exclude-module PyQt5.QtNetworkAuth ^
	--exclude-module PyQt5.QtNfc ^
	--exclude-module PyQt5.QtQml ^
	--exclude-module PyQt5.QtSql ^
	--exclude-module PyQt5.QtQuick ^
	--exclude-module PyQt5.QtSensors ^
	--exclude-module PyQt5.QtSerialPort ^
	--exclude-module PyQt5.QtXml ^
	--exclude-module PyQt5.QtXmlPatterns ^
	--exclude-module PyQt5.QtQuickWidgets ^
	--exclude-module PyQt5.QtOpenGL ^
	--exclude-module PyQt5.QtHelp ^
	--exclude-module PyQt5.QtDBus ^
	--exclude-module PyQt5.QtLocation ^
	moodle2pdf_gui.py
