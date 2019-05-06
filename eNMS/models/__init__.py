from collections import defaultdict
from typing import Dict

models = {}
relationships = defaultdict(dict)

model_properties = defaultdict(list)
property_types: Dict[str, str] = {}
