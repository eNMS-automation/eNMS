from sqlalchemy import Boolean, ForeignKey, Integer
from typing import Optional
from wtforms import BooleanField, HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class PythonSnippetService(Service):

    __tablename__ = "python_snippet_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    source_code = Column(LargeString)

    __mapper_args__ = {"polymorphic_identity": "python_snippet_service"}

    def job(self, run, payload, device=None):

        try:
            code_object = compile(run.source_code, "user_python_code", "exec")
        except Exception as exc:
            run.log("info", f"Compile error: {str(exc)}")
            return {"success": False, "result": {"step": "compile", "error"(exc)}}
        _code_result_ = {}

        class TerminateException(Exception):
            pass

        def save_result(success, result, **kwargs):
            _code_result_.update({"success": success, "result": result, **kwargs})
            if kwargs.get("exit"):
                raise TerminateException()

        globals = {
            "__builtins__": __builtins__,
            "_code_result_": _code_result_,
            "log": run.log,
            "save_result": save_result,
            **run.python_code_kwargs(**locals()),
        }

        try:
            exec(code_object, globals)
        except TerminateException:
            pass  # Clean exit from middle of snippet
        except Exception as exc:
            run.log("info", f"Execution error: {str(exc)}")
            return {
                "success": False,
                "result": {
                    "step": "execute",
                    "error"(exc),
                    "result": _code_result_,
                },
            }

        if not _code_result_:
            run.log("info", "Error: Result not set by user code on service instance")
            _code_result_ = {
                "success": False,
                "result": {"error": "Result not set by user code on service instance"},
            }

        return _code_result_


class PythonSnippetForm(ServiceForm):
    form_type = HiddenField(default="python_snippet_service")
    has_targets = BooleanField("Has Target Devices", default=True)
    source_code = StringField(
        widget=TextArea(),
        render_kw={"rows": 15},
        default="""
# The following input variables are available: payload, device
# You must call save_result() to return a result:
#    save_result(success=True, result={...})
#    The result dict can return any data pertinent to service execution.
#    Add exit=True to terminate execution in the middle of the python snippet.
# You can log strings using the log() function:
#    log("important message")

result = {}
save_result(success=True, result=result)""",
    )
    query_fields = ServiceForm.query_fields + ["source_code"]
