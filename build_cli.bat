pyinstaller --noconfirm --log-level=WARN ^
    --clean ^
	--icon=".\res\moodle.ico" ^
	--console ^
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
	moodle2pdf_cli.py
