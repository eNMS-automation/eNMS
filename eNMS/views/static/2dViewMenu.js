var action = {
  'Parameters': partial(showModal, 'filters'),
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Add new task': partial(showModal, 'scheduling'),
  'Open Street Map': partial(switch_layer, 'osm'),
  'Google Maps': partial(switch_layer, 'gm'),
  'NASA': partial(switch_layer, 'nasa')
}