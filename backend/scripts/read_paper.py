"""Read one scanned paper from the command line and show what GLM-OCR found.

    python -m scripts.read_paper path/to/zikra.pdf
    python -m scripts.read_paper path/to/zikra.pdf --save-layers layers/

Prints every page with a [PRINTED] part and a [HANDWRITTEN] part. With
--save-layers it also writes the two ink layers as PNG files, so you can see
exactly what each OCR call was given. Needs `ollama serve` and `ollama pull glm-ocr`.
"""

import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag import loaders  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path)
    parser.add_argument("--save-layers", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="write the text here as well")
    args = parser.parse_args()

    pages = loaders.read_pages([{"path": str(args.file), "name": args.file.name}], separate_ink=True)

    if args.save_layers:
        args.save_layers.mkdir(parents=True, exist_ok=True)
        for page in pages:
            layers = page.get("layers")
            if not layers:
                continue
            number = page["page"]
            (args.save_layers / f"page{number:02d}_printed.png").write_bytes(
                base64.b64decode(layers.printed_b64)
            )
            if layers.handwritten_b64:
                (args.save_layers / f"page{number:02d}_handwritten.png").write_bytes(
                    base64.b64decode(layers.handwritten_b64)
                )
            print(f"page {number}: {layers.handwriting_pixels} pen pixels, {layers.red_pixels} red-pen pixels")

    text, flags = loaders.run_ocr(pages, "script")
    print(text)
    for flag in flags:
        print(f"[note] {flag}", file=sys.stderr)
    if args.out:
        args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
