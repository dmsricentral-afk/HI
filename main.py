"""
main.py - Kivy/Android port of the Manpower Allocation & Budget tool.

Reuses the exact same data layer as the Windows desktop app:
  - database.py        (SQLite connection + HR login/auth - unchanged)
  - manpower_data.py    (all CRUD + summary logic - unchanged business logic,
                          just stripped of Tkinter/openpyxl imports)

Only the presentation layer is new here, built in Kivy so it can be
packaged into an Android .apk via buildozer (see buildozer.spec and
README_ANDROID.md in this same folder).

Screens:
  LoginScreen           - HR Login (same users table / verify_login())
  ChangePasswordScreen  - forced on first login (must_change_password)
  MainScreen            - Dashboard tab (budget cards + category
                           breakdown) and Roster tab (filter, add,
                           edit, delete positions, export CSV)
"""

import os
import csv
import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import database as db
import manpower_data as ma


# ---------------------------------------------------------------
# Theme - same maroon/gold palette as the desktop app
# ---------------------------------------------------------------
def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, a)


COLOR_BG = hexc("f3ece6")
COLOR_PANEL = hexc("ffffff")
COLOR_ACCENT = hexc("4e0000")
COLOR_ACCENT_DARK = hexc("2d0000")
COLOR_GOLD = hexc("b8860b")
COLOR_MUTED = hexc("7a6f6a")
COLOR_BORDER = hexc("e3d3d6")
COLOR_TEXT = hexc("2a1a1a")
COLOR_GOOD = hexc("2e7d32")
COLOR_BAD = hexc("c0392b")

Window.clearcolor = COLOR_BG


# ---------------------------------------------------------------
# Small styled building blocks
# ---------------------------------------------------------------
class Card(BoxLayout):
    """A white rounded panel, like the desktop app's Panel.TFrame."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*COLOR_PANEL)
            self._rect = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size


class AccentButton(Button):
    def __init__(self, color=COLOR_ACCENT, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", color)
        kwargs.setdefault("color", (1, 1, 1, 1))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)


def section_label(text, **kw):
    kw.setdefault("color", COLOR_ACCENT_DARK)
    kw.setdefault("bold", True)
    kw.setdefault("font_size", sp(15))
    kw.setdefault("size_hint_y", None)
    kw.setdefault("height", dp(30))
    kw.setdefault("halign", "left")
    lbl = Label(text=text, **kw)
    lbl.bind(size=lambda s, v: setattr(s, "text_size", v))
    return lbl


def error_label():
    lbl = Label(text="", color=COLOR_BAD, size_hint_y=None, height=dp(24),
                font_size=sp(12))
    return lbl


def field(hint, password=False, text=""):
    return TextInput(
        text=text, hint_text=hint, password=password, multiline=False,
        size_hint_y=None, height=dp(46), padding=[dp(12), dp(12), 0, 0],
        background_color=COLOR_PANEL, foreground_color=COLOR_TEXT,
        cursor_color=COLOR_ACCENT,
    )


def info_popup(title, message):
    Popup(
        title=title,
        content=Label(text=message, color=COLOR_TEXT),
        size_hint=(0.8, 0.35),
    ).open()


def confirm_popup(title, message, on_yes):
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    box.add_widget(Label(text=message, color=COLOR_TEXT))
    btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    popup = Popup(title=title, content=box, size_hint=(0.85, 0.4))

    def _yes(*a):
        popup.dismiss()
        on_yes()

    btn_row.add_widget(AccentButton(text="Cancel", color=COLOR_MUTED,
                                     on_release=lambda *a: popup.dismiss()))
    btn_row.add_widget(AccentButton(text="Delete", color=COLOR_BAD, on_release=_yes))
    box.add_widget(btn_row)
    popup.open()


# ---------------------------------------------------------------
# Login
# ---------------------------------------------------------------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = FloatLayout()
        card = Card(orientation="vertical", size_hint=(None, None),
                    size=(dp(340), dp(360)), padding=dp(28), spacing=dp(10),
                    pos_hint={"center_x": 0.5, "center_y": 0.5})

        card.add_widget(Label(text="HR Login", bold=True, font_size=sp(22),
                               color=COLOR_ACCENT_DARK, size_hint_y=None, height=dp(34)))
        card.add_widget(Label(text="Ranaya Silks - Manpower Allocation & Budget",
                               color=COLOR_MUTED, font_size=sp(11),
                               size_hint_y=None, height=dp(30)))

        self.username = field("Username", text=db.DEFAULT_USERNAME)
        self.password = field("Password", password=True)
        self.err = error_label()

        card.add_widget(self.username)
        card.add_widget(self.password)
        card.add_widget(self.err)
        card.add_widget(AccentButton(text="Login", size_hint_y=None, height=dp(48),
                                      on_release=self.try_login))

        root.add_widget(card)
        self.add_widget(root)

    def try_login(self, *a):
        username = self.username.text.strip()
        password = self.password.text
        if not username or not password:
            self.err.text = "Enter both username and password."
            return
        user = db.verify_login(username, password)
        if not user:
            self.err.text = "Incorrect username or password."
            self.password.text = ""
            return
        self.err.text = ""
        app = App.get_running_app()
        app.current_user = user
        if user.get("must_change_password"):
            app.root.current = "change_password"
        else:
            app.root.get_screen("main").refresh_all()
            app.root.current = "main"


class ChangePasswordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = FloatLayout()
        card = Card(orientation="vertical", size_hint=(None, None),
                    size=(dp(340), dp(420)), padding=dp(28), spacing=dp(10),
                    pos_hint={"center_x": 0.5, "center_y": 0.5})

        card.add_widget(Label(text="Set a New Password", bold=True, font_size=sp(19),
                               color=COLOR_ACCENT_DARK, size_hint_y=None, height=dp(30)))
        card.add_widget(Label(text="This is your first login - choose a new password.",
                               color=COLOR_MUTED, font_size=sp(11),
                               size_hint_y=None, height=dp(40)))

        self.old_pw = field("Current Password", password=True)
        self.new_pw = field("New Password", password=True)
        self.confirm_pw = field("Confirm New Password", password=True)
        self.err = error_label()

        card.add_widget(self.old_pw)
        card.add_widget(self.new_pw)
        card.add_widget(self.confirm_pw)
        card.add_widget(self.err)
        card.add_widget(AccentButton(text="Update Password", size_hint_y=None,
                                      height=dp(48), on_release=self.submit))

        root.add_widget(card)
        self.add_widget(root)

    def submit(self, *a):
        app = App.get_running_app()
        username = app.current_user["username"]
        new_pw, confirm = self.new_pw.text, self.confirm_pw.text
        if len(new_pw) < 4:
            self.err.text = "New password must be at least 4 characters."
            return
        if new_pw != confirm:
            self.err.text = "New password and confirmation do not match."
            return
        ok = db.change_password(username, self.old_pw.text, new_pw)
        if not ok:
            self.err.text = "Current password is incorrect."
            return
        self.err.text = ""
        info_popup("Password Updated", "Your password has been changed.")
        app.root.get_screen("main").refresh_all()
        app.root.current = "main"


# ---------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------
class StatTile(Card):
    def __init__(self, caption, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(2), **kwargs)
        self.value_lbl = Label(text="-", bold=True, font_size=sp(20),
                                color=COLOR_ACCENT_DARK, size_hint_y=None, height=dp(30))
        cap_lbl = Label(text=caption, font_size=sp(10), color=COLOR_MUTED,
                         size_hint_y=None, height=dp(18))
        self.add_widget(self.value_lbl)
        self.add_widget(cap_lbl)

    def set_value(self, text):
        self.value_lbl.text = text


class CategoryRow(BoxLayout):
    def __init__(self, cat, **kwargs):
        super().__init__(size_hint_y=None, height=dp(40), padding=[dp(8), 0], **kwargs)
        with self.canvas.before:
            Color(*COLOR_PANEL)
            self._rect = RoundedRectangle(radius=[dp(4)])
        self.bind(pos=self._u, size=self._u)

        def lab(t, w, color=COLOR_TEXT, bold=False):
            l = Label(text=t, color=color, size_hint_x=None, width=dp(w),
                      font_size=sp(11), bold=bold, halign="left", valign="middle")
            l.bind(size=lambda s, v: setattr(s, "text_size", v))
            return l

        self.add_widget(lab(cat["category"], 130, bold=True))
        self.add_widget(lab(f'{cat["current"]}/{cat["allocated"]}', 60))
        vac_color = COLOR_BAD if cat["vacant"] else COLOR_GOOD
        self.add_widget(lab(str(cat["vacant"]), 50, color=vac_color, bold=True))
        self.add_widget(lab(f'\u20b9{cat["budget"]:,.0f}', 90))

    def _u(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size


class DashboardView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kwargs)

        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        top.add_widget(Label(text="Floor:", color=COLOR_TEXT, size_hint_x=None, width=dp(50)))
        self.floor_spinner = Spinner(text=ma.ALL_FLOORS, values=[ma.ALL_FLOORS],
                                      background_color=COLOR_ACCENT, color=(1, 1, 1, 1))
        self.floor_spinner.bind(text=lambda s, v: self.refresh())
        top.add_widget(self.floor_spinner)
        self.add_widget(top)

        tiles = GridLayout(cols=3, size_hint_y=None, height=dp(180), spacing=dp(8))
        self.t_allocated = StatTile("Allocated Seats")
        self.t_current = StatTile("Current Staff")
        self.t_vacant = StatTile("Vacant Seats")
        self.t_budget = StatTile("Budgeted Pay")
        self.t_current_pay = StatTile("Current Pay")
        self.t_vac_pct = StatTile("Vacancy %")
        for t in (self.t_allocated, self.t_current, self.t_vacant,
                  self.t_budget, self.t_current_pay, self.t_vac_pct):
            tiles.add_widget(t)
        self.add_widget(tiles)

        self.add_widget(section_label("Category Breakdown"))
        header = BoxLayout(size_hint_y=None, height=dp(24), padding=[dp(8), 0])
        for t, w in [("Category", 130), ("Cur/Alloc", 60), ("Vac", 50), ("Budget", 90)]:
            l = Label(text=t, color=COLOR_MUTED, bold=True, font_size=sp(10),
                      size_hint_x=None, width=dp(w), halign="left")
            l.bind(size=lambda s, v: setattr(s, "text_size", v))
            header.add_widget(l)
        self.add_widget(header)

        scroll = ScrollView()
        self.cat_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.cat_list.bind(minimum_height=self.cat_list.setter("height"))
        scroll.add_widget(self.cat_list)
        self.add_widget(scroll)

    def refresh_floors(self):
        floors = [ma.ALL_FLOORS] + ma.get_floors()
        self.floor_spinner.values = floors
        if self.floor_spinner.text not in floors:
            self.floor_spinner.text = ma.ALL_FLOORS

    def refresh(self):
        floor = self.floor_spinner.text
        summary = ma.get_category_summary(floor=None if floor == ma.ALL_FLOORS else floor)

        self.t_allocated.set_value(str(summary["total_allocated"]))
        self.t_current.set_value(str(summary["total_current"]))
        self.t_vacant.set_value(str(summary["total_vacant"]))
        self.t_budget.set_value(f'\u20b9{summary["total_budget"]:,.0f}')
        self.t_current_pay.set_value(f'\u20b9{summary["total_current_pay"]:,.0f}')
        self.t_vac_pct.set_value(f'{summary["total_vacancy_pct"]}%')

        self.cat_list.clear_widgets()
        for cat in summary["categories"]:
            self.cat_list.add_widget(CategoryRow(cat))


# ---------------------------------------------------------------
# Roster tab
# ---------------------------------------------------------------
class PositionRow(BoxLayout):
    def __init__(self, pos, on_tap, **kwargs):
        super().__init__(size_hint_y=None, height=dp(56), padding=[dp(10), dp(4)],
                          spacing=dp(2), **kwargs)
        with self.canvas.before:
            Color(*COLOR_PANEL)
            self._rect = RoundedRectangle(radius=[dp(6)])
        self.bind(pos=self._u, size=self._u)
        self.orientation = "vertical"

        vacant = not pos["staff_name"].strip()
        name_text = pos["staff_name"].strip() if not vacant else "VACANT"
        name_color = COLOR_BAD if vacant else COLOR_ACCENT_DARK

        top_row = BoxLayout(size_hint_y=None, height=dp(22))
        top_row.add_widget(Label(text=f'{pos["designation"]}', bold=True, color=COLOR_TEXT,
                                  font_size=sp(13), halign="left",
                                  text_size=(dp(200), None)))
        top_row.add_widget(Label(text=f'\u20b9{pos["salary_package"]:,.0f}', color=COLOR_GOLD,
                                  bold=True, font_size=sp(12), halign="right",
                                  size_hint_x=None, width=dp(90)))
        self.add_widget(top_row)

        bottom_row = BoxLayout(size_hint_y=None, height=dp(20))
        bottom_row.add_widget(Label(text=f'{pos["department"]} - {name_text}',
                                     color=name_color, font_size=sp(11), halign="left",
                                     text_size=(dp(280), None)))
        self.add_widget(bottom_row)

        self.pos_data = pos
        self.on_tap = on_tap

    def _u(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.on_tap(self.pos_data)
            return True
        return super().on_touch_up(touch)


class PositionForm(BoxLayout):
    """Add/Edit form used inside a Popup."""

    def __init__(self, pos_data, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), padding=dp(6), **kwargs)
        self.pos_data = pos_data or {}

        def row(label_text, key, initial=""):
            self.add_widget(Label(text=label_text, color=COLOR_MUTED, size_hint_y=None,
                                   height=dp(18), font_size=sp(11), halign="left",
                                   text_size=(dp(280), None)))
            ti = field("", text=str(self.pos_data.get(key, initial)))
            self.add_widget(ti)
            return ti

        self.floor_in = row("Floor", "floor")
        self.dept_in = row("Department / Counter", "department")
        self.cat_in = row("Category", "category")
        self.desig_in = row("Designation", "designation")
        self.name_in = row("Staff Name (blank = vacant)", "staff_name")
        self.grade_in = row("Grade", "grade")
        self.salary_in = row("Salary Package", "salary_package", initial="0")
        self.gender_in = row("Gender", "gender")

    def collect(self):
        return {
            "floor": self.floor_in.text.strip(),
            "department": self.dept_in.text.strip(),
            "category": self.cat_in.text.strip(),
            "designation": self.desig_in.text.strip(),
            "staff_name": self.name_in.text.strip(),
            "grade": self.grade_in.text.strip(),
            "salary_package": self.salary_in.text.strip() or "0",
            "gender": self.gender_in.text.strip(),
        }


class RosterView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kwargs)

        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.floor_spinner = Spinner(text=ma.ALL_FLOORS, values=[ma.ALL_FLOORS],
                                      background_color=COLOR_ACCENT, color=(1, 1, 1, 1))
        self.dept_spinner = Spinner(text=ma.ALL_DEPARTMENTS, values=[ma.ALL_DEPARTMENTS],
                                     background_color=COLOR_ACCENT, color=(1, 1, 1, 1))
        self.floor_spinner.bind(text=self._floor_changed)
        self.dept_spinner.bind(text=lambda s, v: self.refresh_list())
        top.add_widget(self.floor_spinner)
        top.add_widget(self.dept_spinner)
        self.add_widget(top)

        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        actions.add_widget(AccentButton(text="+ Add Position", color=COLOR_ACCENT,
                                         on_release=lambda *a: self.open_form(None)))
        actions.add_widget(AccentButton(text="Export CSV", color=COLOR_GOLD,
                                         on_release=lambda *a: self.export_csv()))
        self.add_widget(actions)

        scroll = ScrollView()
        self.list_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        self.add_widget(scroll)

    def refresh_floors(self):
        floors = [ma.ALL_FLOORS] + ma.get_floors()
        self.floor_spinner.values = floors
        if self.floor_spinner.text not in floors:
            self.floor_spinner.text = ma.ALL_FLOORS
        self._refresh_depts()
        self.refresh_list()

    def _floor_changed(self, spinner, value):
        self._refresh_depts()
        self.refresh_list()

    def _refresh_depts(self):
        floor = self.floor_spinner.text
        depts = [ma.ALL_DEPARTMENTS] + ma.get_departments(
            None if floor == ma.ALL_FLOORS else floor)
        self.dept_spinner.values = depts
        if self.dept_spinner.text not in depts:
            self.dept_spinner.text = ma.ALL_DEPARTMENTS

    def refresh_list(self):
        floor = self.floor_spinner.text
        dept = self.dept_spinner.text
        positions = ma.list_positions(
            floor=None if floor == ma.ALL_FLOORS else floor,
            department=None if dept == ma.ALL_DEPARTMENTS else dept,
        )
        self.list_box.clear_widgets()
        for p in positions:
            self.list_box.add_widget(PositionRow(p, on_tap=self.open_form))

    def open_form(self, pos_data):
        form = PositionForm(pos_data)
        scroll = ScrollView()
        scroll.add_widget(form)
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        box.add_widget(scroll)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup = Popup(
            title="Edit Position" if pos_data else "Add Position",
            content=box, size_hint=(0.92, 0.85),
        )

        def do_save(*a):
            data = form.collect()
            if not data["floor"] or not data["department"] or not data["designation"]:
                info_popup("Missing Info", "Floor, Department and Designation are required.")
                return
            try:
                data["salary_package"] = float(data["salary_package"])
            except ValueError:
                info_popup("Invalid Salary", "Salary Package must be a number.")
                return
            if pos_data:
                ma.update_position(pos_data["pos_id"], data)
            else:
                ma.add_position(data)
            popup.dismiss()
            self.refresh_floors()
            App.get_running_app().root.get_screen("main").dashboard.refresh_floors()

        def do_delete(*a):
            def _confirmed():
                ma.delete_position(pos_data["pos_id"])
                popup.dismiss()
                self.refresh_floors()
                App.get_running_app().root.get_screen("main").dashboard.refresh_floors()
            confirm_popup("Delete Position",
                          f'Remove "{pos_data["designation"]}" in {pos_data["department"]}?',
                          _confirmed)

        btn_row.add_widget(AccentButton(text="Cancel", color=COLOR_MUTED,
                                         on_release=lambda *a: popup.dismiss()))
        if pos_data:
            btn_row.add_widget(AccentButton(text="Delete", color=COLOR_BAD, on_release=do_delete))
        btn_row.add_widget(AccentButton(text="Save", color=COLOR_ACCENT, on_release=do_save))
        box.add_widget(btn_row)
        popup.open()

    def export_csv(self):
        positions = ma.list_positions()
        app = App.get_running_app()
        out_dir = app.user_data_dir
        fname = f"manpower_roster_{datetime.date.today().isoformat()}.csv"
        out_path = os.path.join(out_dir, fname)
        fields = ["floor", "department", "category", "designation",
                  "staff_name", "grade", "salary_package", "gender"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for p in positions:
                writer.writerow({k: p.get(k, "") for k in fields})
        info_popup("Exported", f"Saved to app storage:\n{out_path}")


# ---------------------------------------------------------------
# Main screen (tabs + logout)
# ---------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")

        header = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(12), 0])
        with header.canvas.before:
            Color(*COLOR_ACCENT)
            self._hrect = RoundedRectangle(radius=[0])
        header.bind(pos=self._update_header, size=self._update_header)

        self.title_lbl = Label(text="Ranaya Silks - Manpower", bold=True,
                                color=(1, 1, 1, 1), font_size=sp(15), halign="left")
        self.title_lbl.bind(size=lambda s, v: setattr(s, "text_size", v))
        header.add_widget(self.title_lbl)
        header.add_widget(AccentButton(text="Logout", color=COLOR_ACCENT_DARK,
                                        size_hint_x=None, width=dp(90),
                                        on_release=self.logout))
        root.add_widget(header)

        tabs = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4), padding=dp(4))
        self.btn_dashboard = AccentButton(text="Dashboard", color=COLOR_GOLD,
                                           on_release=lambda *a: self.show_tab("dashboard"))
        self.btn_roster = AccentButton(text="Staff Roster", color=COLOR_MUTED,
                                        on_release=lambda *a: self.show_tab("roster"))
        tabs.add_widget(self.btn_dashboard)
        tabs.add_widget(self.btn_roster)
        root.add_widget(tabs)

        self.body = BoxLayout()
        root.add_widget(self.body)

        self.dashboard = DashboardView()
        self.roster = RosterView()
        self.add_widget(root)
        self._root_box = root
        self.body.add_widget(self.dashboard)
        self.current_tab = "dashboard"

    def _update_header(self, w, *a):
        self._hrect.pos = w.pos
        self._hrect.size = w.size

    def show_tab(self, name):
        self.body.clear_widgets()
        if name == "dashboard":
            self.body.add_widget(self.dashboard)
            self.btn_dashboard.background_color = COLOR_GOLD
            self.btn_roster.background_color = COLOR_MUTED
        else:
            self.body.add_widget(self.roster)
            self.btn_roster.background_color = COLOR_GOLD
            self.btn_dashboard.background_color = COLOR_MUTED
        self.current_tab = name

    def refresh_all(self):
        self.dashboard.refresh_floors()
        self.dashboard.refresh()
        self.roster.refresh_floors()

    def logout(self, *a):
        App.get_running_app().current_user = None
        self.show_tab("dashboard")
        App.get_running_app().root.current = "login"


# ---------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------
class ManpowerMobileApp(App):
    title = "Ranaya Silks - Manpower"

    def build(self):
        # Writable, per-app storage location on every platform (Android
        # included) - point the shared database.py at a DB file there
        # instead of next to the source, which may not be writable once
        # packaged into an .apk.
        os.makedirs(self.user_data_dir, exist_ok=True)
        db.DB_PATH = os.path.join(self.user_data_dir, "payroll.db")

        db.init_db()
        ma.init_manpower_db()

        self.current_user = None

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ChangePasswordScreen(name="change_password"))
        sm.add_widget(MainScreen(name="main"))
        sm.current = "login"
        return sm


if __name__ == "__main__":
    ManpowerMobileApp().run()
