# -*- coding: utf-8 -*-
"""
CAPIBARA POS - Version completa con tematica capibara
- Logo de capibara dibujado
- Modo dia / noche
- Vibracion y animacion al vender
- Sistema de logros
- Ventas, inventario (con EDITAR y nombre visible), clientes, reportes
- Historial de cliente con detalle completo y fecha visible
"""

import json
import os
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.animation import Animation

try:
    from jnius import autoclass
    from android import mActivity
    TIENE_ANDROID = True
except Exception:
    TIENE_ANDROID = False


# =====================================================================
#  TEMAS (DIA / NOCHE)
# =====================================================================
TEMA_DIA = {
    "fondo":     (0.96, 0.91, 0.82, 1),
    "tarjeta":   (0.90, 0.80, 0.65, 1),
    "texto":     (0.30, 0.18, 0.08, 1),
    "texto_2":   (0.50, 0.35, 0.20, 1),
    "dorado":    (0.85, 0.60, 0.20, 1),
    "verde":     (0.35, 0.70, 0.35, 1),
    "verde_o":   (0.20, 0.50, 0.20, 1),
    "rojo":      (0.85, 0.30, 0.25, 1),
    "naranja":   (0.95, 0.55, 0.20, 1),
    "blanco":    (1, 1, 1, 1),
    "marron":    (0.55, 0.35, 0.20, 1),
    "gris":      (0.60, 0.55, 0.45, 1),
}

TEMA_NOCHE = {
    "fondo":     (0.18, 0.12, 0.08, 1),
    "tarjeta":   (0.30, 0.20, 0.13, 1),
    "texto":     (0.96, 0.90, 0.76, 1),
    "texto_2":   (0.78, 0.72, 0.65, 1),
    "dorado":    (0.95, 0.72, 0.30, 1),
    "verde":     (0.55, 0.85, 0.45, 1),
    "verde_o":   (0.32, 0.65, 0.30, 1),
    "rojo":      (0.90, 0.35, 0.30, 1),
    "naranja":   (0.95, 0.60, 0.25, 1),
    "blanco":    (1, 1, 1, 1),
    "marron":    (0.45, 0.28, 0.15, 1),
    "gris":      (0.78, 0.72, 0.65, 1),
}

TEMA = dict(TEMA_NOCHE)


def L(monto):
    return f"L {monto:,.2f}"


def parse_float(texto):
    try:
        return float(texto.replace(",", "").replace(" ", ""))
    except Exception:
        return None


def parse_int(texto):
    try:
        return int(float(texto.replace(",", "").replace(" ", "")))
    except Exception:
        return None


def hoy():
    return datetime.now().strftime("%d/%m/%Y")


def ahora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def mes_actual():
    return datetime.now().strftime("%Y-%m")


def pintar_fondo(widget, color):
    widget.canvas.before.clear()
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(size=widget.size, pos=widget.pos)
    widget.bind(size=lambda i, v: setattr(rect, "size", i.size),
                pos=lambda i, v: setattr(rect, "pos", i.pos))


def tarjeta(parent, titulo, color_valor, font="13sp"):
    caja = BoxLayout(orientation="vertical", padding=6, spacing=2)
    pintar_fondo(caja, TEMA["tarjeta"])
    caja.add_widget(Label(text=titulo, color=TEMA["gris"],
                          font_size="11sp", size_hint_y=0.4))
    lbl = Label(text=L(0), color=color_valor, bold=True,
                font_size=font, size_hint_y=0.6)
    caja.add_widget(lbl)
    parent.add_widget(caja)
    return lbl


def boton(texto, color_fondo, color_texto=None, **kw):
    if color_texto is None:
        color_texto = TEMA["texto"]
    return Button(text=texto, background_normal="",
                  background_color=color_fondo, color=color_texto,
                  bold=True, **kw)


def vibrar(ms=100):
    if TIENE_ANDROID:
        try:
            Context = autoclass("android.content.Context")
            vibrator = mActivity.getSystemService(Context.VIBRATOR_SERVICE)
            vibrator.vibrate(ms)
        except Exception:
            pass


def popup_confirmar(mensaje, al_confirmar):
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    lbl = Label(text=mensaje, color=TEMA["texto"], size_hint_y=0.6)
    lbl.bind(size=lambda i, v: setattr(i, "text_size", i.size))
    box.add_widget(lbl)
    fila = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=0.4)
    b_si = boton("SI, ELIMINAR", TEMA["rojo"], TEMA["blanco"])
    b_no = boton("CANCELAR", TEMA["tarjeta"], TEMA["texto"])
    fila.add_widget(b_si)
    fila.add_widget(b_no)
    box.add_widget(fila)
    pop = Popup(title="Confirmar", content=box, size_hint=(0.85, 0.32),
                auto_dismiss=False)
    pop.background_color = TEMA["fondo"]
    pop.title_color = TEMA["dorado"]

    def confirmar(x):
        pop.dismiss()
        al_confirmar()

    b_si.bind(on_release=confirmar)
    b_no.bind(on_release=lambda x: pop.dismiss())
    pop.open()


# =====================================================================
#  WIDGET: LOGO CAPIBARA
# =====================================================================
class LogoCapibara(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.redibujar, size=self.redibujar)

    def redibujar(self, *args):
        self.canvas.clear()
        w = self.width
        h = self.height
        cx = self.center_x
        cy = self.center_y
        s = min(w, h) / 100.0

        with self.canvas:
            Color(0.45, 0.28, 0.15, 1)
            Ellipse(pos=(cx - 35 * s, cy + 15 * s),
                    size=(14 * s, 14 * s))
            Ellipse(pos=(cx + 21 * s, cy + 15 * s),
                    size=(14 * s, 14 * s))

            Color(0.75, 0.55, 0.35, 1)
            Ellipse(pos=(cx - 30 * s, cy - 20 * s),
                    size=(60 * s, 50 * s))

            Color(0.62, 0.42, 0.25, 1)
            Ellipse(pos=(cx - 14 * s, cy - 18 * s),
                    size=(28 * s, 18 * s))

            Color(0.10, 0.05, 0.02, 1)
            Ellipse(pos=(cx - 18 * s, cy + 2 * s),
                    size=(7 * s, 8 * s))
            Ellipse(pos=(cx + 11 * s, cy + 2 * s),
                    size=(7 * s, 8 * s))

            Color(1, 1, 1, 0.9)
            Ellipse(pos=(cx - 16 * s, cy + 6 * s),
                    size=(3 * s, 3 * s))
            Ellipse(pos=(cx + 13 * s, cy + 6 * s),
                    size=(3 * s, 3 * s))

            Color(0.20, 0.10, 0.05, 1)
            Ellipse(pos=(cx - 4 * s, cy - 12 * s),
                    size=(8 * s, 6 * s))

            Color(0.30, 0.15, 0.08, 1)
            Line(points=[cx - 6 * s, cy - 16 * s,
                         cx, cy - 18 * s,
                         cx + 6 * s, cy - 16 * s],
                 width=1.2)


# =====================================================================
#  PANTALLA PRINCIPAL
# =====================================================================
class PantallaInicio(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.root = BoxLayout(orientation="vertical", padding=10, spacing=8)
        pintar_fondo(self.root, TEMA["fondo"])
        self.add_widget(self.root)

        enc = BoxLayout(orientation="horizontal", spacing=6,
                        size_hint_y=0.13)
        self.logo = LogoCapibara(size_hint_x=0.30)
        enc.add_widget(self.logo)
        caja_txt = BoxLayout(orientation="vertical", size_hint_x=0.70)
        caja_txt.add_widget(Label(text="CAPIBARA POS", color=TEMA["dorado"],
                                  bold=True, font_size="20sp",
                                  halign="left", valign="middle"))
        caja_txt.add_widget(Label(text="Tu tienda amigable",
                                  color=TEMA["gris"], font_size="11sp",
                                  halign="left", valign="middle"))
        enc.add_widget(caja_txt)
        self.root.add_widget(enc)

        self.btn_tema = boton("", TEMA["tarjeta"], TEMA["texto"],
                              size_hint_y=0.06, font_size="12sp")
        self.btn_tema.bind(on_release=lambda x: self.cambiar_tema())
        self.root.add_widget(self.btn_tema)

        grid = GridLayout(cols=2, spacing=6, size_hint_y=0.24)
        self.card_hoy = tarjeta(grid, "VENTAS HOY", TEMA["verde"])
        self.card_mes = tarjeta(grid, "VENTAS DEL MES", TEMA["verde"])
        self.card_gan = tarjeta(grid, "GANANCIA MES", TEMA["dorado"])
        self.card_cred = tarjeta(grid, "FIADO PENDIENTE", TEMA["rojo"])
        self.root.add_widget(grid)

        caja_inv = BoxLayout(orientation="vertical", padding=8,
                             size_hint_y=0.13)
        pintar_fondo(caja_inv, TEMA["tarjeta"])
        self.lbl_inv = Label(text="", color=TEMA["texto"], font_size="11sp",
                             size_hint_y=0.65)
        self.lbl_inv.bind(size=lambda i, v: setattr(i, "text_size", i.size))
        caja_inv.add_widget(self.lbl_inv)
        self.lbl_alerta = Label(text="", color=TEMA["naranja"], bold=True,
                                font_size="11sp", size_hint_y=0.35)
        caja_inv.add_widget(self.lbl_alerta)
        self.root.add_widget(caja_inv)

        b_ven = boton("VENDER", TEMA["verde_o"], TEMA["blanco"],
                      size_hint_y=0.09, font_size="15sp")
        b_ven.bind(on_release=lambda x: self.ir_a("vender"))
        self.root.add_widget(b_ven)

        fila = BoxLayout(orientation="horizontal", spacing=6,
                         size_hint_y=0.09)
        b_inv = boton("INVENTARIO", TEMA["tarjeta"], TEMA["texto"],
                      font_size="13sp")
        b_cli = boton("CLIENTES", TEMA["tarjeta"], TEMA["texto"],
                      font_size="13sp")
        b_inv.bind(on_release=lambda x: self.ir_a("inventario"))
        b_cli.bind(on_release=lambda x: self.ir_a("clientes"))
        fila.add_widget(b_inv)
        fila.add_widget(b_cli)
        self.root.add_widget(fila)

        fila2 = BoxLayout(orientation="horizontal", spacing=6,
                          size_hint_y=0.09)
        b_rep = boton("REPORTES", TEMA["dorado"], TEMA["texto"],
                      font_size="13sp")
        b_log = boton("LOGROS", TEMA["marron"], TEMA["blanco"],
                      font_size="13sp")
        b_rep.bind(on_release=lambda x: self.ir_a("reportes"))
        b_log.bind(on_release=lambda x: self.popup_logros())
        fila2.add_widget(b_rep)
        fila2.add_widget(b_log)
        self.root.add_widget(fila2)

        self.actualizar_boton_tema()

    def actualizar_boton_tema(self):
        try:
            if TEMA["fondo"] == TEMA_DIA["fondo"]:
                self.btn_tema.text = "Cambiar a modo NOCHE"
            else:
                self.btn_tema.text = "Cambiar a modo DIA"
        except Exception:
            self.btn_tema.text = "Cambiar tema"

    def cambiar_tema(self):
        global TEMA
        if TEMA["fondo"] == TEMA_DIA["fondo"]:
            TEMA = dict(TEMA_NOCHE)
        else:
            TEMA = dict(TEMA_DIA)
        app = App.get_running_app()
        app.guardar_tema()
        app.sm.clear_widgets()
        app.construir_pantallas()
        app.sm.current = "inicio"

    def ir_a(self, nombre):
        app = App.get_running_app()
        if nombre == "vender":
            app.pantalla_vender.actualizar()
        elif nombre == "inventario":
            app.pantalla_inventario.actualizar()
        elif nombre == "clientes":
            app.pantalla_clientes.actualizar()
        elif nombre == "reportes":
            app.pantalla_reportes.actualizar()
        app.sm.current = nombre

    def actualizar(self):
        app = App.get_running_app()
        self.card_hoy.text = L(app.ventas_hoy())
        vm, gm = app.ventas_mes_ganancia()
        self.card_mes.text = L(vm)
        self.card_gan.text = L(gm)
        self.card_cred.text = L(app.credito_total())
        self.lbl_inv.text = (f"Invertido: {L(app.inversion_total())}   |   "
                             f"En estante: {L(app.valor_inventario())}")
        agotados = sum(1 for p in app.data["productos"] if p["stock"] <= 0)
        if agotados > 0:
            self.lbl_alerta.text = f"[!] {agotados} producto(s) AGOTADO(S)"
        else:
            self.lbl_alerta.text = "Todo en orden, capibara feliz"

    def popup_logros(self):
        app = App.get_running_app()
        logros = app.calcular_logros()
        box = BoxLayout(orientation="vertical", padding=10, spacing=6)
        box.add_widget(Label(text="TUS LOGROS DE CAPIBARA",
                             color=TEMA["dorado"], bold=True,
                             font_size="14sp", size_hint_y=0.1))
        scroll = ScrollView(size_hint_y=0.75)
        lista = BoxLayout(orientation="vertical", spacing=6,
                          size_hint_y=None, padding=(0, 4))
        lista.bind(minimum_height=lista.setter("height"))
        for logro in logros:
            color = TEMA["dorado"] if logro["logrado"] else TEMA["gris"]
            marca = "[X]" if logro["logrado"] else "[ ]"
            texto = f"{marca} {logro['nombre']}\n     {logro['desc']}"
            lbl = Label(text=texto, color=color, size_hint_y=None,
                        height=48, font_size="11sp", halign="left",
                        valign="middle")
            lbl.bind(size=lambda i, v: setattr(i, "text_size", i.size))
            lista.add_widget(lbl)
        scroll.add_widget(lista)
        box.add_widget(scroll)
        b_cerrar = boton("CERRAR", TEMA["tarjeta"], TEMA["texto"],
                         size_hint_y=0.15)
        box.add_widget(b_cerrar)
        pop = Popup(title="Logros", content=box,
                    size_hint=(0.92, 0.85), auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]
        b_cerrar.bind(on_release=lambda x: pop.dismiss())
        pop.open()

    def on_enter(self):
        self.actualizar()


# =====================================================================
#  PANTALLA VENDER
# =====================================================================
class PantallaVender(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.mapa = {}
        self.producto_sel = None
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        pintar_fondo(root, TEMA["fondo"])

        enc = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=0.07)
        b_vol = boton("<", TEMA["tarjeta"], TEMA["dorado"], size_hint_x=0.15)
        b_vol.bind(on_release=lambda x: self.volver())
        enc.add_widget(b_vol)
        enc.add_widget(Label(text="NUEVA VENTA", color=TEMA["dorado"],
                             bold=True, font_size="18sp"))
        root.add_widget(enc)

        root.add_widget(Label(text="Buscar producto:", color=TEMA["texto"],
                              size_hint_y=0.04, font_size="12sp"))
        self.inp_buscar = TextInput(text="", multiline=False,
                                    hint_text="Escribe para filtrar...",
                                    size_hint_y=0.07)
        self.inp_buscar.bind(text=lambda i, v: self.filtrar())
        root.add_widget(self.inp_buscar)

        self.scroll_res = ScrollView(size_hint_y=0.22, do_scroll_x=False)
        self.lista_res = BoxLayout(orientation="vertical", spacing=4,
                                   size_hint_y=None, padding=(0, 4))
        self.lista_res.bind(minimum_height=self.lista_res.setter("height"))
        self.scroll_res.add_widget(self.lista_res)
        root.add_widget(self.scroll_res)

        caja_sel = BoxLayout(orientation="vertical", padding=8, spacing=4,
                             size_hint_y=0.09)
        pintar_fondo(caja_sel, TEMA["tarjeta"])
        self.lbl_sel = Label(text="Ningun producto seleccionado",
                             color=TEMA["gris"], font_size="12sp",
                             size_hint_y=1)
        self.lbl_sel.bind(size=lambda i, v:
                          setattr(i, "text_size", i.size))
        caja_sel.add_widget(self.lbl_sel)
        root.add_widget(caja_sel)

        fila_cant = BoxLayout(orientation="horizontal", spacing=8,
                              size_hint_y=0.07)
        fila_cant.add_widget(Label(text="Cantidad:", color=TEMA["texto"],
                                   size_hint_x=0.3, font_size="12sp"))
        self.inp_cant = TextInput(text="1", multiline=False,
                                  input_filter="int", size_hint_x=0.7)
        self.inp_cant.bind(text=lambda i, v: self.calcular())
        fila_cant.add_widget(self.inp_cant)
        root.add_widget(fila_cant)

        self.lbl_total = Label(text="Total: L 0.00", color=TEMA["dorado"],
                               bold=True, font_size="15sp",
                               size_hint_y=0.06)
        root.add_widget(self.lbl_total)
        self.lbl_error = Label(text="", color=TEMA["rojo"], font_size="11sp",
                               size_hint_y=0.04)
        root.add_widget(self.lbl_error)

        b_ok = boton("CONFIRMAR VENTA", TEMA["verde_o"], TEMA["blanco"],
                     size_hint_y=0.08, font_size="14sp")
        b_ok.bind(on_release=lambda x: self.vender())
        root.add_widget(b_ok)

        root.add_widget(Label(text="VENTAS RECIENTES", color=TEMA["texto"],
                              bold=True, font_size="12sp",
                              size_hint_y=0.04))

        self.scroll = ScrollView(size_hint_y=0.20)
        self.lista = BoxLayout(orientation="vertical", spacing=5,
                               size_hint_y=None, padding=(0, 4))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        self.scroll.add_widget(self.lista)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def volver(self):
        app = App.get_running_app()
        app.pantalla_inicio.actualizar()
        app.sm.current = "inicio"

    def actualizar(self):
        app = App.get_running_app()
        self.mapa = {}
        for p in app.data["productos"]:
            self.mapa[p["id"]] = p
        self.producto_sel = None
        self.lbl_sel.text = "Ningun producto seleccionado"
        self.lbl_sel.color = TEMA["gris"]
        self.inp_buscar.text = ""
        self.filtrar()
        self.calcular()
        self.lbl_error.text = ""
        self.actualizar_ventas()

    def actualizar_ventas(self):
        app = App.get_running_app()
        self.lista.clear_widgets()
        ventas = app.data["ventas"][-30:]
        if not ventas:
            self.lista.add_widget(Label(text="Aun no hay ventas.",
                                        color=TEMA["gris"], size_hint_y=None,
                                        height=40))
        for v in reversed(ventas):
            fila = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=None, height=40, padding=(2, 2))
            lbl = Label(text=f"{v['fecha']}  {v['cantidad']} x "
                             f"{v['nombre']} = {L(v['total'])}",
                        color=TEMA["texto"], size_hint_x=0.82, font_size="11sp")
            lbl.bind(size=lambda i, v2: setattr(i, "text_size", i.size))
            b_del = boton("X", TEMA["rojo"], TEMA["blanco"], size_hint_x=0.18)
            b_del.bind(on_release=lambda x, vid=v["id"]:
                       popup_confirmar("Anular esta venta? (devuelve stock)",
                                       lambda: self.anular(vid)))
            fila.add_widget(lbl)
            fila.add_widget(b_del)
            self.lista.add_widget(fila)

    def filtrar(self):
        app = App.get_running_app()
        texto = self.inp_buscar.text.strip().lower()
        self.lista_res.clear_widgets()
        prods = app.data["productos"]
        if texto:
            prods = [p for p in prods if texto in p["nombre"].lower()
                     or texto in str(p["id"])]
        if not prods:
            self.lista_res.add_widget(Label(text="Sin resultados.",
                                            color=TEMA["gris"],
                                            size_hint_y=None, height=36))
            return
        for p in prods[:20]:
            color = TEMA["rojo"] if p["stock"] <= 0 else TEMA["texto"]
            b = boton(f"{p['nombre']}  |  {L(p['precio_venta'])}  "
                      f"| stock: {p['stock']}",
                      TEMA["tarjeta"], color, size_hint_y=None, height=38,
                      font_size="12sp")
            b.bind(on_release=lambda x, pid=p["id"]:
                   self.seleccionar(pid))
            self.lista_res.add_widget(b)

    def seleccionar(self, pid):
        app = App.get_running_app()
        p = app.buscar_producto(pid)
        if p is None:
            return
        self.producto_sel = p
        self.lbl_sel.text = (f"{p['nombre']}  |  "
                             f"Venta: {L(p['precio_venta'])}  |  "
                             f"Stock: {p['stock']}")
        self.lbl_sel.color = TEMA["dorado"]
        self.lbl_error.text = ""
        self.calcular()

    def calcular(self):
        p = self.producto_sel
        q = parse_int(self.inp_cant.text) or 0
        if p and q > 0:
            total = q * p["precio_venta"]
            gan = q * (p["precio_venta"] - p["precio_compra"])
            self.lbl_total.text = f"Total: {L(total)}  (ganancia {L(gan)})"
        else:
            self.lbl_total.text = "Total: L 0.00"

    def vender(self):
        app = App.get_running_app()
        p = self.producto_sel
        q = parse_int(self.inp_cant.text) or 0
        if p is None:
            self.lbl_error.text = "Selecciona un producto"
            return
        if q <= 0:
            self.lbl_error.text = "Cantidad invalida"
            return
        if q > p["stock"]:
            self.lbl_error.text = f"Stock insuficiente (hay {p['stock']})"
            return
        app.vender(p["id"], q)
        vibrar(80)
        self.animar_total()
        self.inp_cant.text = "1"
        self.producto_sel = None
        self.lbl_sel.text = "Ningun producto seleccionado"
        self.lbl_sel.color = TEMA["gris"]
        self.inp_buscar.text = ""
        self.filtrar()
        self.calcular()
        self.actualizar_ventas()

    def animar_total(self):
        anim = Animation(font_size=22, duration=0.15) + \
               Animation(font_size=15, duration=0.15)
        self.lbl_total.text = "VENTA HECHA"
        self.lbl_total.color = TEMA["verde"]
        anim.start(self.lbl_total)
        Clock.schedule_once(lambda dt: setattr(self.lbl_total, "color",
                                               TEMA["dorado"]), 0.6)
        Clock.schedule_once(lambda dt: self.calcular(), 0.8)

    def anular(self, vid):
        app = App.get_running_app()
        app.anular_venta(vid)
        self.actualizar_ventas()
        self.filtrar()

    def on_enter(self):
        self.actualizar()


# =====================================================================
#  PANTALLA INVENTARIO
# =====================================================================
class PantallaInventario(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        pintar_fondo(root, TEMA["fondo"])

        enc = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=0.08)
        b_vol = boton("<", TEMA["tarjeta"], TEMA["dorado"], size_hint_x=0.15)
        b_vol.bind(on_release=lambda x: self.volver())
        enc.add_widget(b_vol)
        enc.add_widget(Label(text="INVENTARIO", color=TEMA["dorado"],
                             bold=True, font_size="18sp"))
        root.add_widget(enc)

        b_add = boton("+  AGREGAR PRODUCTO", TEMA["dorado"], TEMA["texto"],
                      size_hint_y=0.08, font_size="13sp")
        b_add.bind(on_release=lambda x: self.popup_producto())
        root.add_widget(b_add)

        self.lbl_info = Label(text="", color=TEMA["gris"], font_size="11sp",
                              size_hint_y=0.05)
        root.add_widget(self.lbl_info)

        self.scroll = ScrollView(size_hint_y=0.74)
        self.lista = BoxLayout(orientation="vertical", spacing=6,
                               size_hint_y=None, padding=(0, 4))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        self.scroll.add_widget(self.lista)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def volver(self):
        App.get_running_app().sm.current = "inicio"

    def actualizar(self):
        app = App.get_running_app()
        prods = app.data["productos"]
        self.lbl_info.text = f"{len(prods)} producto(s) en la tienda"
        self.lista.clear_widgets()
        if not prods:
            self.lista.add_widget(Label(text="Sin productos. Agrega el primero.",
                                        color=TEMA["gris"],
                                        size_hint_y=None, height=40))
            return

        for p in prods:
            color_stock = TEMA["rojo"] if p["stock"] <= 0 else (
                TEMA["naranja"] if p["stock"] <= 3 else TEMA["texto"])

            tarjeta_prod = BoxLayout(orientation="vertical", spacing=2,
                                     size_hint_y=None, height=118,
                                     padding=(8, 6))
            pintar_fondo(tarjeta_prod, TEMA["tarjeta"])

            fila_nombre = BoxLayout(orientation="horizontal",
                                    size_hint_y=0.30)
            lbl_nombre = Label(text=p["nombre"], color=TEMA["dorado"],
                               bold=True, font_size="15sp",
                               halign="left", valign="middle")
            lbl_nombre.bind(size=lambda i, v:
                            setattr(i, "text_size", i.size))
            fila_nombre.add_widget(lbl_nombre)
            tarjeta_prod.add_widget(fila_nombre)

            fila_info = BoxLayout(orientation="horizontal", spacing=6,
                                  size_hint_y=0.32)
            info = (f"Compra: {L(p['precio_compra'])}   >   "
                    f"Venta: {L(p['precio_venta'])}")
            lbl_info = Label(text=info, color=TEMA["texto"],
                             size_hint_x=0.72, font_size="12sp",
                             halign="left", valign="middle")
            lbl_info.bind(size=lambda i, v:
                          setattr(i, "text_size", i.size))
            fila_info.add_widget(lbl_info)

            lbl_st = Label(text=f"Stock: {p['stock']}", color=color_stock,
                           bold=True, size_hint_x=0.28, font_size="12sp")
            fila_info.add_widget(lbl_st)
            tarjeta_prod.add_widget(fila_info)

            fila_btn = BoxLayout(orientation="horizontal", spacing=4,
                                 size_hint_y=0.38)
            b_edit = boton("EDITAR", TEMA["dorado"], TEMA["texto"],
                           size_hint_x=0.40, font_size="11sp")
            b_ent = boton("+ ENTRADA", TEMA["verde_o"], TEMA["blanco"],
                          size_hint_x=0.40, font_size="11sp")
            b_del = boton("X", TEMA["rojo"], TEMA["blanco"],
                          size_hint_x=0.20, font_size="12sp")

            b_edit.bind(on_release=lambda x, pid=p["id"]:
                        self.popup_editar(pid))
            b_ent.bind(on_release=lambda x, pid=p["id"]:
                       self.popup_entrada(pid))
            b_del.bind(on_release=lambda x, pid=p["id"]:
                       popup_confirmar("Eliminar este producto?",
                                       lambda: self.eliminar(pid)))

            fila_btn.add_widget(b_edit)
            fila_btn.add_widget(b_ent)
            fila_btn.add_widget(b_del)
            tarjeta_prod.add_widget(fila_btn)

            self.lista.add_widget(tarjeta_prod)

    def eliminar(self, pid):
        app = App.get_running_app()
        app.eliminar_producto(pid)
        self.actualizar()

    def popup_producto(self):
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", padding=10, spacing=6)
        campos = {}
        for clave, hint in [("nombre", "Nombre (Ej: Arroz 1kg)"),
                            ("pcompra", "Precio de compra (L)"),
                            ("pventa", "Precio de venta (L)"),
                            ("stock", "Cantidad inicial (stock)")]:
            box.add_widget(Label(text=hint + ":", color=TEMA["texto"],
                                 size_hint_y=0.13, font_size="11sp"))
            inp = TextInput(text="", multiline=False, size_hint_y=0.15,
                            input_filter=None if clave == "nombre" else "float")
            box.add_widget(inp)
            campos[clave] = inp
        lbl_error = Label(text="", color=TEMA["rojo"], size_hint_y=0.10,
                          font_size="11sp")
        box.add_widget(lbl_error)
        b_ok = boton("GUARDAR PRODUCTO", TEMA["verde_o"], TEMA["blanco"],
                     size_hint_y=0.14)
        box.add_widget(b_ok)

        pop = Popup(title="Nuevo producto", content=box, size_hint=(0.9, 0.9),
                    auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]

        def guardar(x):
            nombre = campos["nombre"].text.strip()
            pc = parse_float(campos["pcompra"].text)
            pv = parse_float(campos["pventa"].text)
            st = parse_int(campos["stock"].text)
            if not nombre:
                lbl_error.text = "El nombre es obligatorio"
                return
            if pc is None or pv is None or st is None:
                lbl_error.text = "Precios y cantidad deben ser numeros"
                return
            app.agregar_producto(nombre, pc, pv, st)
            pop.dismiss()
            self.actualizar()

        b_ok.bind(on_release=guardar)
        pop.open()

    def popup_editar(self, pid):
        app = App.get_running_app()
        p = app.buscar_producto(pid)
        if p is None:
            return

        box = BoxLayout(orientation="vertical", padding=10, spacing=5)

        box.add_widget(Label(text=f"Editando: {p['nombre']}",
                             color=TEMA["dorado"], size_hint_y=0.08,
                             bold=True, font_size="13sp"))

        box.add_widget(Label(text="Nombre:", color=TEMA["texto"],
                             size_hint_y=0.08, font_size="11sp"))
        inp_nombre = TextInput(text=p["nombre"], multiline=False,
                               size_hint_y=0.12)
        box.add_widget(inp_nombre)

        box.add_widget(Label(text="Precio de COMPRA (L):",
                             color=TEMA["texto"], size_hint_y=0.08,
                             font_size="11sp"))
        inp_compra = TextInput(text=str(p["precio_compra"]),
                               multiline=False, input_filter="float",
                               size_hint_y=0.12)
        box.add_widget(inp_compra)

        box.add_widget(Label(text="Precio de VENTA (L):",
                             color=TEMA["texto"], size_hint_y=0.08,
                             font_size="11sp"))
        inp_venta = TextInput(text=str(p["precio_venta"]),
                              multiline=False, input_filter="float",
                              size_hint_y=0.12)
        box.add_widget(inp_venta)

        box.add_widget(Label(text="Stock actual:",
                             color=TEMA["texto"], size_hint_y=0.08,
                             font_size="11sp"))
        inp_stock = TextInput(text=str(p["stock"]),
                              multiline=False, input_filter="int",
                              size_hint_y=0.12)
        box.add_widget(inp_stock)

        lbl_error = Label(text="", color=TEMA["rojo"], size_hint_y=0.08,
                          font_size="11sp")
        box.add_widget(lbl_error)

        b_ok = boton("GUARDAR CAMBIOS", TEMA["verde_o"], TEMA["blanco"],
                     size_hint_y=0.14)
        box.add_widget(b_ok)

        pop = Popup(title="Editar producto", content=box,
                    size_hint=(0.92, 0.90), auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]

        def guardar(x):
            nombre = inp_nombre.text.strip()
            pc = parse_float(inp_compra.text)
            pv = parse_float(inp_venta.text)
            st = parse_int(inp_stock.text)
            if not nombre:
                lbl_error.text = "El nombre es obligatorio"
                return
            if pc is None or pv is None or st is None:
                lbl_error.text = "Precios y stock deben ser numeros"
                return
            if pc <= 0 or pv <= 0:
                lbl_error.text = "Los precios deben ser mayores a 0"
                return
            if st < 0:
                lbl_error.text = "El stock no puede ser negativo"
                return
            app.editar_producto(pid, nombre, pc, pv, st)
            pop.dismiss()
            self.actualizar()

        b_ok.bind(on_release=guardar)
        pop.open()

    def popup_entrada(self, pid):
        app = App.get_running_app()
        p = app.buscar_producto(pid)
        box = BoxLayout(orientation="vertical", padding=10, spacing=6)
        box.add_widget(Label(text=f"Entrada para: {p['nombre']}",
                             color=TEMA["dorado"], size_hint_y=0.12,
                             bold=True))
        box.add_widget(Label(text="Cantidad que entra:", color=TEMA["texto"],
                             size_hint_y=0.12))
        inp_cant = TextInput(text="", multiline=False, input_filter="int",
                             size_hint_y=0.16)
        box.add_widget(inp_cant)
        box.add_widget(Label(text="Costo unitario (L):", color=TEMA["texto"],
                             size_hint_y=0.12))
        inp_costo = TextInput(text=str(p["precio_compra"]), multiline=False,
                              input_filter="float", size_hint_y=0.16)
        box.add_widget(inp_costo)
        box.add_widget(Label(text="(Opcional) Actualizar precio de venta:",
                             color=TEMA["gris"], size_hint_y=0.10,
                             font_size="10sp"))
        inp_venta = TextInput(text="", multiline=False, input_filter="float",
                              hint_text=f"Actual: {p['precio_venta']}",
                              size_hint_y=0.14)
        box.add_widget(inp_venta)
        lbl_error = Label(text="", color=TEMA["rojo"], size_hint_y=0.10,
                          font_size="11sp")
        box.add_widget(lbl_error)
        b_ok = boton("REGISTRAR ENTRADA", TEMA["verde_o"], TEMA["blanco"],
                     size_hint_y=0.14)
        box.add_widget(b_ok)

        pop = Popup(title="Entrada de mercaderia", content=box,
                    size_hint=(0.9, 0.75), auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]

        def guardar(x):
            cant = parse_int(inp_cant.text)
            costo = parse_float(inp_costo.text)
            if cant is None or cant <= 0 or costo is None:
                lbl_error.text = "Cantidad y costo invalidos"
                return
            venta_nueva = parse_float(inp_venta.text)
            app.agregar_entrada(pid, cant, costo, venta_nueva)
            pop.dismiss()
            self.actualizar()

        b_ok.bind(on_release=guardar)
        pop.open()

    def on_enter(self):
        self.actualizar()


# =====================================================================
#  PANTALLA CLIENTES
# =====================================================================
class PantallaClientes(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        pintar_fondo(root, TEMA["fondo"])

        enc = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=0.08)
        b_vol = boton("<", TEMA["tarjeta"], TEMA["dorado"], size_hint_x=0.15)
        b_vol.bind(on_release=lambda x: self.volver())
        enc.add_widget(b_vol)
        enc.add_widget(Label(text="CLIENTES", color=TEMA["dorado"],
                             bold=True, font_size="18sp"))
        root.add_widget(enc)

        b_add = boton("+  AGREGAR CLIENTE", TEMA["dorado"], TEMA["texto"],
                      size_hint_y=0.08, font_size="13sp")
        b_add.bind(on_release=lambda x: self.popup_cliente())
        root.add_widget(b_add)

        self.scroll = ScrollView(size_hint_y=0.77)
        self.lista = BoxLayout(orientation="vertical", spacing=6,
                               size_hint_y=None, padding=(0, 4))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        self.scroll.add_widget(self.lista)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def volver(self):
        App.get_running_app().sm.current = "inicio"

    def actualizar(self):
        app = App.get_running_app()
        self.lista.clear_widgets()
        if not app.data["clientes"]:
            self.lista.add_widget(Label(text="Sin clientes registrados.",
                                        color=TEMA["gris"],
                                        size_hint_y=None, height=40))
        for c in app.data["clientes"]:
            color = TEMA["rojo"] if c["deuda"] > 0 else TEMA["verde"]
            estado = f"Debe {L(c['deuda'])}" if c["deuda"] > 0 else "Al dia"
            fila = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=None, height=52, padding=(2, 2))
            pintar_fondo(fila, TEMA["tarjeta"])
            lbl = Label(text=f"{c['nombre']}", color=TEMA["texto"],
                        size_hint_x=0.55, font_size="13sp")
            lbl.bind(size=lambda i, v: setattr(i, "text_size", i.size))
            lbl_d = Label(text=estado, color=color, bold=True,
                          size_hint_x=0.30, font_size="12sp")
            b_ver = boton("VER", TEMA["verde_o"], TEMA["blanco"],
                          size_hint_x=0.15, font_size="11sp")
            b_ver.bind(on_release=lambda x, cid=c["id"]:
                       app.abrir_cliente(cid))
            fila.add_widget(lbl)
            fila.add_widget(lbl_d)
            fila.add_widget(b_ver)
            self.lista.add_widget(fila)

    def popup_cliente(self):
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", padding=10, spacing=6)
        box.add_widget(Label(text="Nombre del cliente:", color=TEMA["texto"],
                             size_hint_y=0.15))
        inp_nom = TextInput(text="", multiline=False, size_hint_y=0.20)
        box.add_widget(inp_nom)
        box.add_widget(Label(text="Telefono (opcional):", color=TEMA["texto"],
                             size_hint_y=0.15))
        inp_tel = TextInput(text="", multiline=False, size_hint_y=0.20)
        box.add_widget(inp_tel)
        lbl_error = Label(text="", color=TEMA["rojo"], size_hint_y=0.12,
                          font_size="11sp")
        box.add_widget(lbl_error)
        b_ok = boton("GUARDAR CLIENTE", TEMA["verde_o"], TEMA["blanco"],
                     size_hint_y=0.18)
        box.add_widget(b_ok)

        pop = Popup(title="Nuevo cliente", content=box, size_hint=(0.9, 0.55),
                    auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]

        def guardar(x):
            nombre = inp_nom.text.strip()
            if not nombre:
                lbl_error.text = "El nombre es obligatorio"
                return
            app.agregar_cliente(nombre, inp_tel.text.strip())
            pop.dismiss()
            self.actualizar()

        b_ok.bind(on_release=guardar)
        pop.open()

    def on_enter(self):
        self.actualizar()


# =====================================================================
#  PANTALLA DETALLE DE CLIENTE
# =====================================================================
class PantallaClienteDetalle(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.cliente_id = None
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        pintar_fondo(root, TEMA["fondo"])

        enc = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=0.07)
        b_vol = boton("<", TEMA["tarjeta"], TEMA["dorado"], size_hint_x=0.15)
        b_vol.bind(on_release=lambda x: self.volver())
        enc.add_widget(b_vol)
        self.lbl_titulo = Label(text="", color=TEMA["dorado"], bold=True,
                                font_size="15sp")
        self.lbl_titulo.bind(size=lambda i, v: setattr(i, "text_size", i.size))
        enc.add_widget(self.lbl_titulo)
        root.add_widget(enc)

        caja = BoxLayout(orientation="vertical", padding=8,
                         size_hint_y=0.12)
        pintar_fondo(caja, TEMA["tarjeta"])
        caja.add_widget(Label(text="DEUDA ACTUAL", color=TEMA["gris"],
                              font_size="11sp", size_hint_y=0.3))
        self.lbl_deuda = Label(text=L(0), color=TEMA["rojo"], bold=True,
                               font_size="22sp", size_hint_y=0.7)
        caja.add_widget(self.lbl_deuda)
        root.add_widget(caja)

        fila = BoxLayout(orientation="horizontal", spacing=8,
                         size_hint_y=0.08)
        b_cargo = boton("+ CARGO (FIADO)", TEMA["rojo"], TEMA["blanco"],
                        font_size="13sp")
        b_pago = boton("REGISTRAR PAGO", TEMA["verde_o"], TEMA["blanco"],
                       font_size="13sp")
        b_cargo.bind(on_release=lambda x: self.popup_movimiento("cargo"))
        b_pago.bind(on_release=lambda x: self.popup_movimiento("pago"))
        fila.add_widget(b_cargo)
        fila.add_widget(b_pago)
        root.add_widget(fila)

        root.add_widget(Label(text="HISTORIAL DE MOVIMIENTOS",
                              color=TEMA["texto"], bold=True,
                              font_size="12sp", size_hint_y=0.04))

        self.scroll = ScrollView(size_hint_y=0.61, do_scroll_x=False)
        self.lista = BoxLayout(orientation="vertical", spacing=6,
                               size_hint_y=None, padding=(0, 4))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        self.scroll.add_widget(self.lista)
        root.add_widget(self.scroll)

        b_del = boton("ELIMINAR CLIENTE", TEMA["rojo"], TEMA["blanco"],
                      size_hint_y=0.06, font_size="11sp")
        b_del.bind(on_release=lambda x: self.popup_eliminar())
        root.add_widget(b_del)

        self.add_widget(root)

    def volver(self):
        app = App.get_running_app()
        app.pantalla_clientes.actualizar()
        app.sm.current = "clientes"

    def actualizar(self):
        app = App.get_running_app()
        c = app.buscar_cliente(self.cliente_id)
        if c is None:
            self.volver()
            return
        tel = f" ({c['telefono']})" if c.get("telefono") else ""
        self.lbl_titulo.text = f"{c['nombre']}{tel}"
        self.lbl_deuda.text = L(c["deuda"])
        self.lbl_deuda.color = TEMA["rojo"] if c["deuda"] > 0 else TEMA["verde"]

        self.lista.clear_widgets()
        if not c["historial"]:
            self.lista.add_widget(Label(text="Sin movimientos.",
                                        color=TEMA["gris"],
                                        size_hint_y=None, height=40))
            return

        for m in reversed(c["historial"]):
            if m["tipo"] == "cargo":
                signo, color, titulo = "+", TEMA["rojo"], "CARGO (FIADO)"
            else:
                signo, color, titulo = "-", TEMA["verde"], "PAGO"

            tarjeta_mov = BoxLayout(orientation="vertical", spacing=2,
                                    size_hint_y=None, height=100,
                                    padding=(8, 6))
            pintar_fondo(tarjeta_mov, TEMA["tarjeta"])

            fila1 = BoxLayout(orientation="horizontal",
                              size_hint_y=0.30)
            fecha_str = m.get("fecha_hora", m.get("fecha", ""))
            lbl_fecha = Label(text=fecha_str, color=TEMA["gris"],
                              size_hint_x=0.70, font_size="11sp",
                              halign="left", valign="middle")
            lbl_fecha.bind(size=lambda i, v:
                           setattr(i, "text_size", i.size))
            fila1.add_widget(lbl_fecha)
            lbl_tipo = Label(text=titulo, color=color, bold=True,
                             size_hint_x=0.30, font_size="11sp",
                             halign="right", valign="middle")
            fila1.add_widget(lbl_tipo)
            tarjeta_mov.add_widget(fila1)

            fila2 = BoxLayout(orientation="horizontal",
                              size_hint_y=0.42)
            detalle = m.get("detalle", "") or "(sin detalle)"
            lbl_det = Label(text=detalle, color=TEMA["texto"],
                            font_size="12sp", halign="left",
                            valign="middle")
            lbl_det.bind(size=lambda i, v:
                         setattr(i, "text_size", i.size))
            fila2.add_widget(lbl_det)
            tarjeta_mov.add_widget(fila2)

            fila3 = BoxLayout(orientation="horizontal",
                              size_hint_y=0.28)
            lbl_monto = Label(text=f"{signo} {L(m['monto'])}",
                              color=color, bold=True, font_size="14sp",
                              halign="right", valign="middle")
            lbl_monto.bind(size=lambda i, v:
                           setattr(i, "text_size", i.size))
            fila3.add_widget(lbl_monto)
            tarjeta_mov.add_widget(fila3)

            self.lista.add_widget(tarjeta_mov)

    def popup_movimiento(self, tipo):
        app = App.get_running_app()
        c = app.buscar_cliente(self.cliente_id)
        es_cargo = tipo == "cargo"
        box = BoxLayout(orientation="vertical", padding=10, spacing=6)

        box.add_widget(Label(text="Monto (L):", color=TEMA["texto"],
                             size_hint_y=0.10))
        inp_monto = TextInput(text="", multiline=False, input_filter="float",
                              size_hint_y=0.13)
        box.add_widget(inp_monto)

        box.add_widget(Label(
            text="Detalle (escribe todos los productos):",
            color=TEMA["texto"], size_hint_y=0.10, font_size="11sp"))
        hint = ("Ej: 2 arroz, 1 aceite, 3 latas de atun, "
                "1 bolsa de azucar")
        if not es_cargo:
            hint = "Ej: Abono semana 1"
        inp_det = TextInput(text="", multiline=True, hint_text=hint,
                            size_hint_y=0.42)
        box.add_widget(inp_det)

        lbl_error = Label(text="", color=TEMA["rojo"], size_hint_y=0.08,
                          font_size="11sp")
        box.add_widget(lbl_error)

        b_ok = boton("GUARDAR", TEMA["rojo"] if es_cargo else TEMA["verde_o"],
                     TEMA["blanco"], size_hint_y=0.12)
        box.add_widget(b_ok)

        titulo = f"Cargo - {c['nombre']}" if es_cargo else f"Pago - {c['nombre']}"
        pop = Popup(title=titulo, content=box,
                    size_hint=(0.92, 0.80), auto_dismiss=True)
        pop.background_color = TEMA["fondo"]
        pop.title_color = TEMA["dorado"]

        def guardar(x):
            monto = parse_float(inp_monto.text)
            if monto is None:
                lbl_error.text = "Ingresa un monto valido"
                return
            detalle = inp_det.text.strip()
            if es_cargo:
                app.cargo_cliente(c["id"], monto,
                                  detalle or "Compra a credito")
            else:
                app.pago_cliente(c["id"], monto, detalle or "Pago")
            pop.dismiss()
            self.actualizar()

        b_ok.bind(on_release=guardar)
        pop.open()

    def popup_eliminar(self):
        app = App.get_running_app()
        c = app.buscar_cliente(self.cliente_id)
        if c is None:
            return
        popup_confirmar(f"Eliminar a {c['nombre']}?",
                        self.confirmar_eliminar)

    def confirmar_eliminar(self):
        app = App.get_running_app()
        app.eliminar_cliente(self.cliente_id)
        self.volver()

    def on_enter(self):
        self.actualizar()


# =====================================================================
#  PANTALLA REPORTES
# =====================================================================
class PantallaReportes(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        pintar_fondo(root, TEMA["fondo"])

        enc = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=0.07)
        b_vol = boton("<", TEMA["tarjeta"], TEMA["dorado"], size_hint_x=0.15)
        b_vol.bind(on_release=lambda x: self.volver())
        enc.add_widget(b_vol)
        enc.add_widget(Label(text="REPORTES", color=TEMA["dorado"], bold=True,
                             font_size="18sp"))
        root.add_widget(enc)

        fila_sel = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=0.08)
        fila_sel.add_widget(Label(text="Periodo:", color=TEMA["texto"],
                                  size_hint_x=0.3, font_size="12sp"))
        self.spin_periodo = Spinner(
            text="Este mes",
            values=("Hoy", "Este mes", "Este anio", "Todo"),
            size_hint_x=0.7)
        self.spin_periodo.bind(text=lambda *a: self.actualizar())
        fila_sel.add_widget(self.spin_periodo)
        root.add_widget(fila_sel)

        caja = BoxLayout(orientation="vertical", padding=8, spacing=4,
                         size_hint_y=0.16)
        pintar_fondo(caja, TEMA["tarjeta"])
        self.lbl_titulo = Label(text="", color=TEMA["dorado"], bold=True,
                                font_size="12sp", size_hint_y=0.3)
        caja.add_widget(self.lbl_titulo)
        rf = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=0.7)
        self.card_total = tarjeta(rf, "VENTAS", TEMA["verde"], "12sp")
        self.card_gan = tarjeta(rf, "GANANCIA", TEMA["dorado"], "12sp")
        self.card_cant = tarjeta(rf, "UNIDADES", TEMA["texto"], "12sp")
        caja.add_widget(rf)
        root.add_widget(caja)

        root.add_widget(Label(text="PRODUCTOS MAS VENDIDOS",
                              color=TEMA["texto"], bold=True, font_size="12sp",
                              size_hint_y=0.04))

        self.scroll = ScrollView(size_hint_y=0.57, do_scroll_x=False)
        self.lista = BoxLayout(orientation="vertical", spacing=6,
                               size_hint_y=None, padding=(0, 4))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        self.scroll.add_widget(self.lista)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def volver(self):
        App.get_running_app().sm.current = "inicio"

    def on_enter(self):
        self.actualizar()

    def _filtrar_ventas(self):
        app = App.get_running_app()
        periodo = self.spin_periodo.text
        hoy_str = datetime.now().strftime("%d/%m/%Y")
        mes_str = datetime.now().strftime("%Y-%m")
        anio_str = datetime.now().strftime("%Y")
        ventas = app.data["ventas"]
        if periodo == "Hoy":
            return [v for v in ventas if v["fecha"] == hoy_str]
        if periodo == "Este mes":
            return [v for v in ventas if v.get("mes") == mes_str]
        if periodo == "Este anio":
            return [v for v in ventas
                    if v["fecha"].split("/")[-1] == anio_str]
        return ventas

    def actualizar(self):
        self.lista.clear_widgets()
        ventas = self._filtrar_ventas()

        total = sum(v["total"] for v in ventas)
        ganancia = sum(v["ganancia"] for v in ventas)
        unidades = sum(v["cantidad"] for v in ventas)

        self.lbl_titulo.text = f"Periodo: {self.spin_periodo.text}"
        self.card_total.text = L(total)
        self.card_gan.text = L(ganancia)
        self.card_cant.text = str(unidades)

        mapa = {}
        for v in ventas:
            nombre = v["nombre"]
            if nombre not in mapa:
                mapa[nombre] = {"unidades": 0, "total": 0.0,
                                "ganancia": 0.0}
            mapa[nombre]["unidades"] += v["cantidad"]
            mapa[nombre]["total"] += v["total"]
            mapa[nombre]["ganancia"] += v["ganancia"]

        if not mapa:
            self.lista.add_widget(Label(
                text="Sin ventas en este periodo.",
                color=TEMA["gris"], size_hint_y=None, height=40))
            return

        ordenado = sorted(mapa.items(),
                          key=lambda x: -x[1]["unidades"])

        for i, (nombre, d) in enumerate(ordenado):
            if i == 0:
                medalla, color = "1er", TEMA["dorado"]
            elif i == 1:
                medalla, color = "2do", TEMA["texto"]
            elif i == 2:
                medalla, color = "3er", TEMA["naranja"]
            else:
                medalla, color = f"#{i+1}", TEMA["gris"]

            texto = (f"{medalla}  {nombre}\n"
                     f"Vendidos: {d['unidades']}  |  "
                     f"Total: {L(d['total'])}  |  "
                     f"Gan: {L(d['ganancia'])}")
            lbl = Label(text=texto, color=color, size_hint_y=None,
                        height=54, font_size="11sp")
            lbl.bind(size=lambda i, x: setattr(i, "text_size", i.size))
            self.lista.add_widget(lbl)


# =====================================================================
#  APLICACION
# =====================================================================
class CapibaraApp(App):

    def build(self):
        global TEMA
        self.title = "Capibara POS"
        self.data = self.cargar_datos()
        if self.data.get("tema") == "dia":
            TEMA = dict(TEMA_DIA)
        else:
            TEMA = dict(TEMA_NOCHE)
        self.sm = ScreenManager()
        self.construir_pantallas()
        return self.sm

    def construir_pantallas(self):
        self.pantalla_inicio = PantallaInicio(name="inicio")
        self.pantalla_vender = PantallaVender(name="vender")
        self.pantalla_inventario = PantallaInventario(name="inventario")
        self.pantalla_clientes = PantallaClientes(name="clientes")
        self.pantalla_detalle = PantallaClienteDetalle(name="detalle")
        self.pantalla_reportes = PantallaReportes(name="reportes")
        self.sm.add_widget(self.pantalla_inicio)
        self.sm.add_widget(self.pantalla_vender)
        self.sm.add_widget(self.pantalla_inventario)
        self.sm.add_widget(self.pantalla_clientes)
        self.sm.add_widget(self.pantalla_detalle)
        self.sm.add_widget(self.pantalla_reportes)

    def guardar_tema(self):
        self.data["tema"] = "dia" if TEMA["fondo"] == TEMA_DIA["fondo"] else "noche"
        self.guardar()

    def ruta_datos(self):
        return os.path.join(self.user_data_dir, "capibara_pos.json")

    def cargar_datos(self):
        try:
            with open(self.ruta_datos(), "r") as f:
                return json.load(f)
        except Exception:
            return {"ids": {"producto": 1, "venta": 1, "cliente": 1},
                    "productos": [], "entradas": [],
                    "ventas": [], "clientes": [],
                    "tema": "noche"}

    def guardar(self):
        try:
            with open(self.ruta_datos(), "w") as f:
                json.dump(self.data, f)
        except Exception:
            pass

    def nuevo_id(self, clave):
        nid = self.data["ids"].get(clave, 1)
        self.data["ids"][clave] = nid + 1
        return nid

    def buscar_producto(self, pid):
        for p in self.data["productos"]:
            if p["id"] == pid:
                return p
        return None

    def agregar_producto(self, nombre, pc, pv, stock):
        pid = self.nuevo_id("producto")
        self.data["productos"].append(
            {"id": pid, "nombre": nombre, "precio_compra": pc,
             "precio_venta": pv, "stock": stock})
        if stock > 0:
            self.data["entradas"].append(
                {"pid": pid, "cantidad": stock, "costo": pc,
                 "total": stock * pc, "fecha": hoy()})
        self.guardar()

    def editar_producto(self, pid, nombre, pc, pv, stock):
        p = self.buscar_producto(pid)
        if p is None:
            return
        p["nombre"] = nombre
        p["precio_compra"] = pc
        p["precio_venta"] = pv
        p["stock"] = stock
        self.guardar()

    def agregar_entrada(self, pid, cantidad, costo, venta_nueva=None):
        p = self.buscar_producto(pid)
        if p is None:
            return
        p["stock"] += cantidad
        p["precio_compra"] = costo
        if venta_nueva is not None and venta_nueva > 0:
            p["precio_venta"] = venta_nueva
        self.data["entradas"].append(
            {"pid": pid, "cantidad": cantidad, "costo": costo,
             "total": cantidad * costo, "fecha": hoy()})
        self.guardar()

    def eliminar_producto(self, pid):
        self.data["productos"] = [p for p in self.data["productos"]
                                  if p["id"] != pid]
        self.guardar()

    def vender(self, pid, cantidad):
        p = self.buscar_producto(pid)
        if p is None or cantidad > p["stock"]:
            return False
        p["stock"] -= cantidad
        vid = self.nuevo_id("venta")
        self.data["ventas"].append(
            {"id": vid, "pid": pid, "nombre": p["nombre"],
             "cantidad": cantidad,
             "total": cantidad * p["precio_venta"],
             "ganancia": cantidad * (p["precio_venta"] - p["precio_compra"]),
             "fecha": hoy(), "mes": mes_actual()})
        self.guardar()
        return True

    def anular_venta(self, vid):
        for v in self.data["ventas"]:
            if v["id"] == vid:
                p = self.buscar_producto(v["pid"])
                if p is not None:
                    p["stock"] += v["cantidad"]
                break
        self.data["ventas"] = [v for v in self.data["ventas"]
                               if v["id"] != vid]
        self.guardar()

    def buscar_cliente(self, cid):
        for c in self.data["clientes"]:
            if c["id"] == cid:
                return c
        return None

    def abrir_cliente(self, cid):
        self.pantalla_detalle.cliente_id = cid
        self.pantalla_detalle.actualizar()
        self.sm.current = "detalle"

    def agregar_cliente(self, nombre, telefono):
        cid = self.nuevo_id("cliente")
        self.data["clientes"].append(
            {"id": cid, "nombre": nombre, "telefono": telefono,
             "deuda": 0, "historial": []})
        self.guardar()
        self.pantalla_clientes.actualizar()

    def eliminar_cliente(self, cid):
        self.data["clientes"] = [c for c in self.data["clientes"]
                                 if c["id"] != cid]
        self.guardar()

    def cargo_cliente(self, cid, monto, detalle):
        c = self.buscar_cliente(cid)
        if c is None:
            return
        c["deuda"] += monto
        c["historial"].append({
            "tipo": "cargo",
            "monto": monto,
            "detalle": detalle,
            "fecha": hoy(),
            "fecha_hora": ahora(),
        })
        self.guardar()

    def pago_cliente(self, cid, monto, detalle):
        c = self.buscar_cliente(cid)
        if c is None:
            return
        c["deuda"] -= monto
        c["historial"].append({
            "tipo": "pago",
            "monto": monto,
            "detalle": detalle,
            "fecha": hoy(),
            "fecha_hora": ahora(),
        })
        self.guardar()

    def ventas_hoy(self):
        return sum(v["total"] for v in self.data["ventas"]
                   if v["fecha"] == hoy())

    def ventas_mes_ganancia(self):
        mes = mes_actual()
        ventas = sum(v["total"] for v in self.data["ventas"]
                     if v.get("mes") == mes)
        gan = sum(v["ganancia"] for v in self.data["ventas"]
                  if v.get("mes") == mes)
        return ventas, gan

    def credito_total(self):
        return sum(c["deuda"] for c in self.data["clientes"])

    def inversion_total(self):
        return sum(e["total"] for e in self.data["entradas"])

    def valor_inventario(self):
        return sum(p["stock"] * p["precio_compra"]
                   for p in self.data["productos"])

    def calcular_logros(self):
        ventas = self.data["ventas"]
        total_ventas = len(ventas)
        total_ingresos = sum(v["total"] for v in ventas)
        total_ganancia = sum(v["ganancia"] for v in ventas)
        total_unidades = sum(v["cantidad"] for v in ventas)
        productos = len(self.data["productos"])
        clientes = len(self.data["clientes"])
        ventas_hoy_c = sum(1 for v in ventas if v["fecha"] == hoy())

        return [
            {"nombre": "Primer paso de capibara",
             "desc": "Registra tu primera venta",
             "logrado": total_ventas >= 1},
            {"nombre": "Capibara trabajador",
             "desc": "Registra 10 ventas",
             "logrado": total_ventas >= 10},
            {"nombre": "Capibara vendedor",
             "desc": "Registra 100 ventas",
             "logrado": total_ventas >= 100},
            {"nombre": "Capibara experto",
             "desc": "Registra 500 ventas",
             "logrado": total_ventas >= 500},
            {"nombre": "Bien surtido",
             "desc": "Ten 10 productos en inventario",
             "logrado": productos >= 10},
            {"nombre": "Tienda grande",
             "desc": "Ten 50 productos en inventario",
             "logrado": productos >= 50},
            {"nombre": "Comunidad capibara",
             "desc": "Registra 5 clientes",
             "logrado": clientes >= 5},
            {"nombre": "Amigo de todos",
             "desc": "Registra 20 clientes",
             "logrado": clientes >= 20},
            {"nombre": "Ventas de mil",
             "desc": "L 1,000 en ventas totales",
             "logrado": total_ingresos >= 1000},
            {"nombre": "Ventas de diez mil",
             "desc": "L 10,000 en ventas totales",
             "logrado": total_ingresos >= 10000},
            {"nombre": "Ventas de cien mil",
             "desc": "L 100,000 en ventas totales",
             "logrado": total_ingresos >= 100000},
            {"nombre": "Ganancia capibara",
             "desc": "L 5,000 en ganancias",
             "logrado": total_ganancia >= 5000},
            {"nombre": "Vendedor del dia",
             "desc": "10 ventas en un solo dia",
             "logrado": ventas_hoy_c >= 10},
            {"nombre": "Movimiento de mercancia",
             "desc": "1000 unidades vendidas",
             "logrado": total_unidades >= 1000},
        ]


if __name__ == "__main__":
    CapibaraApp().run()
