#!/usr/bin/env python3
"""Refresh the public Markdown architecture gallery using existing catalogued images."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.import_architecture_templates import FAMILY,GALLERY,INDEX,generate_gallery,generate_index,read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='fail if generated Markdown needs refreshing')
    args=parser.parse_args()
    entries=[e for e in read(ROOT/'templates/catalog.json')['entries'] if e.get('family')==FAMILY]
    documents={e['file']:read(ROOT/e['file']) for e in entries}
    for name,data in ((INDEX,generate_index(entries,documents)),(GALLERY,generate_gallery(entries,documents))):
        path=ROOT/name
        if args.check:
            if not path.is_file() or path.read_bytes()!=data:
                raise SystemExit(f'Needs refresh: {name}')
        else:path.write_bytes(data)
    print(f"{'Checked' if args.check else 'Updated'} gallery: {len({e['slug'] for e in entries})} architectures")


if __name__=='__main__':main()
