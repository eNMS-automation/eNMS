from flask_assets import Bundle

base_js_bundle = Bundle("modules/base/**/*.min.js", output="bundles/base.js")

base_css_bundle = Bundle(
    "modules/base/3_bootstrap/css/bootstrap.min.css",
    "modules/base/**/*.css",
    "modules/base/base.min.css",
    output="bundles/base.css",
)
