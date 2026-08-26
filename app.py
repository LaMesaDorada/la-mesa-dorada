from flask import Flask, render_template, request, redirect
import sqlite3
import os
import resend
from datetime import datetime

app = Flask(__name__)


# =====================================================
# CONFIGURACIÓN DE RESEND
# =====================================================

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# =====================================================
# ENVIAR CORREO
# =====================================================

def enviar_notificacion(correo, nombre, fecha, hora, personas, estado):

    if not RESEND_API_KEY:

        print("ERROR: No existe RESEND_API_KEY en Render.")

        return False


    # =================================================
    # RESERVA ACEPTADA
    # =================================================

    if estado == "Aceptada":

        asunto = "Reserva aceptada - La Mesa Dorada"

        cuerpo = f"""
        <html>
        <body>

        <h2>Reserva aceptada</h2>

        <p>Hola <strong>{nombre}</strong>:</p>

        <p>
        Nos complace informarte que tu reserva en
        <strong>La Mesa Dorada</strong> ha sido ACEPTADA.
        </p>

        <h3>Detalles de tu reserva:</h3>

        <p>
        <strong>Fecha:</strong> {fecha}<br>
        <strong>Hora:</strong> {hora}<br>
        <strong>Personas:</strong> {personas}
        </p>

        <p>
        Te esperamos en nuestro restaurante.
        </p>

        <p>
        ¡Gracias por elegir La Mesa Dorada!
        </p>

        <p>
        Saludos,<br>
        <strong>La Mesa Dorada</strong>
        </p>

        </body>
        </html>
        """


    # =================================================
    # RESERVA RECHAZADA
    # =================================================

    else:

        asunto = "Reserva rechazada - La Mesa Dorada"

        cuerpo = f"""
        <html>
        <body>

        <h2>Reserva rechazada</h2>

        <p>Hola <strong>{nombre}</strong>:</p>

        <p>
        Lamentamos informarte que tu reserva en
        <strong>La Mesa Dorada</strong> ha sido RECHAZADA.
        </p>

        <h3>Detalles de la reserva:</h3>

        <p>
        <strong>Fecha:</strong> {fecha}<br>
        <strong>Hora:</strong> {hora}<br>
        <strong>Personas:</strong> {personas}
        </p>

        <p>
        Si lo deseas, puedes realizar una nueva reserva
        para otra fecha u horario.
        </p>

        <p>
        Saludos,<br>
        <strong>La Mesa Dorada</strong>
        </p>

        </body>
        </html>
        """


    # =================================================
    # ENVIAR CON RESEND
    # =================================================

    try:

        parametros = {
            "from": "La Mesa Dorada <onboarding@resend.dev>",
            "to": [correo],
            "subject": asunto,
            "html": cuerpo
        }

        resultado = resend.Emails.send(parametros)

        print("Correo enviado:", resultado)

        return True


    except Exception as error:

        print("ERROR DE RESEND:", error)

        return False


# =====================================================
# CREAR BASE DE DATOS
# =====================================================

def crear_bd():

    conexion = sqlite3.connect("restaurante.db")

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

    return render_template("index.html")


# =====================================================
# GUARDAR RESERVACIÓN
# =====================================================

@app.route("/reservar", methods=["POST"])
def reservar():

    conexion = sqlite3.connect("restaurante.db")

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


    return render_template("gracias.html")


# =====================================================
# UBICACIÓN
# =====================================================

@app.route("/ubicacion")
def ubicacion():

    return render_template("ubicacion.html")


# =====================================================
# NOSOTROS
# =====================================================

@app.route("/nosotros")
def nosotros():

    return render_template("nosotros.html")


# =====================================================
# CONTACTO
# =====================================================

@app.route("/contacto")
def contacto():

    return render_template("contacto.html")


# =====================================================
# PROMOCIONES
# =====================================================

@app.route("/promociones")
def promociones():

    return render_template("promociones.html")


# =====================================================
# EVENTOS
# =====================================================

@app.route("/eventos")
def eventos():

    return render_template("eventos.html")


# =====================================================
# HORARIOS
# =====================================================

@app.route("/horarios")
def horarios():

    return render_template("horarios.html")


# =====================================================
# TESTIMONIOS
# =====================================================

@app.route("/testimonios")
def testimonios():

    return render_template("testimonios.html")


# =====================================================
# PANEL DE ADMINISTRACIÓN
# =====================================================

@app.route("/admin")
def admin():

    conexion = sqlite3.connect("restaurante.db")

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

@app.route("/aceptar/<int:id>")
def aceptar(id):

    conexion = sqlite3.connect("restaurante.db")

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


        # Cambiar estado

        cursor.execute("""
            UPDATE reservas
            SET estado = 'Aceptada'
            WHERE id = ?
        """, (id,))


        conexion.commit()

        conexion.close()


        # Enviar correo

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


    return redirect("/admin")


# =====================================================
# RECHAZAR Y ELIMINAR RESERVACIÓN
# =====================================================

@app.route("/rechazar/<int:id>", methods=["POST"])
def rechazar(id):

    conexion = sqlite3.connect("restaurante.db")

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


        # Eliminar reserva

        cursor.execute("""
            DELETE FROM reservas
            WHERE id=?
        """, (id,))


        conexion.commit()

        conexion.close()


        # Enviar correo de rechazo

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

