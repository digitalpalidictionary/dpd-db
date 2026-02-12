from jinja2 import Environment, FileSystemLoader

def get_jinja2_env(templates_dir: str) -> Environment:
    """Get a Jinja2 environment with standard settings."""
    return Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
