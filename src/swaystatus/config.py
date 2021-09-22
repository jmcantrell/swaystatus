import os
import sys
import toml
from pathlib import Path
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec


class Config:
    def __init__(self):
        self.directory = (
            Path(
                os.environ.get(
                    "XDG_CONFIG_HOME", Path("~/.config").expanduser()
                )
            )
            / "swaystatus"
        )

        self.file = self.directory / "config.toml"

    def load(self):
        data = (
            toml.loads(open(self.file).read()) if self.file.is_file() else {}
        )

        self.interval = data.get("interval", 1)

        modules_path = [self.directory / "modules"]
        modules_path.extend(data.get("modules_path", []))

        packages = []

        for i, modules_dir in enumerate(modules_path):
            package_name = f"modules{i}"
            package_init_file = Path(modules_dir) / "__init__.py"
            if package_init_file.is_file():
                spec = spec_from_file_location(package_name, package_init_file)
                if spec:
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    spec.loader.exec_module(package)
                    packages.append(package_name)

        self.elements = []

        for module_name in data.get("modules_order", []):
            for package_name in packages:
                try:
                    module = import_module(f"{package_name}.{module_name}")
                except ModuleNotFoundError:
                    continue
                module_config = data.get("modules", {}).get(module_name, {})
                element = module.Element(**module_config)
                element.name = module_name
                self.elements.append(element)
                break
            else:
                raise ModuleNotFoundError(
                    f"No module named '{module_name}' in any modules package"
                )
