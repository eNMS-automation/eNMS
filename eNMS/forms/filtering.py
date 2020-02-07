from collections import OrderedDict
from wtforms import HiddenField, SelectField, StringField

from eNMS.forms import BaseForm
from eNMS.forms.fields import MultipleInstanceField
from eNMS.models import model_properties, relationships
from eNMS.properties import private_properties


def filtering_form_generator():
    for form_type, properties in model_properties.items():
        relations = {}
        properties = list(
            OrderedDict.fromkeys(
                p for p in properties if p not in private_properties + ["type", "id"]
            )
        )
        for model, relation in relationships[form_type].items():
            if model in ("edges", "results"):
                continue
            relations[model] = MultipleInstanceField(model)
            relationships[f"{form_type}_filtering"][model] = relation
        type(
            f"{form_type.capitalize()}FilteringForm",
            (BaseForm,),
            {
                "template": "filtering",
                "properties": sorted(properties) + sorted(relations),
                "form_type": HiddenField(default=f"{form_type}_filtering"),
                "operator": SelectField(
                    "Type of match",
                    choices=(
                        ("all", "Match if all properties match"),
                        ("any", "Match if any property matches"),
                    ),
                ),
                **{
                    **{property: StringField() for property in properties},
                    **{
                        f"{property}_filter": SelectField(
                            choices=(
                                ("inclusion", "Inclusion"),
                                ("equality", "Equality"),
                                ("regex", "Regular Expression"),
                            )
                        )
                        for property in properties
                    },
                    **relations,
                    **{
                        f"{relation}_filter": SelectField(
                            choices=(
                                ("any", "Any"),
                                ("not_any", "Not related to Any"),
                                ("none", "None"),
                            )
                        )
                        for relation in relations
                    },
                },
            },
        )


filtering_form_generator()
