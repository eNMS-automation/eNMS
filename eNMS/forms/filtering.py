from wtforms import HiddenField, SelectField

from eNMS.forms import BaseForm
from eNMS.forms.fields import MultipleInstanceField
from eNMS.models import model_properties, relationships


def filtering_form_generator():
    for form_type, properties in model_properties.items():
        relations = {}
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
                "properties": sorted(relations),
                "form_type": HiddenField(default=f"{form_type}_filtering"),
                **{
                    **relations,
                    **{
                        f"{relation}_filter": SelectField(
                            choices=(
                                ("any", "Any"),
                                ("not_any", "Unrelated"),
                                ("none", "None"),
                            )
                        )
                        for relation in relations
                    },
                },
            },
        )


filtering_form_generator()
