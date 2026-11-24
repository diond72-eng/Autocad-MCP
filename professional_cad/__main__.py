"""Headless CLI with the same entry points as the optional MCP sidecar."""
import argparse
import json
from pathlib import Path

from .model import Project
from .project import generate
from .qa import signature, verify


def main():
    parser=argparse.ArgumentParser(prog="professional-cad")
    commands=parser.add_subparsers(dest="command",required=True)
    p=commands.add_parser("generate")
    p.add_argument("input",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--no-proofs",action="store_true")
    commands.add_parser("schema")
    p=commands.add_parser("validate")
    p.add_argument("output",type=Path)
    p=commands.add_parser("compare")
    p.add_argument("reference",type=Path)
    p.add_argument("candidate",type=Path)
    args=parser.parse_args()
    if args.command=="schema":
        result=Project.model_json_schema()
    elif args.command=="generate":
        result=generate(Project.model_validate_json(args.input.read_bytes()),args.output,not args.no_proofs)
    elif args.command=="validate":
        result=verify(args.output)
    else:
        a,b=signature(args.reference),signature(args.candidate)
        result={"match":a==b,"reference_sheets":len(a),"candidate_sheets":len(b),
                "changed_pages":[i for i,(u,v) in enumerate(zip(a,b),1) if u!=v]}
        print(json.dumps(result,indent=2))
        return 0 if result["match"] else 1
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
