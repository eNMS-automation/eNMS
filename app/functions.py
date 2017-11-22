def handle_uploaded_file(f):
    for chunk in f.chunks():
        print(chunk)