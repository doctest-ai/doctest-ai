"""The docs under test — a first-class, swappable input.

A ``DocsSource`` is the thing varied between ablation arms. llms.txt, an MCP
docs server, and a mounted docs directory are interchangeable *delivery
methods* for it; ``NoDocs`` is the baseline arm that isolates model priors.

``apply(workspace)`` materializes the source into the task workspace and
returns a ``DocsSpec`` describing how the agent must be configured for it.
"""

from __future__ import annotations

import json
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class DocsSpec:
    """Agent-configuration contributions from a docs source."""

    prompt_preamble: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class DocsSource(Protocol):
    def apply(self, workspace: Path) -> DocsSpec: ...


@dataclass
class NoDocs:
    """Baseline arm: the agent gets nothing but its priors."""

    def apply(self, workspace: Path) -> DocsSpec:
        return DocsSpec()


@dataclass
class LLMsTxt:
    """An llms.txt-style file, fetched from a URL or copied from disk."""

    source: str
    filename: str = "llms.txt"

    def apply(self, workspace: Path) -> DocsSpec:
        target = workspace / self.filename
        if self.source.startswith(("http://", "https://")):
            with urllib.request.urlopen(self.source, timeout=60) as response:  # noqa: S310
                target.write_bytes(response.read())
        else:
            shutil.copyfile(self.source, target)
        return DocsSpec(
            prompt_preamble=(
                f"Documentation for the framework under use is provided in "
                f"./{self.filename}. Read it before writing any code, and "
                f"follow it over your prior knowledge wherever they disagree."
            ),
            allowed_tools=["Read"],
        )


@dataclass
class DocsDir:
    """A documentation directory copied into the workspace."""

    path: str
    dirname: str = "docs"

    def apply(self, workspace: Path) -> DocsSpec:
        target = workspace / self.dirname
        if not target.exists():
            shutil.copytree(self.path, target)
        return DocsSpec(
            prompt_preamble=(
                f"Documentation for the framework under use is available in "
                f"./{self.dirname}/. Consult it before writing any code, and "
                f"follow it over your prior knowledge wherever they disagree."
            ),
            allowed_tools=["Read", "Glob", "Grep"],
        )


@dataclass
class MCPDocs:
    """Docs served over MCP (e.g. mcpdoc pointing at a framework's llms.txt).

    ``servers`` is either a ``{name: config}`` dict in Claude Code's
    ``mcpServers`` shape, or a path to an ``mcp-servers.json`` file.
    """

    servers: dict[str, Any] | str
    instructions: str = ""

    def apply(self, workspace: Path) -> DocsSpec:
        if isinstance(self.servers, str):
            payload = json.loads(Path(self.servers).read_text())
            servers = payload.get("mcpServers", payload)
        else:
            servers = self.servers
        preamble = self.instructions or (
            "Documentation for the framework under use is available through "
            "the configured MCP documentation server. Consult it for ANY "
            "question about the framework before writing code, and follow it "
            "over your prior knowledge wherever they disagree."
        )
        return DocsSpec(
            prompt_preamble=preamble,
            allowed_tools=[f"mcp__{name}" for name in servers],
            mcp_servers=servers,
        )
