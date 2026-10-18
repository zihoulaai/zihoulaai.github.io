# -*- coding: utf-8 -*-
"""
生成中文字体子集（WOFF2）。

用法：
    python tools/subset-font.py <源字体路径>

字形范围的取舍：
    只按「当前站点用到的字」取子集，体积最小（约几十万字节），
    但以后写新文章会出现缺字，回退到系统字体后中西文观感割裂。
    所以这里取「站点实际用字 + GB2312 全集 6763 常用汉字」，
    一次生成即可长期使用。

什么时候需要重跑：
    新增文章后。若站点规模变大、担心体积，可改用 3500 常用字表
    （在 collect_chars 中把 GB2312 全集替换成常用字表即可）。
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "fonts"


def gb2312_chars():
    """用编码标准枚举 6763 个常用简体汉字，避免内置一大张字表。"""
    for b1 in range(0xB0, 0xF8):
        for b2 in range(0xA1, 0xFF):
            try:
                yield bytes([b1, b2]).decode("gb2312")
            except UnicodeDecodeError:
                pass


def collect_chars():
    chars = set()

    # 1) 站点实际用到的字符（含 front matter 里的中文分类名）
    targets = list((ROOT / "content").rglob("*.md")) + [ROOT / "hugo.toml"]
    for f in targets:
        if f.is_file():
            chars.update(f.read_text(encoding="utf-8", errors="ignore"))

    # 2) GB2312 常用汉字全集
    chars.update(gb2312_chars())

    # 3) ASCII 可打印字符
    chars.update(chr(c) for c in range(0x20, 0x7F))

    # 4) 中文标点与全角符号
    chars.update("　、。〈〉《》「」『』【】〔〕！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠［＼］＾＿｀｛｜｝～￥°±×÷•—…“”‘’")

    return {c for c in chars if ord(c) >= 0x20}


def main():
    if len(sys.argv) < 2:
        print("usage: python tools/subset-font.py <source-font.ttf>")
        sys.exit(1)

    src = pathlib.Path(sys.argv[1])
    if not src.is_file():
        print("source font not found:", src)
        sys.exit(1)

    chars = collect_chars()
    cjk = sum(1 for c in chars if "\u4e00" <= c <= "\u9fff")
    print(f"collected {len(chars)} chars ({cjk} CJK)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    charset_file = OUT_DIR / "_charset.txt"
    # pyftsubset 的 unicodes-file 每行必须写成 U+XXXX，
    # 写成十进制数字会被静默忽略，只留下极少字形却不报错
    charset_file.write_text(
        "\n".join(f"U+{ord(c):04X}" for c in sorted(chars)), encoding="ascii"
    )

    out = OUT_DIR / "noto-sans-sc-subset.woff2"
    subprocess.run(
        [
            sys.executable, "-m", "fontTools.subset",
            str(src),
            f"--unicodes-file={charset_file}",
            f"--output-file={out}",
            "--flavor=woff2",
            "--layout-features=*",
            "--name-IDs=*",
            "--drop-tables+=DSIG",
        ],
        check=True,
    )
    charset_file.unlink(missing_ok=True)

    size_kb = out.stat().st_size / 1024
    print(f"wrote {out.relative_to(ROOT)} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()