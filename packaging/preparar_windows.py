"""Reúne un Python 3.12 x64 privado y el conector para construir Gestión de Órdenes de Producción."""

import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if (
        sys.platform != "win32"
        or sys.version_info[:2] != (3, 12)
        or struct.calcsize("P") != 8
    ):
        raise SystemExit("Ejecute este script con Python 3.12 de 64 bits para Windows.")
    import tkinter

    interpreter = tkinter.Tcl()
    base = Path(sys.base_prefix)
    tcl = Path(interpreter.eval("info library")).parent
    if not (base / "DLLs" / "_tkinter.pyd").exists() or not tcl.exists():
        raise SystemExit("Instale la distribución completa de Python 3.12 con Tcl/Tk.")
    runtime = ROOT / "runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir()
    for name in ["python.exe", "pythonw.exe", "python312.dll", "python3.dll"]:
        shutil.copy2(base / name, runtime / name)
    for path in base.glob("vcruntime*.dll"):
        shutil.copy2(path, runtime / path.name)
    shutil.copytree(
        base / "DLLs",
        runtime / "DLLs",
        ignore=shutil.ignore_patterns("_test*", "__pycache__"),
    )
    shutil.copytree(tcl, runtime / "tcl", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(
        base / "Lib" / "tkinter",
        runtime / "Lib" / "tkinter",
        ignore=shutil.ignore_patterns("__pycache__", "test"),
    )
    excluded = {
        "site-packages",
        "__pycache__",
        "test",
        "tests",
        "tkinter",
        "idlelib",
        "ensurepip",
        "turtledemo",
    }
    with zipfile.ZipFile(
        runtime / "python312.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for path in (base / "Lib").rglob("*"):
            relative = path.relative_to(base / "Lib")
            if (
                path.is_file()
                and not excluded.intersection(relative.parts)
                and path.suffix not in (".pyc", ".pyo")
            ):
                archive.write(path, relative.as_posix())
    (runtime / "python312._pth").write_text(
        "python312.zip\n.\nDLLs\nLib\n..\n../vendor\nimport site\n", encoding="utf-8"
    )
    license_path = next(
        (p for p in (base / "LICENSE.txt", base / "LICENSE") if p.exists()), None
    )
    if license_path is None:
        raise SystemExit(
            "No se encontró la licencia de Python en la instalación usada para construir."
        )
    shutil.copy2(license_path, runtime / "LICENSE.txt")
    vendor = ROOT / "vendor"
    if vendor.exists():
        shutil.rmtree(vendor)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(vendor),
            "-r",
            str(ROOT / "requirements.txt"),
        ],
        check=True,
    )
    subprocess.run(
        [str(runtime / "python.exe"), str(ROOT / "verificar_entorno.py")],
        cwd=ROOT,
        check=True,
    )
    print(
        "Entorno Windows preparado. Las licencias de terceros se conservan en runtime y vendor."
    )


if __name__ == "__main__":
    main()
