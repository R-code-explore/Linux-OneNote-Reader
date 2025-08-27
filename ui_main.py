from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QWidget, 
    QVBoxLayout, QLabel, QPushButton
)
import sys
import api
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OneNote Linux")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        # Return Button
        self.btn_back = QPushButton("⬅ Retour")
        self.btn_back.clicked.connect(self.go_back)
        self.layout.addWidget(self.btn_back)

        # State label
        self.label = QLabel("Notebooks")
        self.layout.addWidget(self.label)

        # Liste notebooks / sections / pages
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # html pages's content
        self.page_viewer = QWebEngineView()
        self.page_viewer.setVisible(False) # hidden on start
        self.layout.addWidget(self.page_viewer)

        # Display Notebooks
        self.notebooks = api.get_notebooks()
        for nb in self.notebooks:
            self.list_widget.addItem(nb["displayName"])

        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Navigation tracking
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
            raw_html = api.get_page_content(page["id"])
            pretty_html = api.clean_onenote_html(raw_html)

            # Better content display ( not working yet )
            self.page_viewer.setVisible(True)
            self.page_viewer.setHtml(pretty_html)

            # Hidden lists while page reading
            self.list_widget.setVisible(False)
            self.label.setText(f"Lecture : {page['title']}")
            self.current_level = "page_content"


    def go_back(self):
        if not self.history:
            return

        prev_level = self.history.pop()

        if prev_level == "notebooks":
            self.page_viewer.setVisible(False)
            self.page_viewer.setHtml("")
            self.list_widget.setVisible(True)

            self.list_widget.clear()
            for nb in self.notebooks:
                self.list_widget.addItem(nb["displayName"])
            self.label.setText("Notebooks")
            self.current_level = "notebooks"

        elif prev_level == "sections":
            self.page_viewer.setVisible(False)
            self.page_viewer.setHtml("")
            self.list_widget.setVisible(True)

            self.list_widget.clear()
            for sec in self.sections:
                self.list_widget.addItem(sec["displayName"])
            self.label.setText(f"Sections de {self.current_notebook['displayName']}")
            self.current_level = "sections"

        elif prev_level == "pages":
            self.page_viewer.setVisible(False)
            self.page_viewer.setHtml("")
            self.list_widget.setVisible(True)

            self.list_widget.clear()
            for pg in self.pages:
                self.list_widget.addItem(pg["title"])
            self.label.setText(f"Pages de {self.current_section['displayName']}")
            self.current_level = "pages"

        elif prev_level == "page_content":
            self.page_viewer.setVisible(False)
            self.page_viewer.setHtml("")  # cleaner
            self.list_widget.setVisible(True)

            self.label.setText(f"Pages de {self.current_section['displayName']}")
            self.current_level = "pages"

def run_ui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
