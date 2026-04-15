"""
Client lourd minimal pour explorer les AAV.
Phase 1 :
- afficher la liste des AAV
- afficher les détails d'un AAV sélectionné
- filtrer par discipline et type
"""

import tkinter as tk
from tkinter import ttk, messagebox

from api_client import APIClient


class AAVApp(tk.Tk):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()

        self.title("L'Architecte du Savoir - Client lourd")
        self.geometry("1000x600")

        # Client API
        self.api = APIClient()

        # Données actuellement affichées
        self.current_aavs = []

        # Variables des filtres
        self.discipline_var = tk.StringVar()
        self.type_var = tk.StringVar()

        self._build_ui()
        self.load_aavs()

    def _build_ui(self):
        """Construit l'interface graphique principale."""

        # Frame principale
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # -------------------------------
        # Zone filtres
        # -------------------------------
        filters_frame = ttk.LabelFrame(main_frame, text="Filtres", padding=10)
        filters_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filters_frame, text="Discipline :").grid(row=0, column=0, padx=5, pady=5)
        discipline_entry = ttk.Entry(filters_frame, textvariable=self.discipline_var, width=25)
        discipline_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filters_frame, text="Type :").grid(row=0, column=2, padx=5, pady=5)
        type_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.type_var,
            values=["", "Atomique", "Composite (Chapitre)"],
            state="readonly",
            width=22
        )
        type_combo.grid(row=0, column=3, padx=5, pady=5)
        type_combo.current(0)

        ttk.Button(filters_frame, text="Appliquer", command=self.load_aavs).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(filters_frame, text="Réinitialiser", command=self.reset_filters).grid(row=0, column=5, padx=5, pady=5)

        # -------------------------------
        # Zone contenu
        # -------------------------------
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)

        # Colonne gauche : liste des AAV
        left_frame = ttk.LabelFrame(content_frame, text="Liste des AAV", padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.tree = ttk.Treeview(
            left_frame,
            columns=("id", "nom", "discipline", "type"),
            show="headings",
            height=20
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("discipline", text="Discipline")
        self.tree.heading("type", text="Type")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nom", width=250)
        self.tree.column("discipline", width=150)
        self.tree.column("type", width=160)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_aav)

        # Colonne droite : détail
        right_frame = ttk.LabelFrame(content_frame, text="Détail de l'AAV", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)

        self.detail_text = tk.Text(right_frame, wrap="word", state="disabled")
        self.detail_text.pack(fill="both", expand=True)

    def load_aavs(self):
        """Charge les AAV depuis l'API et remplit le tableau."""
        try:
            discipline = self.discipline_var.get().strip() or None
            type_aav = self.type_var.get().strip() or None

            self.current_aavs = self.api.get_aavs(discipline=discipline, type_aav=type_aav)

            # Vider l'ancien contenu du tableau
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Remplir avec les nouveaux AAV
            for aav in self.current_aavs:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        aav["id_aav"],
                        aav["nom"],
                        aav["discipline"],
                        aav["type_aav"]
                    )
                )

            self.clear_details()

        except Exception as e:
            messagebox.showerror("Erreur API", f"Impossible de charger les AAV :\n{e}")

    def on_select_aav(self, event):
        """Affiche le détail de l'AAV sélectionné dans le tableau."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        if not values:
            return

        id_aav = values[0]

        try:
            aav = self.api.get_aav(id_aav)

            texte = (
                f"ID : {aav['id_aav']}\n\n"
                f"Nom : {aav['nom']}\n\n"
                f"Discipline : {aav['discipline']}\n\n"
                f"Enseignement : {aav['enseignement']}\n\n"
                f"Type : {aav['type_aav']}\n\n"
                f"Type d'évaluation : {aav['type_evaluation']}\n\n"
                f"Pré-requis : {aav.get('prerequis_ids', [])}\n\n"
                f"Description :\n{aav['description_markdown']}"
            )

            self.detail_text.configure(state="normal")
            self.detail_text.delete("1.0", tk.END)
            self.detail_text.insert(tk.END, texte)
            self.detail_text.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Erreur API", f"Impossible de charger le détail de l'AAV :\n{e}")

    def clear_details(self):
        """Vide la zone de détail."""
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.configure(state="disabled")

    def reset_filters(self):
        """Réinitialise les filtres puis recharge la liste."""
        self.discipline_var.set("")
        self.type_var.set("")
        self.load_aavs()


if __name__ == "__main__":
    app = AAVApp()
    app.mainloop()