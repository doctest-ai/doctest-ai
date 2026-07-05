from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

from doctest_ai.agent import DEFAULT_DISALLOWED_TOOLS


class Settings(BaseSettings):
    """Configuration that is not specific to the agent for execution."""

    max_retries: int | None = None
    reps: int | None = None
    arms: list[str] | None = None
    artifact: str | None = None
    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "doctest-ai"), extra="ignore"
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
        return init_settings, PyprojectTomlConfigSettingsSource(settings_cls)


class ClaudeCodeSettings(BaseSettings):
    """Configuration to set the CLI options available in Claude Code."""

    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(
        default_factory=lambda: list(DEFAULT_DISALLOWED_TOOLS)
    )
    model: str | None = None
    max_turns: int | None = None
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
        return init_settings, PyprojectTomlConfigSettingsSource(settings_cls)
