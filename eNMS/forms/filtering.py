from wtforms import HiddenField, SelectField, StringField

from eNMS.forms import BaseForm, form_properties
from eNMS.forms.fields import MultipleInstanceField
from eNMS.models import relationships
from eNMS.properties.table import filtering_properties


def filtering_form_generator():
    for table, properties in filtering_properties.items():
        relations = {}
        for model, relation in relationships[table].items():
            if model in ("edges", "results"):
                continue
            relations[model] = MultipleInstanceField(model)
            relationships[f"{table}_filtering"][model] = relation
        type(
            f"{table.capitalize()}FilteringForm",
            (BaseForm,),
            {
                "template": "filtering",
                "properties": list(relations) + properties,
                "form_type": HiddenField(default=f"{table}_filtering"),
                "operator": SelectField(
                    "Match Condition",
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
                            choices=(("any", "Any"), ("not_any", "Not related to Any"))
                        )
                        for relation in relations
                    },
                },
            },
        )


filtering_form_generator()
