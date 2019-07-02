from collections import defaultdict
from typing import Dict

models: dict = {}
relationships: defaultdict = defaultdict(dict)
model_properties: defaultdict = defaultdict(list)
property_types: Dict[str, str] = {}
