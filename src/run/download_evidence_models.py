"""Download only selected pinned models, instead of the entire legacy model list."""
import argparse
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", action="append", required=True)
    p.add_argument("--cache-dir", type=Path,
                   default=Path(os.environ.get("HF_HOME", "/workspace/hf")) / "hub")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    import yaml
    root = Path(__file__).resolve().parents[2]
    models = {m["id"]: m for m in yaml.safe_load((root / "configs/models.yaml").read_text())["models"]}
    if len(set(args.model)) != len(args.model) or set(args.model) - set(models):
        p.error("duplicate or unknown model IDs")
    if not args.dry_run:
        from huggingface_hub import snapshot_download
    for name in args.model:
        cfg = models[name]
        print(f"{name}: {cfg['repo']} @ {cfg['revision']}", flush=True)
        if not args.dry_run:
            path = snapshot_download(repo_id=cfg["repo"], revision=cfg["revision"],
                                     cache_dir=str(args.cache_dir))
            print(f"Ready: {path}", flush=True)


if __name__ == "__main__":
    main()
