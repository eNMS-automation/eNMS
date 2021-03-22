from copy import deepcopy
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm, form_properties
from eNMS.forms.fields import (
    HiddenField,
    MultipleInstanceField,
    SelectField,
    StringField,
)
from eNMS.models import relationships


def filtering_form_generator():
    for model in ("device", "link", "pool", "run", "service", "task", "user"):
        properties, relations = app.properties["filtering"].get(model, []), {}
        for related_model, relation in relationships[model].items():
            if related_model in ("edges", "results"):
                continue
            relations[related_model] = MultipleInstanceField(related_model)
            relationships[f"{model}_filtering"][related_model] = relation
            relationships[f"{model}_relation_filtering"][related_model] = relation
        relation_form = {
            "template": "filtering",
            "properties": sorted(relations),
            "object_type": model,
            "form_type": HiddenField(default=f"{model}_relation_filtering"),
            **{
                **relations,
                **{
                    f"{relation}_filter": SelectField(
                        choices=(("any", "Any"), ("all", "All"))
                    )
                    for relation in relations
                },
            },
        }
        type(f"{model}RelationshipFilteringForm", (BaseForm,), relation_form)
        form, form_type = deepcopy(relation_form), f"{model}_filtering"
        for property in properties:
            form_properties[form_type][f"{property}_filter"] = {"type": "list"}
        form.update(
            {
                "form_type": HiddenField(default=form_type),
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
        type(f"{model}FilteringForm", (BaseForm,), form)


def add_instance_form_generator():
    for model in ("device", "link", "user", "service"):
        relationships[f"add_{model}s"]["instances"] = {
            "type": "object-list",
            "model": model,
        }
        type(
            f"{model}RelationshipFilteringForm",
            (BaseForm,),
            {
                "form_type": HiddenField(default=f"add_{model}s"),
                "action": "eNMS.base.addInstancesToRelation",
                "model": HiddenField(default=model),
                "relation_id": HiddenField(),
                "relation_type": HiddenField(),
                "property": HiddenField(),
                "instances": MultipleInstanceField(f"{model}s", model=model),
                "names": StringField(widget=TextArea(), render_kw={"rows": 8}),
            },
        )


filtering_form_generator()
add_instance_form_generator()
