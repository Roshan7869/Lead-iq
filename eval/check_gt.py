#!/usr/bin/env python3
"""Check ground_truth.json structure"""
import json

data = json.load(open('eval/ground_truth.json'))
sources = {}
for g in data:
    src = g['source']
    sources[src] = sources.get(src, 0) + 1

print(f'Total records: {len(data)}')
print(f'Source counts: {sources}')

# Check hacker_news entries
hn_entries = [g for g in data if g['source'] == 'hacker_news']
if hn_entries:
    print(f'\nhacker_news entries: {len(hn_entries)}')
    for e in hn_entries[:3]:
        print(f'  - {e["id"]}: {e["expected"]["company_name"]} (min_conf: {e["expected"]["confidence_min"]})')
