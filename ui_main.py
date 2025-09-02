import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QLabel,
    QPushButton, QMessageBox, QInputDialog, QLineEdit, QDialog, QDialogButtonBox,
    QFormLayout, QPlainTextEdit, QHBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import api


class OneNoteUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OneNote Explorer")
        self.resize(1000, 700)

        # État courant
        self.current_level = "notebooks"
        self.current_notebook = None
        self.current_section = None
        self.current_page = None
        self.history = []

        # --- Layout principal ---
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)

        # --- Barre d'actions ---
        btn_bar = QHBoxLayout()
        self.layout.addLayout(btn_bar)

        self.btn_back = QPushButton("⬅ Retour")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setVisible(False)
        btn_bar.addWidget(self.btn_back)

        self.btn_new_page = QPushButton("➕ Nouvelle page")
        self.btn_new_page.clicked.connect(self.create_new_page_dialog)
        self.btn_new_page.setVisible(False)
        btn_bar.addWidget(self.btn_new_page)

        # --- Label niveau courant ---
        self.label = QLabel("Carnets OneNote")
        self.layout.addWidget(self.label)

        # --- Liste pour notebooks/sections/pages ---
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # --- Affichage contenu page ---
        self.webview = QWebEngineView()
        self.webview.setVisible(False)
        self.layout.addWidget(self.webview, stretch=1)

        # --- Charger les notebooks initiaux ---
        self.load_notebooks()

    # ---------------------
    # Navigation & chargement
    # ---------------------

    def load_notebooks(self):
        try:
            notebooks = api.get_notebooks()
            self.notebooks = notebooks
            self.list_widget.clear()
            for nb in notebooks:
                self.list_widget.addItem(nb["displayName"])
            self.label.setText("Carnets OneNote")
            self.current_level = "notebooks"
            self.btn_back.setVisible(False)
            self.btn_new_page.setVisible(False)
            self.webview.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les carnets:\n{e}")

    def on_item_double_clicked(self, item):
        if self.current_level == "notebooks":
            nb = next(n for n in self.notebooks if n["displayName"] == item.text())
            self.history.append(("notebooks", None))
            self.load_sections(nb)

        elif self.current_level == "sections":
            sec = next(s for s in self.sections if s["displayName"] == item.text())
            self.history.append(("sections", self.current_notebook))
            self.load_pages(sec)

        elif self.current_level == "pages":
            pg = next(p for p in self.pages if p["title"] == item.text())
            self.history.append(("pages", self.current_section))
            self.load_page_content(pg)

    def load_sections(self, notebook):
        try:
            sections = api.get_sections(notebook["id"])
            self.sections = sections
            self.current_notebook = notebook
            self.current_level = "sections"

            self.list_widget.clear()
            for sec in sections:
                self.list_widget.addItem(sec["displayName"])
            self.label.setText(f"Sections de {notebook['displayName']}")
            self.btn_back.setVisible(True)
            self.btn_new_page.setVisible(False)
            self.webview.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les sections:\n{e}")

    def load_pages(self, section):
        try:
            pages = api.get_pages(section["id"])
            self.pages = pages
            self.current_section = section
            self.current_level = "pages"

            self.list_widget.clear()
            for pg in pages:
                self.list_widget.addItem(pg["title"])
            self.label.setText(f"Pages de {section['displayName']}")
            self.btn_back.setVisible(True)
            self.btn_new_page.setVisible(True)
            self.webview.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les pages:\n{e}")

    def load_page_content(self, page):
        try:
            raw_html = api.get_page_content(page["id"])
            cleaned = api.clean_onenote_html(raw_html)
            self.webview.setHtml(cleaned)
            self.current_page = page
            self.current_level = "page_content"

            self.label.setText(page["title"])
            self.list_widget.clear()
            self.btn_back.setVisible(True)
            self.btn_new_page.setVisible(False)
            self.webview.setVisible(True)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le contenu:\n{e}")

    def go_back(self):
        if not self.history:
            return

        prev_level, obj = self.history.pop()

        if prev_level == "notebooks":
            self.load_notebooks()
        elif prev_level == "sections":
            self.load_sections(obj)
        elif prev_level == "pages":
            self.load_pages(obj)

    # ---------------------
    # Création d'une nouvelle page
    # ---------------------

    def create_new_page_dialog(self):
        if not self.current_section:
            QMessageBox.warning(self, "OneNote", "Sélectionne d'abord une section.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Nouvelle page OneNote")
        form = QFormLayout(dlg)

        title_edit = QLineEdit(dlg)
        title_edit.setPlaceholderText("Titre de la page")
        form.addRow("Titre:", title_edit)

        content_edit = QPlainTextEdit(dlg)
        content_edit.setPlaceholderText("Contenu HTML simple (ex: <p>Hello</p>)")
        content_edit.setPlainText("<h1>Nouvelle page</h1><p>Contenu…</p>")
        form.addRow("Contenu:", content_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dlg
        )
        form.addRow(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        title = title_edit.text().strip() or "Sans titre"
        html = content_edit.toPlainText().strip() or "<p>(vide)</p>"

        try:
            api.create_page(self.current_section["id"], title, html)
            # Rafraîchir les pages
            self.load_pages(self.current_section)
            QMessageBox.information(self, "OneNote", "Page créée ✅")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Création impossible:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OneNoteUI()
    win.show()
    sys.exit(app.exec())