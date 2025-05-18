# Installation Guide

This document provides detailed instructions for installing gSort Professional on different platforms.

## Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB+ recommended for large datasets
- **CPU**: Multi-core processor recommended
- **Storage**: 200MB for installation, plus space for your data files
- **Python**: If installing from source, Python 3.8 or newer is required

## Option 1: Standalone Executable (Recommended)

### Windows

1. Download the latest installer from the [releases page](https://github.com/krackn88/gsort-professional/releases)
2. Run the downloaded `gSort-Professional-Setup-X.X.X.exe` file
3. Follow the installation wizard instructions
4. Launch gSort Professional from the Start Menu or desktop shortcut

### macOS

1. Download the latest `.dmg` file from the [releases page](https://github.com/krackn88/gsort-professional/releases)
2. Open the downloaded `.dmg` file
3. Drag the gSort Professional app to your Applications folder
4. Launch from Applications or using Spotlight (Cmd+Space)

### Linux

1. Download the latest `.AppImage` file from the [releases page](https://github.com/krackn88/gsort-professional/releases)
2. Make the AppImage executable:
   ```bash
   chmod +x gSort-Professional-X.X.X.AppImage
   ```
3. Run the application:
   ```bash
   ./gSort-Professional-X.X.X.AppImage
   ```

## Option 2: Installation from Source

### Prerequisites

- Python 3.8 or newer
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Steps

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/krackn88/gsort-professional.git
   cd gsort-professional
   ```
   
   Alternatively, download and extract the source code from the [releases page](https://github.com/krackn88/gsort-professional/releases).

2. **Create and activate a virtual environment (recommended)**:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the package and dependencies**:
   ```bash
   pip install -e .
   ```
   
   For development installation with additional tools:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Building from Source

### Prerequisites

- All requirements for installation from source
- PyInstaller (`pip install pyinstaller`)

### Build Steps

1. **Prepare the environment**:
   ```bash
   # Install the development dependencies
   pip install -e ".[dev]"
   ```

2. **Build the executable**:
   ```bash
   # On Windows
   pyinstaller gsort-professional.spec
   
   # On macOS
   pyinstaller gsort-professional.spec
   
   # On Linux
   pyinstaller gsort-professional.spec
   ```

3. **Find the built application**:
   The built application will be located in the `dist` directory.

## Troubleshooting

### Common Issues

#### Missing Dependencies

If you encounter errors about missing modules when running from source, ensure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

#### Permission Issues (Linux/macOS)

If you encounter permission issues:
```bash
chmod +x gSort-Professional-X.X.X.AppImage  # For AppImage
chmod +x venv/bin/python  # For virtual environment
```

#### Display Issues

If the UI appears too small or too large:
- Try running with `--style Fusion` command line argument
- Adjust your system's display scaling settings

## Support

For additional help or to report issues:
- Open an issue on [GitHub](https://github.com/krackn88/gsort-professional/issues)
- Check the [FAQ](https://github.com/krackn88/gsort-professional/wiki/FAQ) on our wiki