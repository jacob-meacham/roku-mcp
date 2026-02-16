"""Application configuration and settings, loaded from config.yml."""

import os
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

CONFIG_FILE = Path(os.environ.get("ROKU_MCP_CONFIG", "config.yml"))


class ServerConfig(BaseModel):
    """Server settings."""

    host: str = "0.0.0.0"
    port: int = 8080


class DeviceConfig(BaseModel):
    """A single Roku device."""

    name: str = "Roku"
    ip: str = "192.168.1.100"


class Settings(BaseSettings):
    """Application settings loaded from config.yml with env var overrides."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    devices: list[DeviceConfig] = Field(default_factory=lambda: [DeviceConfig()])

    model_config = {
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        from pydantic_settings import YamlConfigSettingsSource

        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=CONFIG_FILE),
        )

    def get_device(self, name: str | None = None) -> DeviceConfig:
        """Resolve a device by name, defaulting to the first configured device."""
        if name is None:
            return self.devices[0]
        for device in self.devices:
            if device.name == name:
                return device
        msg = f"Device not found: {name}"
        raise ValueError(msg)
