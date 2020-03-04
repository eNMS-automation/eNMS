from copy import deepcopy

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    HiddenField,
    MultipleInstanceField,
    SelectField,
    StringField,
)
from eNMS.models import models, relationships


def filtering_form_generator():
    for form_type in models:
        properties, relations = app.properties["filtering"].get(form_type, []), {}
        for model, relation in relationships[form_type].items():
            if model in ("edges", "results"):
                continue
            relations[model] = MultipleInstanceField(model)
            relationships[f"{form_type}_filtering"][model] = relation
            relationships[f"{form_type}_relation_filtering"][model] = relation
        relation_form = {
            "template": "filtering",
            "properties": sorted(relations),
            "form_type": HiddenField(default=f"{form_type}_relation_filtering"),
            **{
                **relations,
                **{
                    f"{relation}_filter": SelectField(
                        choices=(
                            ("any", "Any"),
                            ("all", "All"),
                            ("not_any", "Unrelated"),
                            ("none", "None"),
                        )
                    )
                    for relation in relations
                },
            },
        }
        type(f"{form_type}RelationshipFilteringForm", (BaseForm,), relation_form)
        form = deepcopy(relation_form)
        form.update(
            {
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
            }
        )
        type(f"{form_type}FilteringForm", (BaseForm,), form)


filtering_form_generator()
