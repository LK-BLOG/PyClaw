#!/usr/bin/env python3
import os

for k, v in os.environ.items():
    if 'bili' in k.lower() or 'sess' in k.lower():
        print(f"{k}: {v[:10]}... (len {len(v)})")
