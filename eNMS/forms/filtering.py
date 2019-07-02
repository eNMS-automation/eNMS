from wtforms import HiddenField, SelectField, StringField

from eNMS.forms import BaseForm
from eNMS.forms.fields import MultipleInstanceField
from eNMS.models import relationships
from eNMS.properties.table import filtering_properties


def filtering_form_generator() -> None:
    print("tttt"*100, relationships)
    for table, properties in filtering_properties.items():
        kwargs = {}

        if table in ("device", "link", "configuration"):
            kwargs["pools"] = MultipleInstanceField("Pools", instance_type="Pool")
        if table == "service":
            kwargs["workflows"] = MultipleInstanceField(
                "Workflows", instance_type="Workflow"
            )
        if table == "workflow":
            kwargs["services"] = MultipleInstanceField(
                "Services", instance_type="Service"
            )
        type(
            f"{table.capitalize()}FilteringForm",
            (BaseForm,),
            {
                "template": "filtering",
                "properties": list(kwargs) + properties,
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
                    **kwargs,
                },
            },
        )


filtering_form_generator()
