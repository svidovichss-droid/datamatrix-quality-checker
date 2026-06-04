# Build Instructions for DataMatrix Quality Checker

## ⚠️ CRITICAL: Use Conda for Windows Builds

The `libdmtx-64.dll` DLL loading error occurs because PyInstaller doesn't properly bundle native C++ DLLs from wheel packages without proper environment setup.

**Solution: Use Conda** (recommended)

### Windows - Recommended Method (Conda)

```bash
scripts\build_conda.bat
```

This script:
1. Creates a `dmtx-build` conda environment
2. Installs packages via conda (provides proper DLL dependencies)
3. Builds the executable with PyInstaller
4. Result: `dist\DataMatrixChecker.exe` with all DLLs properly bundled

### Windows - Alternative (System Python)

```bash
scripts\build.bat
```

Note: May fail with DLL errors if dependencies aren't installed with proper C++ runtime support.

### Linux/macOS

```bash
bash scripts/build.sh
```

## Installation Requirements

### Option 1: Conda (Recommended for Windows)

```bash
# Install Miniconda: https://docs.conda.io/projects/miniconda/en/latest/

# Run build
scripts\build_conda.bat
```

### Option 2: System Python + pip

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller build.spec

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller build.spec
```

## Troubleshooting

### Error: "Could not find module 'libdmtx-64.dll'"

**Causes:**
- PyInstaller didn't bundle the DLL
- Conda environment not active
- Missing C++ runtime

**Solutions:**
1. Use `scripts\build_conda.bat` (recommended)
2. Ensure conda base environment is active
3. Install Visual C++ Redistributable: https://support.microsoft.com/en-us/help/2977003
4. Manually copy DLL to `dist\` folder:
   - Find: `python -c "import pylibdmtx; print(pylibdmtx.__file__)"`
   - Copy `libdmtx-64.dll` from that location to `dist\` folder

### Build takes too long

- First build is slower (~5 minutes)
- Subsequent builds are faster (2-3 minutes)

## Output

After successful build:
- Executable: `dist\DataMatrixChecker.exe`
- Size: ~150-200 MB (portable, no installation needed)
- All DLLs included in the bundle

## Running the Executable

```bash
# Simple
dist\DataMatrixChecker.exe

# With Conda environment active
conda activate dmtx-build
dist\DataMatrixChecker.exe
```
