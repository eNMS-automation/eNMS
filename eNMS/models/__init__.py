from collections import defaultdict
from typing import Dict

classes = {}
service_classes = {}
relationships = defaultdict(dict)

cls_to_properties = defaultdict(list)
property_types: Dict[str, str] = {}
