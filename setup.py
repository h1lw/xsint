import re
from pathlib import Path
from setuptools import setup, find_packages


def _read_version() -> str:
    init = Path(__file__).parent / "xsint" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        raise RuntimeError("could not find __version__ in xsint/__init__.py")
    return m.group(1)


setup(
    name="xsint",
    version=_read_version(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiohttp",
        "aiohttp-socks",
        "phonenumbers",
        "geopy",
        "hashid",
        "httpx",
        "intelx",
        "telethon",
    ],
    entry_points={
        "console_scripts": [
            "xsint=xsint.__main__:main",
        ],
    },
)
