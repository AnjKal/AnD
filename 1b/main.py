#!/usr/bin/env python3
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from optimized_utils import process_documents

def main():
    parser = argparse.ArgumentParser(
        description='Optimized Document Analysis System using BGE-small',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing input.json and pdfs/ folder (default: data)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory to save output JSON (default: output)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of top sections to include in the analysis (default: 10)'
    )
    
    args = parser.parse_args()
    
    try:
        # Process documents using the optimized pipeline
        process_documents(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            top_n=args.top_n
        )
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
