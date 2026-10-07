import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "embed", "gate", "dev", "validation", "freeze", "final", "reproduce", "diagnostics", "scaling", "report"])
    args = parser.parse_args()
    from .common import OUT
    if args.stage not in ("report", "reproduce") and (OUT / "final-started.json").exists():
        raise RuntimeError("This run is sealed; use a new evidence directory for an independent fixed-config replay")
    if args.stage in ("prepare", "embed"):
        from . import data
        getattr(data, args.stage)()
    elif args.stage in ("gate", "scaling"):
        from . import topology_study
        getattr(topology_study, args.stage)()
    else:
        from . import experiment
        getattr(experiment, args.stage)()


if __name__ == "__main__":
    main()
