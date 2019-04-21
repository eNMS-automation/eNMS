from contextlib import contextmanager
from flask import Flask
from sqlalchemy.orm import Session

from eNMS.framework import delete


class Controller:
    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session

    @contextmanager
    def session_scope() -> Generator:
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

    def delete_instance(self, cls, instance_id):
        instance = delete(cls, id=id)
        info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
        return instance


controller = Controller()
