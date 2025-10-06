"""
PyQt6 Admin-GUI für das Poll-System
Modernes Dark Mode Design mit Material-Style
"""

import sys
import threading
import requests
import webbrowser
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QTextEdit,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QHeaderView,
    QSplitter, QGroupBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

from database import Database
from api import run_server


class ServerThread(QThread):
    """Separater Thread für den FastAPI-Server"""
    def run(self):
        try:
            run_server(host="0.0.0.0", port=8000)
        except Exception as e:
            print(f"Server-Fehler: {e}")


class CandidateDialog(QDialog):
    """Dialog zum Hinzufügen/Bearbeiten von Kandidaten"""

    def __init__(self, parent=None, candidate=None):
        super().__init__(parent)
        self.candidate = candidate
        self.setWindowTitle("Kandidat bearbeiten" if candidate else "Kandidat hinzufügen")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Name Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name des Kandidaten")
        if self.candidate:
            self.name_input.setText(self.candidate['name'])
        layout.addRow("Name:", self.name_input)

        # Beschreibung Input
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optionale Beschreibung")
        self.desc_input.setMaximumHeight(100)
        if self.candidate:
            self.desc_input.setPlainText(self.candidate.get('description', ''))
        layout.addRow("Beschreibung:", self.desc_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def get_data(self):
        """Gibt eingegebene Daten zurück"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.desc_input.toPlainText().strip()
        }


class AdminGUI(QMainWindow):
    """Hauptfenster der Admin-GUI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("easyWahl - Admin Panel")
        self.setGeometry(100, 100, 700, 800)

        # Server-Status
        self.server_running = False
        self.server_thread = None
        self.api_base = "http://localhost:8000"

        # Datenbank
        self.db = Database()

        # Kandidaten-Daten Cache
        self.candidates_data = []

        # UI aufbauen
        self.setup_ui()

        # Timer für Auto-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_results)

        # Initiales Update
        self.refresh_candidates()
        self.refresh_results()

    def setup_ui(self):
        """Erstellt die komplette UI"""

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === HEADER ===
        header = self.create_header()
        main_layout.addWidget(header)

        # Container für Inhalt mit Padding
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)

        # === SERVER CONTROL ===
        server_control = self.create_server_control()
        content_layout.addWidget(server_control)

        # === ADMIN ACTIONS ===
        admin_actions = self.create_admin_actions()
        content_layout.addWidget(admin_actions)

        # === CONTENT AREA ===
        # Kandidaten-Panel (nimmt die ganze Breite)
        candidates_panel = self.create_candidates_panel()
        content_layout.addWidget(candidates_panel)

        main_layout.addWidget(content_container)


        # Styling
        self.apply_stylesheet()

    def create_header(self):
        """Erstellt den Header"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f0f2f0,
                    stop:1 #000c40
                );
                border: none;
            }
        """)
        header.setFixedHeight(80)

        layout = QHBoxLayout(header)

        title = QLabel("easyWahl - Admin Panel")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        return header

    def create_server_control(self):
        """Erstellt die Server-Steuerung"""
        group = QGroupBox("Server-Steuerung")
        group.setFixedHeight(95)

        # Haupt-Layout (vertikal für Zentrierung)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)

        # Horizontales Layout für Buttons und Status
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)

        # Start Button
        self.start_btn = QPushButton("▶ Server starten")
        self.start_btn.clicked.connect(self.start_server)
        self.start_btn.setMinimumHeight(40)
        h_layout.addWidget(self.start_btn)

        # Stop Button
        self.stop_btn = QPushButton("■ Server stoppen")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        h_layout.addWidget(self.stop_btn)

        # Frontend Button
        frontend_btn = QPushButton("🌐 Live-Ergebnisse")
        frontend_btn.clicked.connect(lambda: webbrowser.open("http://localhost:5173/live"))
        frontend_btn.setMinimumHeight(40)
        frontend_btn.setMinimumWidth(180)
        h_layout.addWidget(frontend_btn)

        h_layout.addStretch()

        # Status Label
        self.status_label = QLabel("● Server gestoppt")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
        h_layout.addWidget(self.status_label)

        # Zentriere horizontal layout vertikal
        main_layout.addStretch()
        main_layout.addLayout(h_layout)
        main_layout.addStretch()

        group.setLayout(main_layout)
        return group

    def create_candidates_panel(self):
        """Erstellt das Kandidaten-Panel"""
        # Container Widget für Panel + Spacer
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        panel = QGroupBox("Kandidaten-Verwaltung")
        panel.setFixedHeight(500)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(12)

        # Tabelle
        self.candidates_table = QTableWidget()
        self.candidates_table.setColumnCount(3)
        self.candidates_table.setHorizontalHeaderLabels(["ID", "Name", "Beschreibung"])
        self.candidates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.candidates_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.candidates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.candidates_table.setAlternatingRowColors(True)

        # Verstecke die Zeilennummern-Spalte
        self.candidates_table.verticalHeader().setVisible(False)

        layout.addWidget(self.candidates_table)

        # Button-Leiste
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        add_btn = QPushButton("➕ Hinzufügen")
        add_btn.clicked.connect(self.add_candidate)
        add_btn.setMinimumHeight(40)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏ Bearbeiten")
        edit_btn.clicked.connect(self.edit_candidate)
        edit_btn.setMinimumHeight(40)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("✕ Löschen")
        delete_btn.clicked.connect(self.delete_candidate)
        delete_btn.setMinimumHeight(40)
        button_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("↻ Aktualisieren")
        refresh_btn.clicked.connect(self.refresh_candidates)
        refresh_btn.setMinimumHeight(40)
        button_layout.addWidget(refresh_btn)

        reset_table_btn = QPushButton("✕ DROP TABLE")
        reset_table_btn.clicked.connect(self.reset_table)
        reset_table_btn.setMinimumHeight(40)
        reset_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        button_layout.addWidget(reset_table_btn)

        layout.addLayout(button_layout)

        panel.setLayout(layout)
        container_layout.addWidget(panel)

        # Spacer für leeren Bereich bei großen Fenstern
        container_layout.addStretch()

        return container

    def create_admin_actions(self):
        """Erstellt Admin-Aktionen horizontal"""
        group = QGroupBox("Admin-Aktionen")
        group.setFixedHeight(95)

        # Haupt-Layout (vertikal für Zentrierung)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)

        # Horizontales Layout für Buttons
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)

        unlock_btn = QPushButton("⚡ Clients entsperren")
        unlock_btn.clicked.connect(self.unlock_clients)
        unlock_btn.setMinimumHeight(45)
        h_layout.addWidget(unlock_btn)

        reset_btn = QPushButton("↻ Wahl zurücksetzen")
        reset_btn.clicked.connect(self.reset_votes)
        reset_btn.setMinimumHeight(45)
        h_layout.addWidget(reset_btn)

        export_btn = QPushButton("📄 Excel exportieren")
        export_btn.clicked.connect(self.export_excel)
        export_btn.setMinimumHeight(45)
        h_layout.addWidget(export_btn)

        title_btn = QPushButton("✏ Titel ändern")
        title_btn.clicked.connect(self.change_title)
        title_btn.setMinimumHeight(45)
        h_layout.addWidget(title_btn)

        # Zentriere horizontal layout vertikal
        main_layout.addStretch()
        main_layout.addLayout(h_layout)
        main_layout.addStretch()

        group.setLayout(main_layout)
        return group

    def apply_stylesheet(self):
        """Wendet Dark Mode Styles an"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e293b;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e2e8f0;
            }
            QPushButton {
                background-color: #586cc7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #627ae2;
            }
            QPushButton:pressed {
                background-color: #627ae2;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
            QTableWidget {
                border: 1px solid #334155;
                border-radius: 4px;
                background-color: #1e293b;
                gridline-color: #334155;
                color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
                background-color: #1e293b;
            }
            QTableWidget::item:alternate {
                background-color: #1a2332;
            }
            QTableWidget::item:selected {
                background-color: #586cc7 !important;
                color: white !important;
            }
            QTableWidget::item:alternate:selected {
                background-color: #586cc7 !important;
                color: white !important;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #0f172a;
                border: none;
                border-bottom: 2px solid #586cc7;
                border-right: 1px solid #334155;
            }
            QHeaderView::section {
                background-color: #0f172a;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #586cc7;
                font-weight: bold;
                color: #e2e8f0;
            }
            QHeaderView::section:vertical {
                background-color: #0f172a;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
                color: #94a3b8;
            }
            QTextEdit {
                border: 1px solid #334155;
                border-radius: 4px;
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 8px;
            }
            QLineEdit {
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                background-color: #1e293b;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 2px solid #586cc7;
            }
            QLabel {
                color: #e2e8f0;
            }
            QDialog {
                background-color: #1e293b;
            }
            QMessageBox {
                background-color: #1e293b;
            }
            QMessageBox QLabel {
                color: #e2e8f0;
            }
        """)

    # === SERVER-FUNKTIONEN ===

    def start_server(self):
        """Startet den Server"""
        if self.server_running:
            return

        self.server_thread = ServerThread()
        self.server_thread.start()

        self.server_running = True
        self.status_label.setText("● Server läuft")
        self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Starte Auto-Update
        self.update_timer.start(2000)

        QMessageBox.information(self, "Server gestartet",
                               "Server läuft auf http://localhost:8000")

    def stop_server(self):
        """Stoppt den Server (Info)"""
        QMessageBox.warning(self, "Server stoppen",
                           "Der Server kann nur durch Schließen der Anwendung gestoppt werden.")

    # === KANDIDATEN-FUNKTIONEN ===

    def refresh_candidates(self):
        """Lädt Kandidaten neu"""
        self.candidates_data = self.db.get_candidates()
        self.candidates_table.setRowCount(0)

        for candidate in self.candidates_data:
            row = self.candidates_table.rowCount()
            self.candidates_table.insertRow(row)

            self.candidates_table.setItem(row, 0, QTableWidgetItem(str(candidate['id'])))
            self.candidates_table.setItem(row, 1, QTableWidgetItem(candidate['name']))
            self.candidates_table.setItem(row, 2, QTableWidgetItem(candidate.get('description', '')))

    def add_candidate(self):
        """Öffnet Dialog zum Hinzufügen"""
        dialog = CandidateDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein")
                return

            self.db.add_candidate(data['name'], data['description'])
            self.refresh_candidates()
            self.refresh_results()
            QMessageBox.information(self, "Erfolg", "Kandidat hinzugefügt")

    def edit_candidate(self):
        """Öffnet Dialog zum Bearbeiten"""
        selected = self.candidates_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Kandidaten")
            return

        row = self.candidates_table.currentRow()
        candidate = self.candidates_data[row]

        dialog = CandidateDialog(self, candidate)
        if dialog.exec():
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein")
                return

            self.db.update_candidate(candidate['id'], data['name'], data['description'])
            self.refresh_candidates()
            self.refresh_results()
            QMessageBox.information(self, "Erfolg", "Kandidat aktualisiert")

    def delete_candidate(self):
        """Löscht Kandidat"""
        selected = self.candidates_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Kandidaten")
            return

        row = self.candidates_table.currentRow()
        candidate = self.candidates_data[row]

        reply = QMessageBox.question(
            self, "Löschen bestätigen",
            f"Kandidat '{candidate['name']}' wirklich löschen?\n"
            "Alle Stimmen für diesen Kandidaten werden ebenfalls gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_candidate(candidate['id'])
            self.refresh_candidates()
            self.refresh_results()
            QMessageBox.information(self, "Erfolg", "Kandidat gelöscht")

    def reset_table(self):
        """Löscht die gesamte Datenbank und erstellt sie neu"""
        reply = QMessageBox.question(
            self, "Datenbank zurücksetzen",
            "WARNUNG: Die gesamte Datenbank wird gelöscht und neu erstellt!\n\n"
            "- Alle Kandidaten werden gelöscht\n"
            "- Alle Stimmen werden gelöscht\n"
            "- Alle Client-Informationen werden gelöscht\n"
            "- Alle Einstellungen werden zurückgesetzt\n\n"
            "Möchten Sie wirklich fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lösche und erstelle alle Tabellen neu
            conn = self.db._get_connection()
            cursor = conn.cursor()

            # Lösche alle Tabellen
            cursor.execute("DROP TABLE IF EXISTS votes")
            cursor.execute("DROP TABLE IF EXISTS candidates")
            cursor.execute("DROP TABLE IF EXISTS clients")
            cursor.execute("DROP TABLE IF EXISTS settings")

            conn.commit()
            conn.close()

            # Erstelle Tabellen neu
            self.db._init_database()

            self.refresh_candidates()
            self.refresh_results()
            QMessageBox.information(self, "Erfolg", "Datenbank wurde komplett zurückgesetzt und neu erstellt")

    # === ERGEBNIS-FUNKTIONEN ===

    def refresh_results(self):
        """Aktualisiert Ergebnisse - Nicht mehr verwendet, da Live-Ergebnisse entfernt wurden"""
        pass

    # === ADMIN-FUNKTIONEN ===

    def unlock_clients(self):
        """Entsperrt Clients und löst Reload aus"""
        reply = QMessageBox.question(
            self, "Clients entsperren",
            "Alle Clients für eine neue Abstimmungsrunde entsperren?\n\n"
            "Alle Client-Browser werden zur Startseite weitergeleitet.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.unlock_clients()

            # Sende Unlock-Broadcast über WebSocket (löst Client-Reload aus)
            try:
                import asyncio
                from websocket_manager import WebSocketManager

                # Hole die WebSocket-Manager-Instanz aus der API
                # Dies wird über den bereits laufenden Server kommuniziert
                requests.post(f"{self.api_base}/api/admin/unlock", timeout=2)

            except Exception as e:
                print(f"WebSocket-Broadcast-Fehler: {e}")

            QMessageBox.information(self, "Erfolg", "Alle Clients wurden entsperrt und neu geladen")

    def reset_votes(self):
        """Setzt Votes zurück"""
        reply = QMessageBox.question(
            self, "Wahl zurücksetzen",
            "Alle Stimmen löschen? Kandidaten bleiben erhalten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.reset_votes()
            self.refresh_results()
            QMessageBox.information(self, "Erfolg", "Alle Stimmen wurden zurückgesetzt")

    def export_excel(self):
        """Exportiert als Excel"""
        try:
            response = requests.get(f"{self.api_base}/api/export", timeout=10)
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"abstimmung_ergebnisse_{timestamp}.xlsx"
                
                # Open file save dialog
                from PyQt6.QtWidgets import QFileDialog
                filepath, _ = QFileDialog.getSaveFileName(
                    self,
                    "Excel-Datei speichern",  # Dialog title
                    str(Path.home() / "Downloads" / filename),  # Default path and filename
                    "Excel Files (*.xlsx);;All Files (*)"  # File filters
                )
                
                # Check if user cancelled the dialog
                if not filepath:
                    return
                
                # Ensure .xlsx extension
                if not filepath.endswith('.xlsx'):
                    filepath += '.xlsx'

                with open(filepath, "wb") as f:
                    f.write(response.content)

                QMessageBox.information(self, "Export erfolgreich",
                                       f"Datei gespeichert:\n{filepath}")
            else:
                raise Exception("Export fehlgeschlagen")
        except Exception as e:
            QMessageBox.critical(self, "Fehler",
                               f"Excel-Export fehlgeschlagen:\n{str(e)}\n\nServer muss laufen!")

    def change_title(self):
        """Ändert den Wahl-title"""
        try:
            # Hole aktuellen title
            response = requests.get(f"{self.api_base}/api/settings/vote-title", timeout=2)
            current_title = "vote_title"
            if response.status_code == 200:
                current_title = response.json().get("title", current_title)

            # Dialog für neuen title
            from PyQt6.QtWidgets import QInputDialog
            new_title, ok = QInputDialog.getText(
                self,
                "Titel ändern",
                "Neuer Titel für die Wahlseite:",
                QLineEdit.EchoMode.Normal,
                current_title
            )

            if ok and new_title.strip():
                # Setze neuen title
                response = requests.post(
                    f"{self.api_base}/api/settings/vote-title",
                    params={"title": new_title.strip()},
                    timeout=2
                )

                if response.status_code == 200:
                    QMessageBox.information(self, "Erfolg", f"title geändert zu:\n\"{new_title.strip()}\"")
                else:
                    raise Exception("Titel konnte nicht gesetzt werden")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Titel-Änderung fehlgeschlagen:\n{str(e)}\n\nServer muss laufen!")

    def closeEvent(self, event):
        """Handler für Fenster-Schließen"""
        self.update_timer.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Setze App-Metadaten
    app.setApplicationName("easyWahl Admin")
    app.setOrganizationName("easyWahl")

    # Erstelle und zeige Hauptfenster
    window = AdminGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
