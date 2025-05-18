#!/usr/bin/env python3
"""
Build script for gSort Professional.
Simplifies the building process for different platforms.
"""

import os
import sys
import shutil
import subprocess
import platform
import argparse
from datetime import datetime

# Ensure our path is correct
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Build gSort Professional")
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    
    parser.add_argument(
        "--release",
        action="store_true",
        help="Build a release version"
    )
    
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    
    parser.add_argument(
        "--installer",
        action="store_true",
        help="Create an installer (Windows only)"
    )
    
    return parser.parse_args()


def clean_build_dirs():
    """Clean build directories"""
    print("Cleaning build directories...")
    
    dirs_to_clean = ['build', 'dist', 'gsort_professional.egg-info']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)


def run_tests():
    """Run tests"""
    print("Running tests...")
    
    try:
        subprocess.run([sys.executable, "-m", "pytest"], check=True)
        print("Tests passed!")
    except subprocess.CalledProcessError:
        print("Tests failed!")
        sys.exit(1)
    except FileNotFoundError:
        print("pytest not found. Skipping tests.")


def build_application(release=False):
    """Build the application"""
    print("Building application...")
    
    # Determine spec file
    spec_file = "gsort-professional.spec"
    
    # Build command
    cmd = [
        "pyinstaller",
        spec_file,
        "--noconfirm"
    ]
    
    if release:
        cmd.append("--clean")
    
    try:
        subprocess.run(cmd, check=True)
        print("Build complete!")
    except subprocess.CalledProcessError:
        print("Build failed!")
        sys.exit(1)
    except FileNotFoundError:
        print("PyInstaller not found. Make sure it's installed.")
        sys.exit(1)


def create_installer():
    """Create an installer (Windows only)"""
    if platform.system() != "Windows":
        print("Installer creation is currently only supported on Windows.")
        return
    
    print("Creating installer...")
    
    # This would normally use a tool like NSIS or Inno Setup
    # For demonstration purposes, we'll just create a ZIP file
    
    import zipfile
    from gsort import __version__
    
    # Create ZIP file
    zip_name = f"gsort-professional-{__version__}.zip"
    
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("dist/gSort-Professional"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "dist")
                    zipf.write(file_path, arcname)
        
        print(f"Created installer: {zip_name}")
    except Exception as e:
        print(f"Error creating installer: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 80)
    print(f"gSort Professional Build Script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    args = parse_args()
    
    # Clean build directories if requested
    if args.clean:
        clean_build_dirs()
    
    # Run tests unless skipped
    if not args.skip_tests:
        run_tests()
    
    # Build application
    build_application(release=args.release)
    
    # Create installer if requested and on Windows
    if args.installer:
        create_installer()
    
    print("\nBuild process completed successfully!")


if __name__ == "__main__":
    main()
