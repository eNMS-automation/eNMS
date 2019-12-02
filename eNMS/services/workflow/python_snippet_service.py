from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import PythonField
from eNMS.models.automation import Service


class PythonSnippetService(Service):

    __tablename__ = "python_snippet_service"
    pretty_name = "Python Snippet"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    source_code = Column(LargeString)

    __mapper_args__ = {"polymorphic_identity": "python_snippet_service"}

    def job(self, run, payload, device=None):

        try:
            code_object = compile(run.source_code, "user_python_code", "exec")
        except Exception as exc:
            run.log("info", f"Compile error: {str(exc)}")
            return {"success": False, "result": {"step": "compile", "error": str(exc)}}
        result = {}

        class TerminateException(Exception):
            pass

        def save_result(success, result, **kwargs):
            result.update({"success": success, "result": result, **kwargs})
            if kwargs.get("exit"):
                raise TerminateException()

        globals = {
            "__builtins__": __builtins__,
            "result": result,
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
                "result": {"step": "execute", "error": str(exc), "result": result},
            }

        return {"result": result}


class PythonSnippetForm(ServiceForm):
    form_type = HiddenField(default="python_snippet_service")
    source_code = PythonField(
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
