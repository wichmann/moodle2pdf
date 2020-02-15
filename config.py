
import datetime

import toml
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4


with open('config.toml') as f:
    CONFIG = toml.loads(f.read())


PAGE_WIDTH, PAGE_HEIGHT = A4
BORDER_HORIZONTAL = CONFIG['pdf']['border_horizontal']*cm
BORDER_VERTICAL = CONFIG['pdf']['border_vertical']*cm
TODAY = datetime.datetime.today().strftime('%d.%m.%Y')
