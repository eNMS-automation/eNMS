def allowed_file(name, webpage):
    # allowed extensions depending on the webpage
    allowed_extensions = {'nodes': {'xls', 'xlsx'}, 'netmiko': {'yaml'}}
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions[webpage]
    return allowed_syntax and allowed_extension