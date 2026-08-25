from flask import Flask, render_template, request, redirect
import sqlite3
import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


app = Flask(__name__)


# =====================================================
# CONFIGURACIÓN DEL CORREO
# =====================================================

def enviar_notificacion(correo, nombre, fecha, hora, personas, estado):

    # Estas son las variables que debes tener configuradas
    # en Render → Environment Variables
    remitente = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")

    # Verificar que las variables existan
    if not remitente or not password:
        print("ERROR: No están configuradas EMAIL_USER o EMAIL_PASSWORD en Render.")
        return False

    mensaje = MIMEMultipart()

    mensaje["From"] = remitente
    mensaje["To"] = correo

    # =================================================
    # RESERVA ACEPTADA
    # =================================================

    if estado == "Aceptada":

        mensaje["Subject"] = "Reserva aceptada - La Mesa Dorada"

        cuerpo = f"""
Hola {nombre}:

Nos complace informarte que tu reserva en La Mesa Dorada
ha sido ACEPTADA.

Detalles de tu reserva:

Fecha: {fecha}
Hora: {hora}
Personas: {personas}

Te esperamos en nuestro restaurante.

¡Gracias por elegir La Mesa Dorada!

Saludos,

La Mesa Dorada
"""

    # =================================================
    # RESERVA RECHAZADA
    # =================================================

    else:

        mensaje["Subject"] = "Reserva rechazada - La Mesa Dorada"

        cuerpo = f"""
Hola {nombre}:

Lamentamos informarte que tu reserva en La Mesa Dorada
ha sido RECHAZADA.

Detalles de la reserva:

Fecha: {fecha}
Hora: {hora}
Personas: {personas}

Si lo deseas, puedes realizar una nueva reserva
para otra fecha u horario.

Saludos,

La Mesa Dorada
"""

    mensaje.attach(
        MIMEText(cuerpo, "plain")
    )

    # =================================================
    # CONEXIÓN CON GMAIL
    # =================================================

    try:

        servidor = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=10
        )

        servidor.starttls()

        servidor.login(
            remitente,
            password
        )

        servidor.sendmail(
            remitente,
            correo,
            mensaje.as_string()
        )

        servidor.quit()

        print("Correo enviado correctamente.")

        return True

    except Exception as error:

        # IMPORTANTE:
        # Si Gmail falla, la aplicación NO se cae.
        print("No se pudo enviar el correo:", error)

        return False


# =====================================================
# CREAR BASE DE DATOS
# =====================================================

def crear_bd():

    conexion = sqlite3.connect(
        "restaurante.db"
    )

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre TEXT,

            correo TEXT,

            telefono TEXT,

            fecha TEXT,

            hora TEXT,

            personas TEXT,

            comentarios TEXT,

            estado TEXT DEFAULT 'Pendiente'

        )
    """)

    conexion.commit()

    conexion.close()


crear_bd()


# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# =====================================================
# GUARDAR RESERVACIÓN
# =====================================================

@app.route(
    "/reservar",
    methods=["POST"]
)
def reservar():

    conexion = sqlite3.connect(
        "restaurante.db"
    )

    cursor = conexion.cursor()

    fecha = request.form["fecha"]
    hora = request.form["hora"]

    # =================================================
    # VALIDAR FECHA
    # =================================================

    try:

        fecha_reserva = datetime.strptime(
            fecha,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        conexion.close()

        return """
        <h2>La fecha no es válida.</h2>
        <a href="/">Volver</a>
        """

    fecha_actual = datetime.now().date()

    if fecha_reserva < fecha_actual:

        conexion.close()

        return """
        <h2>No se permiten reservas para fechas pasadas.</h2>
        <a href="/">Volver</a>
        """

    # =================================================
    # GUARDAR RESERVA
    # =================================================

    cursor.execute("""
        INSERT INTO reservas
        (
            nombre,
            correo,
            telefono,
            fecha,
            hora,
            personas,
            comentarios
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        request.form["nombre"],
        request.form["correo"],
        request.form["telefono"],
        request.form["fecha"],
        request.form["hora"],
        request.form["personas"],
        request.form["comentarios"]

    ))

    conexion.commit()

    conexion.close()

    return render_template(
        "gracias.html"
    )


# =====================================================
# UBICACIÓN
# =====================================================

@app.route("/ubicacion")
def ubicacion():

    return render_template(
        "ubicacion.html"
    )


# =====================================================
# NOSOTROS
# =====================================================

@app.route("/nosotros")
def nosotros():

    return render_template(
        "nosotros.html"
    )


# =====================================================
# CONTACTO
# =====================================================

@app.route("/contacto")
def contacto():

    return render_template(
        "contacto.html"
    )


# =====================================================
# PROMOCIONES
# =====================================================

@app.route("/promociones")
def promociones():

    return render_template(
        "promociones.html"
    )


# =====================================================
# EVENTOS
# =====================================================

@app.route("/eventos")
def eventos():

    return render_template(
        "eventos.html"
    )


# =====================================================
# HORARIOS
# =====================================================

@app.route("/horarios")
def horarios():

    return render_template(
        "horarios.html"
    )


# =====================================================
# TESTIMONIOS
# =====================================================

@app.route("/testimonios")
def testimonios():

    return render_template(
        "testimonios.html"
    )


# =====================================================
# PANEL DE ADMINISTRACIÓN
# =====================================================

@app.route("/admin")
def admin():

    conexion = sqlite3.connect(
        "restaurante.db"
    )

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM reservas
        ORDER BY id DESC
    """)

    reservas = cursor.fetchall()

    conexion.close()

    return render_template(
        "admin.html",
        reservas=reservas
    )


# =====================================================
# ACEPTAR RESERVACIÓN
# =====================================================

@app.route(
    "/aceptar/<int:id>"
)
def aceptar(id):

    conexion = sqlite3.connect(
        "restaurante.db"
    )

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre,
            correo,
            fecha,
            hora,
            personas
        FROM reservas
        WHERE id=?
    """, (id,))

    reserva = cursor.fetchone()

    if reserva:

        nombre, correo, fecha, hora, personas = reserva

        # =================================================
        # CAMBIAR ESTADO A ACEPTADA
        # =================================================

        cursor.execute("""
            UPDATE reservas
            SET estado = 'Aceptada'
            WHERE id = ?
        """, (id,))

        conexion.commit()

        conexion.close()

        # =================================================
        # ENVIAR CORREO
        # =================================================

        enviar_notificacion(
            correo,
            nombre,
            fecha,
            hora,
            personas,
            "Aceptada"
        )

    else:

        conexion.close()

    # Volver al panel
    return redirect("/admin")


# =====================================================
# RECHAZAR Y ELIMINAR RESERVACIÓN
# =====================================================

@app.route(
    "/rechazar/<int:id>",
    methods=["POST"]
)
def rechazar(id):

    conexion = sqlite3.connect(
        "restaurante.db"
    )

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre,
            correo,
            fecha,
            hora,
            personas
        FROM reservas
        WHERE id=?
    """, (id,))

    reserva = cursor.fetchone()

    if reserva:

        nombre, correo, fecha, hora, personas = reserva

        # =================================================
        # ELIMINAR RESERVA
        # =================================================

        cursor.execute("""
            DELETE FROM reservas
            WHERE id=?
        """, (id,))

        conexion.commit()

        conexion.close()

        # =================================================
        # ENVIAR CORREO DE RECHAZO
        # =================================================

        enviar_notificacion(
            correo,
            nombre,
            fecha,
            hora,
            personas,
            "Rechazada"
        )

    else:

        conexion.close()

    # =================================================
    # VOLVER AL PANEL
    # =================================================

    return redirect("/admin")


# =====================================================
# INICIAR FLASK
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )