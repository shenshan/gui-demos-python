# %%
import datajoint as dj
from costagui_demos.dj_tables import *
from costagui_demos.app import app
from dj_dashboard.templates import TableBlock

# %%
surgery_table_tab = TableBlock(
    surgery.Surgery, app,
    extra_tables=[surgery.Surgery.Implant,
                  surgery.Surgery.Injection,
                  surgery.Surgery.Pipette])


if __name__ == '__main__':
    dj.config['safemode'] = False
    app.layout = surgery_table_tab.layout
    app.run_server(debug=True)

# %%
