import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "embed", "gate", "dev", "validation", "freeze", "final", "diagnostics", "scaling", "report"])
    args = parser.parse_args()
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
