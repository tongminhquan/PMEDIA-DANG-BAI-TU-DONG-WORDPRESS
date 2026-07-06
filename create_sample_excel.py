from __future__ import annotations

from pathlib import Path


def main() -> int:
    try:
        import pandas as pd
        from PIL import Image, ImageDraw
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        print("Install dependencies with: python -m pip install -r requirements.txt")
        return 1

    data_dir = Path("data")
    image_dir = data_dir / "sample_images"
    image_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "ma_bai": "bai01",
            "title": "Bài demo 01",
            "content": "<p>Đoạn mở đầu.</p><p>Đoạn nội dung chính.</p><p>Đoạn kết.</p>",
            "category": "Tin tức",
            "tags": "demo, auto poster",
            "status": "draft",
        },
        {
            "ma_bai": "bai02",
            "title": "Bài demo 02",
            "content": "Đoạn một.\n\nĐoạn hai.\n\nĐoạn ba.",
            "category": "Hướng dẫn",
            "tags": "demo",
            "status": "draft",
        },
    ]
    pd.DataFrame(rows).to_excel(data_dir / "sample_posts.xlsx", index=False)

    samples = [
        ("bai01_bg.jpg", "#f05a5a"),
        ("bai01_1.jpg", "#f7c948"),
        ("bai01_2.jpg", "#4cc9f0"),
        ("bai02_bg.jpg", "#b9794b"),
        ("bai02_1.jpg", "#90be6d"),
        ("orphan_1.jpg", "#777777"),
    ]
    for name, color in samples:
        image = Image.new("RGB", (900, 600), color)
        draw = ImageDraw.Draw(image)
        draw.text((40, 40), name, fill="white")
        image.save(image_dir / name, quality=88)

    print(f"Created {data_dir / 'sample_posts.xlsx'}")
    print(f"Created sample images in {image_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
