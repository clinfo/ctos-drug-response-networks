from pathlib import Path

CANONICAL_DRUGS = {
    "ldn193189": "LDN193189",
    "ldn-193189": "LDN193189",
    "cetuximab": "cetuximab",
    "trametinib": "trametinib",
    "xav939": "XAV939",
    "gdc0941": "GDC0941",
    "gdc-0941": "GDC0941",
    "pre": "pretreatment",
    "pretreatment": "pretreatment",
    "before drug administration": "pretreatment",
}

FIGURE_FAMILIES = ["fig2", "fig3", "fig4", "fig5", "fig6"]

TEXT_FILE_SUFFIXES = {
    ".md", ".txt", ".py", ".sh", ".R", ".yaml", ".yml", ".json", ".tsv", ".csv", ".cff", ".toml"
}

METADATA_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    ".zenodo.json",
    "RELEASE_CHECKLIST.md",
]
