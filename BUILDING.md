Building with Nuitka

Quick steps (Windows):

1. Activate your virtualenv (if using .venv):

PowerShell:

    . .venv\Scripts\Activate.ps1

cmd.exe:

    .venv\Scripts\activate.bat

2. Run the included script (PowerShell recommended):

PowerShell:

    .\build_nuitka.ps1

or in cmd.exe:

    build_nuitka.bat

What the scripts do:
- Ensure `nuitka`, `setuptools`, and `wheel` are installed in the active Python environment.
- Run Nuitka with `--standalone` and `--include-data-dir=assets=assets` so the `assets` folder is packaged alongside the executable.
- Output is written to `dist_main`.

Notes:
- If you want to debug, remove `--windows-disable-console` from the build command in the script so the console is visible.
- If specific data files are still missing in the build output, you can add additional `--include-data-file` or `--include-data-dir` flags.
- For a single-file exe use `--onefile` instead of `--standalone` but expect larger exe and runtime extraction behavior.
