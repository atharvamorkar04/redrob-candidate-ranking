import json
import gzip

def stream_candidates(jsonl_path: str):
    """
    Streams candidates from a JSON-lines (.jsonl, .json) or GZipped file.
    Robustly handles both JSON arrays (loaded in memory) and JSON-lines formats (streamed).
    """
    import os
    jsonl_path = os.path.abspath(jsonl_path)
    open_fn = gzip.open if jsonl_path.endswith('.gz') else open
    mode = 'rt' if jsonl_path.endswith('.gz') else 'r'
    
    # Read the first non-empty character to check if it's a JSON array
    first_char = ''
    with open_fn(jsonl_path, mode, encoding='utf-8-sig') as f:
        for line in f:
            line_strip = line.strip()
            if line_strip:
                first_char = line_strip[0]
                break
                
    if first_char == '[':
        # Load as standard JSON array (safe for smaller files like sample_candidates.json)
        with open_fn(jsonl_path, mode, encoding='utf-8-sig') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
    else:
        # Stream line-by-line (JSON-lines)
        with open_fn(jsonl_path, mode, encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


