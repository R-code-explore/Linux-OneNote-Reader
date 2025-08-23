from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QWidget, 
    QVBoxLayout, QLabel, QPushButton, QTextBrowser
)
import sys
import api

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OneNote Linux")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        # Bouton retour
        self.btn_back = QPushButton("⬅ Retour")
        self.btn_back.clicked.connect(self.go_back)
        self.layout.addWidget(self.btn_back)

        # Label d’état
        self.label = QLabel("Notebooks")
        self.layout.addWidget(self.label)

        # Liste notebooks / sections / pages
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Zone pour contenu des pages
        self.page_viewer = QTextBrowser()
        self.page_viewer.setVisible(False)  # caché au départ
        self.layout.addWidget(self.page_viewer)

        # Charger les notebooks
        self.notebooks = api.get_notebooks()
        for nb in self.notebooks:
            self.list_widget.addItem(nb["displayName"])

        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Suivi de navigation
        self.history = []
        self.current_level = "notebooks"
        self.current_notebook = None
        self.current_section = None
        self.current_page = None

    def on_item_double_clicked(self, item):
        if self.current_level == "notebooks":
            notebook = next(nb for nb in self.notebooks if nb["displayName"] == item.text())
            self.current_notebook = notebook
            sections = api.get_sections(notebook["id"])

            self.history.append("notebooks")
            self.list_widget.clear()
            for sec in sections:
                self.list_widget.addItem(sec["displayName"])

            self.sections = sections
            self.label.setText(f"Sections de {notebook['displayName']}")
            self.current_level = "sections"

        elif self.current_level == "sections":
            section = next(sec for sec in self.sections if sec["displayName"] == item.text())
            self.current_section = section
            pages = api.get_pages(section["id"])

            self.history.append("sections")
            self.list_widget.clear()
            for pg in pages:
                self.list_widget.addItem(pg["title"])

            self.pages = pages
            self.label.setText(f"Pages de {section['displayName']}")
            self.current_level = "pages"

        elif self.current_level == "pages":
            page = next(pg for pg in self.pages if pg["title"] == item.text())
            self.current_page = page

            self.history.append("pages")
            html_content = api.get_page_content(page["id"])

            # Afficher contenu HTML dans le viewer
            self.page_viewer.setVisible(True)
            self.page_viewer.setHtml(html_content)

            # Cacher la liste quand on lit une page
            self.list_widget.setVisible(False)
            self.label.setText(f"Lecture : {page['title']}")
            self.current_level = "page_content"

    def go_back(self):
        if not self.history:
            return

        prev_level = self.history.pop()

        if prev_level == "notebooks":
            self.list_widget.clear()
            for nb in self.notebooks:
                self.list_widget.addItem(nb["displayName"])
            self.label.setText("Notebooks")
            self.current_level = "notebooks"

        elif prev_level == "sections":
            self.list_widget.clear()
            for sec in self.sections:
                self.list_widget.addItem(sec["displayName"])
            self.label.setText(f"Sections de {self.current_notebook['displayName']}")
            self.current_level = "sections"

        elif prev_level == "pages":
            self.list_widget.clear()
            for pg in self.pages:
                self.list_widget.addItem(pg["title"])
            self.label.setText(f"Pages de {self.current_section['displayName']}")
            self.current_level = "pages"

        elif prev_level == "page_content":
            self.page_viewer.setVisible(False)
            self.list_widget.setVisible(True)
            self.label.setText(f"Pages de {self.current_section['displayName']}")
            self.current_level = "pages"

def run_ui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())