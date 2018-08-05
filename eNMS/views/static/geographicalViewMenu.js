var action = {
  'Parameters': partial(showModal, 'filters'),
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Add new task': partial(showModal, 'scheduling'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa')
}