from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class ClaudeCodeSettings(BaseSettings):
    """Configuration to set the CLI options available in Claude Code."""

    allowed_tools: list[str] = Field(default_factory=list)
    model: str | None = None
    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "doctest-ai", "claude-code"),
        extra="forbid",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)
