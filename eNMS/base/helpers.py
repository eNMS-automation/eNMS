from sqlalchemy import exc


from eNMS import db


def get_obj(model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


def integrity_rollback(function):
    def wrapper(*a, **kw):
        try:
            function(*a, **kw)
        except exc.IntegrityError:
            db.session.rollback()
    return wrapper


def str_dict(input, depth=0):
    tab = '\t' * depth
    if isinstance(input, list):
        result = '\n'
        for element in input:
            result += '{}- {}\n'.format(tab, str_dict(element, depth + 1))
        return result
    elif isinstance(input, dict):
        result = ''
        for key, value in input.items():
            result += '\n{}{}: {}'.format(tab, key, str_dict(value, depth + 1))
        return result
    else:
        return str(input)


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension
