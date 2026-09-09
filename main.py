import sys
from converter.version import APP_VERSION


def main():
    try:
        from PyQt5.QtWidgets import QApplication
        from converter.gui import MainWindow
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PyQt5"):
            print("PyQt5 fehlt. Bitte: python -m pip install -r requirements.txt", file=sys.stderr)
            return 1
        raise
    app = QApplication(sys.argv)
    app.setApplicationName("MACH3 -> simCNC")
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    window.show()
    if len(sys.argv) > 1:
        window.load_profile(sys.argv[1])
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
