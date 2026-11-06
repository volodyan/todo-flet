import os
import flet as ft
from supabase import create_client, Client

# --- Инициализация Supabase ---
# Ключи не в коде: локально — os.environ, при сборке APK — через flet build с секретами.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Не заданы SUPABASE_URL и SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Цвета для приоритетов
PRIORITY_COLORS = {
    "high": ft.Colors.RED_400,
    "medium": ft.Colors.ORANGE_400,
    "low": ft.Colors.GREY_500,
}


def main(page: ft.Page):
    page.title = "Задачи"
    page.padding = 16

    # ---------- Элементы формы ----------
    title_input = ft.TextField(
        label="Название задачи",
        hint_text="Что нужно сделать?",
        expand=True,
    )

    priority_dropdown = ft.Dropdown(
        label="Приоритет",
        value="medium",
        width=150,
        options=[
            ft.DropdownOption(key="low", text="Низкий"),
            ft.DropdownOption(key="medium", text="Средний"),
            ft.DropdownOption(key="high", text="Высокий"),
        ],
    )

    add_button = ft.Button("Добавить", icon=ft.Icons.ADD)

    # ---------- Список задач ----------
    # ListView обязателен с expand=True, иначе не займёт доступное место
    tasks_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding(top=16))

    # ---------- Функции работы с БД ----------

    def load_tasks():
        """Загружает все задачи и перерисовывает список."""
        tasks_list.controls.clear()
        try:
            resp = supabase.table("tasks").select("*").order("created_at", desc=True).execute()
            tasks = resp.data or []
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(...)))
            return

        if not tasks:
            tasks_list.controls.append(
                ft.Text("Пока нет задач. Добавь первую!", color=ft.Colors.GREY_600)
            )
        else:
            for task in tasks:
                tasks_list.controls.append(build_task_row(task))

        page.update()

    def build_task_row(task: dict) -> ft.Row:
        """Собирает одну строку задачи из данных Supabase."""
        task_id = task["id"]
        is_done = task.get("is_done", False)
        priority = task.get("priority", "medium")

        def on_checkbox_change(e, tid=task_id):
            try:
                supabase.table("tasks").update({"is_done": e.control.value}).eq("id", tid).execute()
            except Exception as ex:
                page.show_dialog(ft.SnackBar(ft.Text(...)))

        def on_delete(e, tid=task_id):
            try:
                supabase.table("tasks").delete().eq("id", tid).execute()
                load_tasks()  # перезагружаем список после удаления
            except Exception as ex:
                page.show_dialog(ft.SnackBar(ft.Text(...)))

        return ft.Row(
            controls=[
                ft.Checkbox(value=is_done, on_change=on_checkbox_change),
                ft.Text(
                    task["title"],
                    expand=True,
                    size=16,
                    # зачёркиваем выполненные
                    style=ft.TextStyle(
                        decoration=ft.TextDecoration.LINE_THROUGH if is_done else None,
                        color=ft.Colors.GREY_500 if is_done else None,
                    ),
                ),
                ft.Text(
                    priority.upper(),
                    size=12,
                    color=PRIORITY_COLORS.get(priority, ft.Colors.GREY),
                    weight=ft.FontWeight.BOLD,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_300,
                    tooltip="Удалить",
                    on_click=on_delete,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def on_add_click(e):
        """Добавляет новую задачу."""
        title = title_input.value.strip()
        if not title:
            page.show_dialog(ft.SnackBar(ft.Text(...)))

        try:
            supabase.table("tasks").insert({
                "title": title,
                "priority": priority_dropdown.value,
                "is_done": False,
            }).execute()
            title_input.value = ""
            load_tasks()
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(...)))

    add_button.on_click = on_add_click

    # ---------- Компоновка ----------
    page.add(
        ft.Row(
            controls=[title_input, priority_dropdown, add_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        tasks_list,
    )

    # Первичная загрузка при старте
    load_tasks()


ft.run(main)