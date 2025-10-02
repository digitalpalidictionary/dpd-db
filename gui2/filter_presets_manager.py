import json

from gui2.toolkit import ToolKit

PresetData = dict[str, list | int]


class FilterPresetsManager:
    def __init__(self, toolkit: ToolKit) -> None:
        self.paths = toolkit.paths
        self.presets_path = self.paths.filter_presets_path
        self.presets: dict[str, PresetData] = self.load_presets()

    def load_presets(self) -> dict[str, PresetData]:
        try:
            with open(self.presets_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_presets(self) -> None:
        with open(self.presets_path, "w") as f:
            json.dump(self.presets, f, ensure_ascii=False, indent=4)

    def save_preset(
        self,
        name: str,
        data_filters: list[list[str]],
        display_filters: list[str],
        limit: int,
    ) -> None:
        self.presets[name] = {
            "data_filters": data_filters,
            "display_filters": display_filters,
            "limit": limit,
        }
        self.save_presets()

    def delete_preset(self, name: str) -> None:
        if name in self.presets:
            del self.presets[name]
            self.save_presets()

    def get_preset(self, name: str) -> PresetData | None:
        return self.presets.get(name)

    def list_presets(self) -> list[str]:
        return list(self.presets.keys())

    def get_first_preset(self) -> PresetData | None:
        if self.presets:
            first_preset_name = next(iter(self.presets))
            return self.get_preset(first_preset_name)
        return None

    def get_first_preset_name(self) -> str | None:
        if self.presets:
            return next(iter(self.presets))
        return None
