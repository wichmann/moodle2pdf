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
	moodle2pdf_gui.py
