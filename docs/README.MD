To build the docs:

- `cd docs` 
- `mkdocs build` 
- Note: output will be in the `docs/build` folder
 
To serve the docs locally (http://127.0.0.1:8000) 

- `cd docs` 
- `mkdocs serve --dev-addr 0.0.0.0:8000`  
- Note: You can change your `setup/settings.json` (`documentation_url": "http://localhost:8000/"`) if desired.

For more information on mkdocs, refer to: 

- https://www.mkdocs.org/
- https://github.com/mkdocs/mkdocs/wiki/MkDocs-Themes
- https://squidfunk.github.io/mkdocs-material/
