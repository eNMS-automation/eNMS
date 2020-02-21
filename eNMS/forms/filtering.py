from wtforms import HiddenField, SelectField, StringField

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
            form = {
                "template": "filtering",
                "properties": sorted(relations),
                "form_type": HiddenField(default=f"{form_type}_relation_filtering"),
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
            }
        type(f"{form_type}RelationshipFilteringForm", (BaseForm,), form)
        form.update({
            "form_type": HiddenField(default=f"{form_type}_filtering"),
            "properties": sorted(properties) + sorted(relations),
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
        })
        type(f"{form_type}FilteringForm", (BaseForm,), form)


filtering_form_generator()
