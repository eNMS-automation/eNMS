# Contributing

## Environment

eNMS uses:

-   Black for python code formatting.
-   Flake8 to make sure that the python code is PEP8-compliant.
-   Prettier for javascript code formatting.
-   Eslint to make sure the javascript code is compliant with google
    standards for javascript.

There is a dedicated `requirements_dev.txt` file to install these python
libraries:

    pip install -r requirements_dev.txt

## Pull Requests

Before opening a pull request with changes, one should make sure
that:

1. Candidate Python code is:

    - Black compliant

        Black is a code formatting enforcement tool. Once installed (see 
        [their repository](https://github.com/psf/black) for details), compliance
        can be verified with the following command:
        
        `black --check --verbose`

    - PEP8 (flake8) compliant
    
        `flake8 --config build/linting/.flake8`

2. Candidate Javascript code is:

    - Prettier compliant
    
        `npm run prettier`

    - ESLint compliant

        `npm run lint`

# Documentation

Concerning documentation updates, one can build a local version of
the docs like so:

```
mkdocs html
```

If mkdocs is already initialized in one's environment, the following command
will launch a local documentation server:

```
mkdocs serve
```

This server will automatically update and refresh whenever any filesystem
changes are made in the `enms/docs` folder or `mkdocs.yml`
