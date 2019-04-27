from flask import Flask
from sqlalchemy.orm import Session


class Controller:
    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session

    @contextmanager
    def session_scope(self) -> Generator:
        session = self.session()  # type: ignore
        try:
            yield session
            session.commit()
        except Exception as e:
            info(str(e))
            session.rollback()
            raise e
        finally:
            self.session.remove()

    def str_dict(self, input: Any, depth: int = 0) -> str:
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.str_dict(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.str_dict(value, depth + 1)}"
            return result
        else:
            return str(input)

    def strip_all(self, input: str) -> str:
        return input.translate(str.maketrans("", "", f"{punctuation} "))


controller = Controller()
