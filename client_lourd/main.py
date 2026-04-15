from __future__ import annotations

import flet as ft
import requests

from api_client import APIClient


class AAVExplorerApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.api = APIClient()
        self.current_aavs: list[dict] = []
        self.selected_aav: dict | None = None
        self.current_learners: list[dict] = []

        self.page.title = "L'Architecte du Savoir - Client lourd"
        self.page.window_width = 1300
        self.page.window_height = 760
        self.page.padding = 16
        self.page.scroll = ft.ScrollMode.AUTO

        # =========================
        # AAV controls
        # =========================
        self.discipline_field = ft.TextField(
            label="Discipline",
            hint_text="Ex: Mathématiques",
            expand=1,
        )

        self.type_dropdown = ft.Dropdown(
            label="Type",
            width=220,
            options=[
                ft.dropdown.Option(""),
                ft.dropdown.Option("Atomique"),
                ft.dropdown.Option("Composite (Chapitre)"),
            ],
            value="",
        )

        self.load_button = ft.FilledButton("Appliquer", on_click=self.load_aavs)
        self.reset_button = ft.OutlinedButton("Réinitialiser", on_click=self.reset_filters)
        self.create_button = ft.FilledButton("Créer AAV", on_click=self.open_create_dialog)

        self.edit_prereq_button = ft.OutlinedButton(
            "Modifier prérequis",
            on_click=self.open_edit_prereq_dialog,
            disabled=True,
        )

        self.aav_list = ft.ListView(
            expand=True,
            spacing=6,
            auto_scroll=False,
        )

        self.detail_panel = ft.Container(
            content=ft.Text("Sélectionne un AAV dans la liste."),
            padding=16,
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=12,
        )

        # =========================
        # Phase 3 controls
        # =========================
        self.learner_dropdown = ft.Dropdown(
            label="Apprenant",
            width=300,
            options=[],
        )

        self.load_learner_button = ft.FilledButton(
            "Charger apprenant",
            on_click=self.load_learner_summary,
        )

        self.learner_summary_panel = ft.Container(
            content=ft.Text("Choisis un apprenant puis clique sur 'Charger apprenant'."),
            padding=16,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=12,
        )

        self.sim_aav_id_field = ft.TextField(
            label="ID AAV cible",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.sim_exercice_field = ft.TextField(
            label="ID exercice",
            width=180,
            value="1001",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.sim_score_field = ft.TextField(
            label="Score (0 à 1)",
            width=180,
            value="0.8",
        )

        self.simulate_button = ft.FilledButton(
            "Simuler Tentative",
            on_click=self.simulate_tentative_action,
        )

        self.status_text = ft.Text("", color=ft.Colors.RED)

        self.build_layout()
        self.load_aavs()
        self.load_learners()

    # =====================================================
    # LAYOUT
    # =====================================================

    def build_layout(self) -> None:
        aav_filters = ft.Row(
            controls=[
                self.discipline_field,
                self.type_dropdown,
                self.load_button,
                self.reset_button,
                self.create_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        left_column = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Liste des AAV", size=20, weight=ft.FontWeight.BOLD),
                    self.aav_list,
                ],
                expand=True,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=12,
            expand=1,
        )

        right_column = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Détail de l'AAV", size=20, weight=ft.FontWeight.BOLD),
                            self.edit_prereq_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.detail_panel,
                ],
                expand=True,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=12,
            expand=1,
        )

        phase3_block = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Phase 3 - Suivi apprenant", size=22, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            self.learner_dropdown,
                            self.load_learner_button,
                        ]
                    ),
                    self.learner_summary_panel,
                    ft.Divider(),
                    ft.Text("Simulation de tentative", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            self.sim_aav_id_field,
                            self.sim_exercice_field,
                            self.sim_score_field,
                            self.simulate_button,
                        ],
                        wrap=True,
                    ),
                ],
                tight=True,
                spacing=12,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=12,
        )

        self.page.add(
            ft.Column(
                controls=[
                    ft.Text("Dashboard AAV", size=28, weight=ft.FontWeight.BOLD),
                    aav_filters,
                    self.status_text,
                    ft.Row(
                        controls=[left_column, right_column],
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    phase3_block,
                ],
                expand=True,
            )
        )

    # =====================================================
    # COMMON
    # =====================================================

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED if error else ft.Colors.GREEN
        self.page.update()

    def get_next_aav_id(self) -> int:
        if not self.current_aavs:
            return 1
        ids = [aav["id_aav"] for aav in self.current_aavs if "id_aav" in aav]
        return max(ids) + 1 if ids else 1

    # =====================================================
    # AAV - LIST / DETAIL
    # =====================================================

    def reset_filters(self, e: ft.ControlEvent) -> None:
        self.discipline_field.value = ""
        self.type_dropdown.value = ""
        self.load_aavs()

    def load_aavs(self, e: ft.ControlEvent | None = None) -> None:
        try:
            self.set_status("", error=False)

            discipline = self.discipline_field.value.strip() or None
            type_aav = self.type_dropdown.value or None

            self.current_aavs = self.api.get_aavs(
                discipline=discipline,
                type_aav=type_aav,
            )

            self.aav_list.controls.clear()

            if not self.current_aavs:
                self.aav_list.controls.append(ft.Text("Aucun AAV trouvé."))
            else:
                for aav in self.current_aavs:
                    tile = ft.ListTile(
                        title=ft.Text(f"{aav['id_aav']} - {aav['nom']}"),
                        subtitle=ft.Text(f"{aav['discipline']} | {aav['type_aav']}"),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=lambda evt, aav_id=aav["id_aav"]: self.show_details(aav_id),
                    )
                    self.aav_list.controls.append(ft.Card(content=tile))

            self.detail_panel.content = ft.Text("Sélectionne un AAV dans la liste.")
            self.selected_aav = None
            self.edit_prereq_button.disabled = True
            self.page.update()

        except requests.RequestException as exc:
            self.set_status(f"Erreur réseau/API : {exc}", error=True)
        except Exception as exc:
            self.set_status(f"Erreur inattendue : {exc}", error=True)

    def show_details(self, id_aav: int) -> None:
        try:
            aav = self.api.get_aav(id_aav)
            self.selected_aav = aav
            self.edit_prereq_button.disabled = False

            details = ft.Column(
                controls=[
                    ft.Text(f"ID : {aav['id_aav']}", selectable=True),
                    ft.Text(f"Nom : {aav['nom']}", selectable=True),
                    ft.Text(f"Discipline : {aav['discipline']}", selectable=True),
                    ft.Text(f"Enseignement : {aav['enseignement']}", selectable=True),
                    ft.Text(f"Type : {aav['type_aav']}", selectable=True),
                    ft.Text(f"Évaluation : {aav['type_evaluation']}", selectable=True),
                    ft.Text(f"Pré-requis : {aav.get('prerequis_ids', [])}", selectable=True),
                    ft.Divider(),
                    ft.Text("Description", weight=ft.FontWeight.BOLD),
                    ft.Text(aav["description_markdown"], selectable=True),
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            )

            self.detail_panel.content = details
            self.page.update()

        except requests.RequestException as exc:
            self.set_status(f"Erreur API détail : {exc}", error=True)
        except Exception as exc:
            self.set_status(f"Erreur inattendue : {exc}", error=True)

    # =====================================================
    # PHASE 2 - CREATE AAV
    # =====================================================

    def open_create_dialog(self, e):
        self.dialog_error = ft.Text("", color=ft.Colors.RED)

        self.id_field = ft.TextField(
            label="ID *",
            value=str(self.get_next_aav_id()),
            hint_text="ID unique",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.nom_field = ft.TextField(label="Nom *")
        self.libelle_field = ft.TextField(label="Libellé intégration * (min 5 caractères)")
        self.discipline_field_form = ft.TextField(label="Discipline *")
        self.enseignement_field = ft.TextField(label="Enseignement *")
        self.description_field = ft.TextField(
            label="Description * (min 10 caractères)",
            multiline=True,
        )

        self.type_dropdown_form = ft.Dropdown(
            label="Type AAV *",
            value="Atomique",
            options=[
                ft.dropdown.Option("Atomique"),
                ft.dropdown.Option("Composite (Chapitre)"),
            ],
        )

        self.prerequis_field = ft.TextField(label="Pré-requis (ids séparés par ,)")

        self.type_eval_dropdown = ft.Dropdown(
            label="Type évaluation *",
            value="Humaine",
            options=[
                ft.dropdown.Option("Humaine"),
                ft.dropdown.Option("Calcul Automatisé"),
                ft.dropdown.Option("Compréhension par Chute"),
                ft.dropdown.Option("Validation par Invention"),
                ft.dropdown.Option("Exercice de Critique"),
                ft.dropdown.Option("Évaluation par les Pairs"),
                ft.dropdown.Option("Agrégation (Composite)"),
            ],
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Créer un AAV"),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    controls=[
                        ft.Text("Composite : au moins un pré-requis.", size=12),
                        self.id_field,
                        self.nom_field,
                        self.libelle_field,
                        self.discipline_field_form,
                        self.enseignement_field,
                        self.type_dropdown_form,
                        self.description_field,
                        self.prerequis_field,
                        self.type_eval_dropdown,
                        self.dialog_error,
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: self.close_dialog()),
                ft.FilledButton("Créer", on_click=self.create_aav_action),
            ],
        )

        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)

        self.dialog.open = True
        self.page.update()

    def close_dialog(self):
        self.dialog.open = False
        self.page.update()

    def create_aav_action(self, e):
        self.dialog_error.value = ""

        try:
            if not self.id_field.value:
                self.dialog_error.value = "ID obligatoire"
                self.page.update()
                return

            if not self.nom_field.value:
                self.dialog_error.value = "Nom obligatoire"
                self.page.update()
                return

            if not self.libelle_field.value or len(self.libelle_field.value.strip()) < 5:
                self.dialog_error.value = "Libellé obligatoire (min 5 caractères)"
                self.page.update()
                return

            if not self.discipline_field_form.value:
                self.dialog_error.value = "Discipline obligatoire"
                self.page.update()
                return

            if not self.enseignement_field.value:
                self.dialog_error.value = "Enseignement obligatoire"
                self.page.update()
                return

            if not self.description_field.value or len(self.description_field.value.strip()) < 10:
                self.dialog_error.value = "Description obligatoire (min 10 caractères)"
                self.page.update()
                return

            prerequis = []
            if self.prerequis_field.value and self.prerequis_field.value.strip():
                prerequis = [
                    int(x.strip())
                    for x in self.prerequis_field.value.split(",")
                    if x.strip()
                ]

            type_aav = self.type_dropdown_form.value

            if type_aav == "Composite (Chapitre)" and not prerequis:
                self.dialog_error.value = "Un AAV composite doit avoir au moins un pré-requis."
                self.page.update()
                return

            payload = {
                "id_aav": int(self.id_field.value),
                "nom": self.nom_field.value.strip(),
                "libelle_integration": self.libelle_field.value.strip(),
                "discipline": self.discipline_field_form.value.strip(),
                "enseignement": self.enseignement_field.value.strip(),
                "type_aav": type_aav,
                "description_markdown": self.description_field.value.strip(),
                "prerequis_ids": prerequis,
                "prerequis_externes_codes": [],
                "code_prerequis_interdisciplinaire": None,
                "type_evaluation": self.type_eval_dropdown.value,
            }

            created = self.api.create_aav(payload)
            self.close_dialog()
            self.load_aavs()
            self.set_status(f"AAV créé : {created['nom']}")

        except ValueError:
            self.dialog_error.value = "ID / prérequis invalides"
            self.page.update()
        except Exception as exc:
            self.dialog_error.value = str(exc)
            self.page.update()

    # =====================================================
    # PHASE 2 - EDIT PREREQUIS
    # =====================================================

    def open_edit_prereq_dialog(self, e):
        if not self.selected_aav:
            self.set_status("Aucun AAV sélectionné.", error=True)
            return

        prerequis_actuels = self.selected_aav.get("prerequis_ids", [])
        prerequis_txt = ",".join(str(x) for x in prerequis_actuels)

        self.edit_prereq_error = ft.Text("", color=ft.Colors.RED)

        self.edit_prereq_field = ft.TextField(
            label="Pré-requis (IDs séparés par des virgules)",
            value=prerequis_txt,
            hint_text="Ex : 1,2,3",
        )

        self.edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Modifier les pré-requis de l'AAV {self.selected_aav['id_aav']}"),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    controls=[
                        ft.Text(f"Nom : {self.selected_aav['nom']}"),
                        self.edit_prereq_field,
                        self.edit_prereq_error,
                    ],
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: self.close_edit_dialog()),
                ft.FilledButton("Enregistrer", on_click=self.save_prerequis_action),
            ],
        )

        if self.edit_dialog not in self.page.overlay:
            self.page.overlay.append(self.edit_dialog)

        self.edit_dialog.open = True
        self.page.update()

    def save_prerequis_action(self, e):
        if not self.selected_aav:
            return

        self.edit_prereq_error.value = ""

        try:
            raw_value = self.edit_prereq_field.value.strip()

            prerequis_ids = []
            if raw_value:
                prerequis_ids = [
                    int(x.strip())
                    for x in raw_value.split(",")
                    if x.strip()
                ]

            if self.selected_aav.get("type_aav") == "Composite (Chapitre)" and not prerequis_ids:
                self.edit_prereq_error.value = "Un AAV Composite doit avoir au moins un pré-requis."
                self.page.update()
                return

            updated = self.api.update_aav_prerequis(
                self.selected_aav["id_aav"],
                prerequis_ids,
            )

            self.selected_aav = updated
            self.close_edit_dialog()
            self.show_details(updated["id_aav"])
            self.set_status("Pré-requis mis à jour avec succès.")

        except ValueError:
            self.edit_prereq_error.value = "Les pré-requis doivent être des entiers."
            self.page.update()
        except Exception as exc:
            self.edit_prereq_error.value = str(exc)
            self.page.update()

    def close_edit_dialog(self):
        self.edit_dialog.open = False
        self.page.update()

    # =====================================================
    # PHASE 3 - LEARNERS
    # =====================================================

    def load_learners(self) -> None:
        try:
            learners = self.api.get_learners()
            self.current_learners = learners

            options = []
            for learner in learners:
                learner_id = learner.get("id_apprenant")
                username = learner.get("nom_utilisateur", f"Apprenant {learner_id}")
                options.append(
                    ft.dropdown.Option(
                        key=str(learner_id),
                        text=f"{learner_id} - {username}",
                    )
                )

            self.learner_dropdown.options = options
            if options:
                self.learner_dropdown.value = options[0].key

            self.page.update()

        except Exception as exc:
            self.set_status(
                "Phase 3 : impossible de charger les apprenants. "
                "Vérifie que l'API expose GET /learners/ .",
                error=True,
            )

    def load_learner_summary(self, e):
        if not self.learner_dropdown.value:
            self.set_status("Choisis un apprenant.", error=True)
            return

        try:
            learner_id = int(self.learner_dropdown.value)
            summary = self.api.get_learner_summary(learner_id)

            content = ft.Column(
                controls=[
                    ft.Text(f"ID apprenant : {summary.get('id_apprenant', learner_id)}"),
                    ft.Text(f"Total AAV suivis : {summary.get('total', 'N/A')}"),
                    ft.Text(f"AAV maitrises : {summary.get('maitrise', 'N/A')}"),
                    ft.Text(f"AAV en cours : {summary.get('en_cours', 'N/A')}"),
                    ft.Text(f"AAV non commences : {summary.get('non_commence', 'N/A')}"),
                    ft.Text(f"Taux de maitrise global : {summary.get('taux_maitrise_global', 'N/A')}%"),
                ],
                tight=True,
            )

            self.learner_summary_panel.content = content
            self.set_status("Résumé apprenant chargé.")
            self.page.update()

        except Exception as exc:
            self.set_status(
                "Impossible de charger le résumé apprenant. "
                "Vérifie que l'API expose GET /learners/{id}/learning-status/summary .",
                error=True,
            )

    def simulate_tentative_action(self, e):
        if not self.learner_dropdown.value:
            self.set_status("Choisis d'abord un apprenant.", error=True)
            return

        try:
            learner_id = int(self.learner_dropdown.value)
            aav_id = int(self.sim_aav_id_field.value)
            exercice_id = int(self.sim_exercice_field.value)
            score = float(self.sim_score_field.value)

            if score < 0 or score > 1:
                self.set_status("Le score doit être entre 0 et 1.", error=True)
                return

            payload = {
                "id_apprenant": learner_id,
                "id_aav_cible": aav_id,
                "id_exercice_ou_evenement": exercice_id,
                "score_obtenu": score,
            }

            created_attempt = self.api.create_attempt(payload)
            process_result = self.api.process_attempt(created_attempt["id"])
            self.set_status(process_result.get("message", "Tentative traitee avec succes."))
            self.load_learner_summary(None)

        except ValueError:
            self.set_status("Les champs simulation doivent être numériques.", error=True)
        except Exception as exc:
            self.set_status(
                "Impossible de simuler la tentative. "
                "Vérifie que l'API expose POST /attempts puis POST /attempts/{id}/process .",
                error=True,
            )


def main(page: ft.Page) -> None:
    AAVExplorerApp(page)


if __name__ == "__main__":
    ft.run(main)
