"""Executa e salva os notebooks que compõem a evidência da entrega."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOKS = (
    Path("notebooks/01_eda.ipynb"),
    Path("notebooks/02_baseline_vs_bandit.ipynb"),
)


def main() -> None:
    root = Path.cwd()
    for path in NOTEBOOKS:
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(
            notebook,
            timeout=600,
            kernel_name="python3",
            resources={"metadata": {"path": str(root)}},
        )
        client.execute()
        nbformat.write(notebook, path)
        print(f"Notebook executado: {path}")


if __name__ == "__main__":
    main()
