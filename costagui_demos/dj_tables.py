import datajoint as dj

lab = dj.create_virtual_module('lab', 'costa_lab')
subject = dj.create_virtual_module('subject', 'costa_subject')
action = dj.create_virtual_module('action', 'costa_action')
surgery = dj.create_virtual_module('surgery', 'costa_surgery')
acquisition = dj.create_virtual_module('acquisition', 'costa_acquisition')
hardware = dj.create_virtual_module('hardware', 'costa_hardware')
virus = dj.create_virtual_module('virus', 'costa_virus')
