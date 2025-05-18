# Building gSort Professional

This document provides instructions for building gSort Professional from source.

## Prerequisites

Before building the application, ensure you have the following installed:

- Python 3.8 or newer
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Option 1: Using the Build Script (Recommended)

The easiest way to build gSort Professional is using the included build script.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the build script
python build.py
```

### Build Script Options

The build script supports several options:

```bash
# Clean build directories before building
python build.py --clean

# Build a release version
python build.py --release

# Skip running tests
python build.py --skip-tests

# Create an installer (Windows only)
python build.py --installer

# Combine options
python build.py --clean --release --installer
```

## Option 2: Manual Building

If you prefer to build manually, follow these steps:

```bash
# Install dependencies
pip install -r requirements.txt

# Run PyInstaller directly
pyinstaller gsort-professional.spec
```

The built application will be found in the `dist` directory.

## Platform-Specific Instructions

### Windows

On Windows, you can create an installer using the build script:

```bash
python build.py --release --installer
```

This will create a ZIP file in the current directory.

For a proper installer, you can use NSIS or Inno Setup with the files generated in the `dist` directory.

### macOS

On macOS, the build process creates an app bundle:

```bash
python build.py --release
```

The .app bundle will be created in the `dist` directory.

To create a DMG file:

```bash
# Install create-dmg tool
brew install create-dmg

# Create DMG
create-dmg \
  --volname "gSort Professional" \
  --volicon "resources/icons/app_icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "gSort Professional.app" 200 190 \
  --hide-extension "gSort Professional.app" \
  --app-drop-link 600 185 \
  "gSort Professional.dmg" \
  "dist/gSort Professional.app"
```

### Linux

On Linux, the build process creates a directory with all necessary files:

```bash
python build.py --release
```

To create an AppImage:

```bash
# Install appimagetool
wget -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x appimagetool

# Create AppDir structure
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Copy files
cp -r dist/gSort-Professional/* AppDir/usr/bin/
cp resources/icons/app_icon.png AppDir/usr/share/icons/hicolor/256x256/apps/gsort-professional.png

# Create desktop file
cat > AppDir/usr/share/applications/gsort-professional.desktop << EOF
[Desktop Entry]
Name=gSort Professional
Exec=gsort-professional
Icon=gsort-professional
Type=Application
Categories=Utility;
EOF

# Create AppRun file
cat > AppDir/AppRun << EOF
#!/bin/sh
SELF=\$(readlink -f "\$0")
HERE=\${SELF%/*}
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
"\${HERE}/usr/bin/gSort-Professional" "$@"
EOF
chmod +x AppDir/AppRun

# Create AppImage
./appimagetool AppDir
```

## Troubleshooting

### Common Issues

#### Missing Dependencies

If you encounter errors about missing modules:

```bash
pip install -r requirements.txt
```

#### PyInstaller Hook Errors

If PyInstaller has issues finding modules:

```bash
# Try running with debug output
pyinstaller --log-level DEBUG gsort-professional.spec
```

#### Resource Files Missing

Ensure the `resources` directory has all necessary files:

```bash
# Check resource files
ls -la resources/icons/
ls -la resources/images/
ls -la resources/styles/
```

#### Build Script Permission Issues

On Linux/macOS:

```bash
chmod +x build.py
```

## Support

For additional help or to report build issues:
- Open an issue on [GitHub](https://github.com/krackn88/gsort-professional/issues)
