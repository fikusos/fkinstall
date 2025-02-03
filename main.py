import sys
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QProgressBar, QListWidgetItem, QTabWidget,
    QInputDialog, QCheckBox, QStackedWidget
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon


class Worker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command, password=None):
        super().__init__()
        self.command = command
        self.password = password

    def run(self):
        try:
            if self.password:
                process = subprocess.run(
                    self.command, input=self.password.encode(), check=True, capture_output=True
                )
            else:
                process = subprocess.run(self.command, check=True, capture_output=True)
            self.finished.emit(process.stdout.decode())
        except subprocess.CalledProcessError as e:
            self.error.emit(e.stderr.decode())


class PackageItem(QWidget):
    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setPixmap(self.get_package_icon(self.package_name).pixmap(32, 32))
        layout.addWidget(self.icon_label)
        self.label = QLabel(self.package_name)
        self.label.setStyleSheet("font-size: 14px; color: #ECEFF4;")
        layout.addWidget(self.label)
        layout.addStretch()
        self.install_button = QPushButton()
        self.install_button.setIcon(QIcon.fromTheme("system-software-install"))
        self.install_button.setFixedSize(32, 32)
        self.install_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.install_button.clicked.connect(self.install_package)
        layout.addWidget(self.install_button)
        self.remove_button = QPushButton()
        self.remove_button.setIcon(QIcon.fromTheme("edit-delete"))
        self.remove_button.setFixedSize(32, 32)
        self.remove_button.setStyleSheet(
            """
            QPushButton {
                background-color: #F44336;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            """
        )
        self.remove_button.clicked.connect(self.remove_package)
        layout.addWidget(self.remove_button)
        self.setLayout(layout)

    def get_package_icon(self, package_name):
        icon = QIcon.fromTheme(package_name)
        if icon.isNull():
            icon = QIcon.fromTheme("applications-other")
        return icon

    def install_package(self):
        self.parent.install_selected_package(self.package_name)

    def remove_package(self):
        self.parent.remove_selected_package(self.package_name)


class FKInstall(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FKInstall")
        self.setGeometry(100, 100, 1000, 700)
        self.set_style()
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.main_page = QWidget()
        self.init_main_page()
        self.central_widget.addWidget(self.main_page)
        self.log_file = os.path.expanduser("~/.local/share/fkinstall.log")
        self.ensure_log_file_exists()
        self.config_dir = os.path.expanduser("~/.config/fkinstall")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.ensure_config_dir_exists()

    def ensure_log_file_exists(self):
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("FKInstall Log\n")

    def log_message(self, message):
        with open(self.log_file, "a") as f:
            f.write(f"{message}\n")

    def ensure_config_dir_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def set_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel {
                color: #ECEFF4;
                font-size: 16px;
            }
            QTextEdit {
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QLineEdit {
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                background-color: #4CAF50;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTabBar::tab {
                background: #4C566A;
                color: #ECEFF4;
                padding: 10px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #81A1C1;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 5px;
            }
            """
        )

    def init_main_page(self):
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setStyleSheet(
            """
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #555;
            background-color: #2E3440;
            color: #ECEFF4;
            """
        )
        self.search_input.returnPressed.connect(self.on_search_enter_pressed)
        search_layout.addWidget(self.search_input)
        self.update_button = QPushButton("Update System")
        self.update_button.setStyleSheet(
            """
            QPushButton {
                font-size: 12px;
                padding: 5px;
                border-radius: 5px;
                background-color: #4CAF50;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.update_button.clicked.connect(self.update_system)
        search_layout.addWidget(self.update_button)
        layout.addLayout(search_layout)
        self.package_manager_switch = QCheckBox("Use yay instead of pacman")
        self.package_manager_switch.setStyleSheet(
            """
            font-size: 14px;
            color: #ECEFF4;
            """
        )
        self.package_manager_switch.setChecked(False)
        layout.addWidget(self.package_manager_switch)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabBar::tab {
                background: #4C566A;
                color: #ECEFF4;
                padding: 10px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #81A1C1;
            }
            """
        )
        layout.addWidget(self.tabs)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 5px;
            }
            """
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.main_page.setLayout(layout)
        self.init_categories()

    def init_categories(self):
        categories = {
            "Internet": [
                "firefox", "chromium", "thunderbird", "opera", "vivaldi", "tor-browser", "falkon",
                "qutebrowser", "epiphany", "midori", "lynx", "links", "w3m", "surf", "dillo", "netsurf",
                "palemoon", "waterfox", "basilisk", "otter-browser", "slimjet", "iridium", "ungoogled-chromium",
                "seamonkey", "konqueror", "luakit", "arora", "qupzilla", "dooble", "uzbl", "min", "nyxt",
                "elinks", "retawq", "edbrowse", "w3", "amaya", "dillo2", "kazehakase", "galeon", "rekonq"
            ],
            "Terminal": [
                "vim", "emacs", "htop", "alacritty", "kitty", "tmux", "zsh", "fish", "bash", "neofetch",
                "ranger", "ncdu", "glances", "btop", "lazygit", "tig", "micro", "nano", "mc", "terminator",
                "tilix", "guake", "yakuake", "cool-retro-term", "hyper", "tabby", "wezterm", "xterm",
                "rxvt", "st", "sakura", "eterm", "terminology", "gnome-terminal", "konsole", "xfce4-terminal",
                "lxterminal", "mate-terminal", "deepin-terminal", "terminix", "blackbox", "alacritty", "kitty"
            ],
            "WM/DE": [
                "cinnamon", "gnome", "kde-plasma", "xfce4", "i3", "awesome", "bspwm", "dwm", "qtile", "lxde",
                "lxqt", "mate", "enlightenment", "openbox", "fluxbox", "icewm", "jwm", "pekwm", "spectrwm",
                "herbstluftwm", "xmonad", "sway", "hyprland", "river", "wayfire", "weston", "labwc",
                "budgie", "pantheon", "deepin", "lumina", "trinity", "ede", "ede2", "ede3", "ede4", "ede5"
            ],
            "Office": [
                "libreoffice", "onlyoffice", "wps-office", "abiword", "gnumeric", "scribus", "latexila",
                "lyx", "texmaker", "texstudio", "kile", "gummi", "focuswriter", "zathura", "calibre",
                "okular", "evince", "masterpdfeditor", "xournalpp", "joplin", "cherrytree", "zim",
                "notepadqq", "geany", "bluefish", "brackets", "atom", "sublime-text", "vscode", "codeblocks",
                "qtcreator", "kdevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang"
            ],
            "Multimedia": [
                "vlc", "audacity", "kdenlive", "obs-studio", "kodi", "handbrake", "ffmpeg", "gstreamer",
                "mpv", "smplayer", "celluloid", "shotcut", "pitivi", "openshot", "blender", "gimp", "inkscape",
                "darktable", "rawtherapee", "digikam", "krita", "mypaint", "pencil2d", "synfigstudio",
                "ardour", "lmms", "musescore", "rosegarden", "hydrogen", "qtractor", "audacious", "clementine",
                "rhythmbox", "amarok", "exaile", "guayadeque", "quodlibet", "deadbeef", "cmus", "mpd", "ncmpcpp"
            ],
            "Games": [
                "steam", "lutris", "minecraft-launcher", "wine", "playonlinux", "retroarch", "dolphin-emu",
                "pcsx2", "ppsspp", "mupen64plus", "scummvm", "dosbox", "openmw", "minetest", "supertuxkart",
                "xonotic", "wesnoth", "0ad", "openttd", "freeciv", "warzone2100", "megaglest", "teeworlds",
                "openra", "hedgewars", "armagetronad", "nethack", "angband", "dungeoncrawl", "cataclysm-dda",
                "cogmind", "adom", "tome4", "nethack", "angband", "dungeoncrawl", "cataclysm-dda", "cogmind"
            ],
            "Development": [
                "vscode", "sublime-text", "atom", "intellij-idea-community-edition", "pycharm-community-edition",
                "eclipse", "netbeans", "codeblocks", "qtcreator", "kdevelop", "geany", "bluefish", "brackets",
                "monodevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang", "llvm",
                "cmake", "meson", "ninja", "git", "mercurial", "subversion", "docker", "podman", "kubernetes",
                "ansible", "terraform", "vagrant", "packer", "puppet", "chef", "salt", "consul", "nomad", "vault"
            ],
            "System Utilities": [
                "htop", "gnome-disk-utility", "gparted", "timeshift", "grub-customizer", "gnome-system-monitor",
                "baobab", "stacer", "bleachbit", "grsync", "rsync", "timeshift", "cron", "systemd", "ufw",
                "gufw", "firewalld", "nmap", "wireshark", "tcpdump", "htop", "iotop", "iftop", "nethogs",
                "bmon", "glances", "neofetch", "screenfetch", "alsi", "archey", "inxi", "hardinfo", "lshw",
                "lsof", "strace", "ltrace", "gdb", "valgrind", "perf", "sysstat", "dstat", "sar", "iostat"
            ],
        }

        for category, packages in categories.items():
            tab = QListWidget()
            tab.setStyleSheet(
                """
                font-size: 14px;
                background-color: #2E3440;
                color: #ECEFF4;
                border-radius: 5px;
                """
            )
            for package in packages:
                item = QListWidgetItem()
                widget = PackageItem(package, self)
                item.setSizeHint(widget.sizeHint())
                tab.addItem(item)
                tab.setItemWidget(item, widget)
            self.tabs.addTab(tab, category)

    def on_search_enter_pressed(self):
        query = self.search_input.text()
        if query:
            self.search_packages(query)
        else:
            self.tabs.currentWidget().clear()

    def search_packages(self, query):
        try:
            if self.package_manager_switch.isChecked():
                result = subprocess.run(
                    ["yay", "-Ss", query], capture_output=True, text=True, check=False
                )
            else:
                result = subprocess.run(
                    ["pacman", "-Ss", query], capture_output=True, text=True, check=False
                )
            
            if not result.stdout:
                QMessageBox.information(self, "Info", "No packages found.")
                self.tabs.currentWidget().clear()
                return

            packages = result.stdout.splitlines()
            self.tabs.currentWidget().clear()
            for package in packages:
                if "/" in package:
                    parts = package.split("/")
                    if len(parts) > 1 and len(parts[1].split()) > 0:
                        package_name = parts[1].split()[0]
                        item = QListWidgetItem()
                        widget = PackageItem(package_name, self)
                        item.setSizeHint(widget.sizeHint())
                        self.tabs.currentWidget().addItem(item)
                        self.tabs.currentWidget().setItemWidget(item, widget)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error searching for packages: {e}")

    def install_selected_package(self, package_name):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        if self.package_manager_switch.isChecked():
            self.install_yay_package(package_name)
        else:
            self.install_pacman_package(package_name)

    def install_yay_package(self, package_name):
        self.worker = Worker(["yay", "-S", "--noconfirm", package_name])
        self.worker.finished.connect(self.on_install_finished)
        self.worker.error.connect(self.on_install_error)
        self.worker.start()

    def install_pacman_package(self, package_name):
        password, ok = QInputDialog.getText(
            self, "Enter Password", "Enter your sudo password:", QLineEdit.Password
        )
        if ok and password:
            self.worker = Worker(["sudo", "-S", "pacman", "-S", "--noconfirm", package_name], password)
            self.worker.finished.connect(self.on_install_finished)
            self.worker.error.connect(self.on_install_error)
            self.worker.start()

    def on_install_finished(self, output):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "Package installed successfully!")
        self.log_message(f"Package installed: {output}")

    def on_install_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error installing package: {error}")
        self.log_message(f"Error installing package: {error}")

    def remove_selected_package(self, package_name):
        try:
            subprocess.run(["sudo", "pacman", "-Rcc", "--noconfirm", package_name], check=True)
            QMessageBox.information(self, "Success", f"Package {package_name} removed successfully!")
            self.log_message(f"Package removed: {package_name}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Error removing package: {e}")
            self.log_message(f"Error removing package: {e}")

    def update_system(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        if self.package_manager_switch.isChecked():
            self.worker = Worker(["yay", "-Syu", "--noconfirm"])
        else:
            password, ok = QInputDialog.getText(
                self, "Enter Password", "Enter your sudo password:", QLineEdit.Password
            )
            if ok and password:
                self.worker = Worker(["sudo", "-S", "pacman", "-Syu", "--noconfirm"], password)
            else:
                return

        self.worker.finished.connect(self.on_update_finished)
        self.worker.error.connect(self.on_update_error)
        self.worker.start()

    def on_update_finished(self, output):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "System updated successfully!")
        self.log_message(f"System updated: {output}")

    def on_update_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error updating system: {error}")
        self.log_message(f"Error updating system: {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FKInstall()
    window.show()
    sys.exit(app.exec_())
