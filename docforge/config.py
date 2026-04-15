import os

import yaml


class SourceConfig:
    def __init__(self, name, patterns, base_dir=".", exclude=None, max_chars=50000):
        self.name = name
        self.patterns = patterns
        self.base_dir = base_dir
        self.exclude = exclude if exclude is not None else []
        self.max_chars = max_chars


class DocConfig:
    def __init__(self, doc_id, output, title, prompt_template, sources,
                 sidebar_position=1, extra_context=None):
        self.id = doc_id
        self.output = output
        self.title = title
        self.prompt_template = prompt_template
        self.sources = sources
        self.sidebar_position = sidebar_position
        self.extra_context = extra_context if extra_context is not None else {}


class AuthConfig:
    def __init__(self, enabled=True, method="token", token_hashes=None):
        self.enabled = enabled
        self.method = method
        self.token_hashes = token_hashes if token_hashes is not None else []


class SiteConfig:
    def __init__(self, title="Dev Docs", url="", base_url="/",
                 github_user="", repo_name="", locale="ru", no_index=True):
        self.title = title
        self.url = url
        self.base_url = base_url
        self.github_user = github_user
        self.repo_name = repo_name
        self.locale = locale
        self.no_index = no_index


class ProjectConfig:
    def __init__(self, project_name, description="", model="gemini-2.5-flash",
                 output_dir="docs/dev", docusaurus_dir="docs-site",
                 sources=None, docs=None, auth=None, site=None,
                 system_prompt=""):
        self.project_name = project_name
        self.description = description
        self.model = model
        self.output_dir = output_dir
        self.docusaurus_dir = docusaurus_dir
        self.sources = sources if sources is not None else []
        self.docs = docs if docs is not None else []
        self.auth = auth if auth is not None else AuthConfig()
        self.site = site if site is not None else SiteConfig()
        self.system_prompt = system_prompt

    @classmethod
    def from_file(cls, path):
        config_path = str(path)

        if not os.path.exists(config_path):
            raise IOError(
                "Configuration not found: %s\n"
                "Run: docforge init" % config_path
            )

        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        sources = [
            SourceConfig(**s) for s in raw.get("sources", [])
        ]

        docs = []
        for d in raw.get("docs", []):
            doc_data = dict(d)
            if "id" in doc_data:
                doc_data["doc_id"] = doc_data.pop("id")
            docs.append(DocConfig(**doc_data))

        auth = AuthConfig(**raw.get("auth", {}))
        site = SiteConfig(**raw.get("site", {}))

        return cls(
            project_name=raw["project_name"],
            description=raw.get("description", ""),
            model=raw.get("model", "gemini-2.5-flash"),
            output_dir=raw.get("output_dir", "docs/dev"),
            docusaurus_dir=raw.get("docusaurus_dir", "docs-site"),
            sources=sources,
            docs=docs,
            auth=auth,
            site=site,
            system_prompt=raw.get("system_prompt", ""),
        )
