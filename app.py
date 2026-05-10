from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager
from models import User, Liga, Equipo, Jugador, Temporada, Estadistica
from functools import wraps
from flask import abort
import os

print("🔥 APP PY CARGADO CORRECTAMENTE")


def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:
                return redirect("/login")

            if current_user.role not in roles:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function
    return wrapper


# ------------------ CONFIGURACIÓN ------------------
app = Flask(__name__)
app.secret_key = "clave_secreta"
@app.route("/test2")
def test2():
    return "TEST 2 OK"

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()


# ------------------ LOGIN ------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect("/home")

        error = "Usuario o contraseña incorrecta"

    return render_template("login.html", error=error)


# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "jugador")

        if User.query.filter_by(username=username).first():
            error = "El usuario ya existe"
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")

    return render_template("register.html", error=error)

# ------------------ HOME (LANDING) ------------------
@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/")
def index():
    return redirect("/login")

# ------------------ USERS ------------------
@app.route("/users")
@login_required
def users():
    users_list = User.query.all()
    return render_template("users.html", users=users_list)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit(id):

    user = User.query.get_or_404(id)

    if request.method == "POST":
        user.username = request.form["username"]
        user.role = request.form["role"]
        db.session.commit()
        return redirect("/users")

    return render_template("edit_user.html", user=user)


@app.route("/delete/<int:id>")
@login_required
@roles_required("admin")
def delete(id):

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()

    return redirect("/users")


# ------------------ JUGADORES ------------------
@app.route("/jugadores")
@login_required
def jugadores():

    equipo_id = request.args.get("equipo_id")
    posicion = request.args.get("posicion")
    ordenar = request.args.get("ordenar")

    jugadores_query = Jugador.query

    if equipo_id:
        jugadores_query = jugadores_query.filter_by(equipo_id=equipo_id)

    if posicion:
        jugadores_query = jugadores_query.filter_by(posicion=posicion)

    jugadores_list = jugadores_query.all()

    if ordenar == "puntos":
        jugadores_list.sort(key=lambda j: sum(e.puntos for e in j.estadisticas), reverse=True)
    elif ordenar == "rebotes":
        jugadores_list.sort(key=lambda j: sum(e.rebotes for e in j.estadisticas), reverse=True)
    elif ordenar == "asistencias":
        jugadores_list.sort(key=lambda j: sum(e.asistencias for e in j.estadisticas), reverse=True)

    equipos = Equipo.query.all()

    return render_template("jugadores.html", jugadores=jugadores_list, equipos=equipos)


@app.route("/jugadores/crear", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_jugador():

    if request.method == "POST":
        nuevo = Jugador(
            nombre=request.form["nombre"],
            apellido=request.form["apellido"],
            numero=int(request.form["numero"]),
            posicion=request.form["posicion"],
            edad=int(request.form["edad"]),
            equipo_id=int(request.form["equipo_id"])
        )

        db.session.add(nuevo)
        db.session.commit()
        return redirect("/jugadores")

    equipos = Equipo.query.all()
    return render_template("crear_jugador.html", equipos=equipos)


@app.route("/jugadores/edit/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def edit_jugador(id):

    jugador = Jugador.query.get_or_404(id)

    if request.method == "POST":
        jugador.nombre = request.form["nombre"]
        jugador.apellido = request.form["apellido"]
        jugador.numero = int(request.form["numero"])
        jugador.posicion = request.form["posicion"]
        jugador.edad = int(request.form["edad"])
        jugador.equipo_id = int(request.form["equipo_id"])

        db.session.commit()
        return redirect("/jugadores")

    equipos = Equipo.query.all()
    return render_template("edit_jugador.html", jugador=jugador, equipos=equipos)


@app.route("/jugadores/delete/<int:id>")
@login_required
@roles_required("entrenador", "admin")
def delete_jugador(id):

    jugador = Jugador.query.get_or_404(id)
    equipo_id = jugador.equipo_id

    db.session.delete(jugador)
    db.session.commit()

    return redirect(f"/equipos/{equipo_id}/jugadores")


# ------------------ ESTADÍSTICAS ------------------
@app.route("/estadisticas/crear/<int:jugador_id>", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_estadisticas(jugador_id):

    jugador = Jugador.query.get_or_404(jugador_id)
    temporadas = Temporada.query.all()

    if request.method == "POST":

        nueva = Estadistica(
            jugador_id=jugador.id,
            temporada_id=int(request.form["temporada_id"]),
            partidos=int(request.form["partidos"]),
            puntos=int(request.form["puntos"]),
            rebotes=int(request.form["rebotes"]),
            asistencias=int(request.form["asistencias"])
        )

        db.session.add(nueva)
        db.session.commit()

        return redirect(f"/equipos/{jugador.equipo_id}/jugadores")

    return render_template("crear_estadisticas.html", jugador=jugador, temporadas=temporadas)


@app.route("/estadisticas/edit/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def edit_estadistica(id):

    stat = Estadistica.query.get_or_404(id)

    if request.method == "POST":

        stat.partidos = int(request.form["partidos"])
        stat.puntos = int(request.form["puntos"])
        stat.rebotes = int(request.form["rebotes"])
        stat.asistencias = int(request.form["asistencias"])

        db.session.commit()

        return redirect(f"/equipos/{stat.jugador.equipo_id}/jugadores")

    return render_template("edit_estadistica.html", stat=stat)


@app.route("/estadisticas/delete/<int:id>")
@login_required
@roles_required("entrenador", "admin")
def delete_estadistica(id):

    stat = Estadistica.query.get_or_404(id)
    equipo_id = stat.jugador.equipo_id

    db.session.delete(stat)
    db.session.commit()

    return redirect(f"/equipos/{equipo_id}/jugadores")



# ------------------ LIGAS ------------------

@app.route("/ligas")
@login_required
def ligas():
    ligas_list = Liga.query.all()
    return render_template("ligas.html", ligas=ligas_list)


@app.route("/ligas/crear", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_liga():

    if request.method == "POST":
        nueva = Liga(
            nombre=request.form["nombre"],
            ciudad=request.form["ciudad"],
            categoria=request.form["categoria"]
        )

        db.session.add(nueva)
        db.session.commit()

        return redirect("/ligas")

    return render_template("crear_liga.html")

@app.route("/ligas/<int:id>")
@login_required
def ver_liga(id):
    liga = Liga.query.get_or_404(id)
    equipos = Equipo.query.filter_by(liga_id=id).all()
    return render_template("liga_detalle.html", liga=liga, equipos=equipos)

# ------------------ TEMPORADAS ------------------

@app.route("/temporadas")
@login_required
def temporadas():
    temporadas_list = Temporada.query.all()
    return render_template("temporadas.html", temporadas=temporadas_list)


@app.route("/temporadas/crear", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_temporada():

    if request.method == "POST":
        nueva = Temporada(
            nombre=request.form["nombre"],
            liga_id=int(request.form["liga_id"])
        )

        db.session.add(nueva)
        db.session.commit()

        return redirect("/temporadas")

    ligas = Liga.query.all()
    return render_template("crear_temporada.html", ligas=ligas)

#---------------- COMAPRADOR --------------
@app.route("/comparador", methods=["GET", "POST"])
@login_required
def comparador():

    ligas = Liga.query.all()

    # 🔽 FILTROS (GET)
    liga_id = request.args.get("liga_id")
    equipo_id = request.args.get("equipo_id")

    equipos = Equipo.query.all()

    jugadores_query = Jugador.query

    if equipo_id:
        jugadores_query = jugadores_query.filter_by(equipo_id=equipo_id)

    if liga_id:
        equipos_liga = Equipo.query.filter_by(liga_id=liga_id).all()
        equipos_ids = [e.id for e in equipos_liga]
        jugadores_query = jugadores_query.filter(Jugador.equipo_id.in_(equipos_ids))

    jugadores = jugadores_query.all()

    jugador1 = None
    jugador2 = None

    # 🔽 COMPARACIÓN (POST REAL)
    if request.method == "POST":
        jugador1_id = request.form.get("jugador1")
        jugador2_id = request.form.get("jugador2")

        if jugador1_id and jugador2_id:
            jugador1 = Jugador.query.get(int(jugador1_id))
            jugador2 = Jugador.query.get(int(jugador2_id))

    return render_template(
        "comparador.html",
        ligas=ligas,
        equipos=equipos,
        jugadores=jugadores,
        jugador1=jugador1,
        jugador2=jugador2
    )

@app.route("/ligas/<int:liga_id>/crear_equipo", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_equipo_liga(liga_id):

    liga = Liga.query.get_or_404(liga_id)
    temporadas = Temporada.query.filter_by(liga_id=liga_id).all()  # 🔥 CLAVE

    if request.method == "POST":

        equipo = Equipo(
            nombre=request.form["nombre"],
            liga_id=liga.id,
            temporada_id=int(request.form["temporada_id"])  # 🔥 ya no será None
        )

        db.session.add(equipo)
        db.session.commit()

        return redirect(f"/ligas/{liga.id}")

    return render_template(
        "crear_equipo.html",
        liga=liga,
        temporadas=temporadas   # 🔥 CLAVE
    )

# ---------------- EQUIPOS --------------
@app.route("/equipos/crear", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def crear_equipo():

    if request.method == "POST":

        equipo = Equipo(
            nombre=request.form["nombre"],
            liga_id=int(request.form["liga_id"]),
            temporada_id = int(request.form["temporada_id"])
        )

        db.session.add(equipo)
        db.session.commit()

        return redirect("/ligas")

    ligas = Liga.query.all()
    return render_template("crear_equipo.html", ligas=ligas)

@app.route("/equipos/<int:id>/jugadores")
@login_required
def jugadores_equipo(id):

    equipo = Equipo.query.get_or_404(id)
    jugadores_list = Jugador.query.filter_by(equipo_id=id).all()

    return render_template(
        "jugadores_equipo.html",
        equipo=equipo,
        jugadores=jugadores_list
    )

@app.route("/equipos/edit/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("entrenador", "admin")
def edit_equipo(id):

    equipo = Equipo.query.get_or_404(id)

    if request.method == "POST":

        equipo.nombre = request.form["nombre"]
        equipo.liga_id = int(request.form["liga_id"])

        db.session.commit()

        return redirect(f"/ligas/{equipo.liga_id}")

    ligas = Liga.query.all()

    return render_template(
        "editar_equipo.html",
        equipo=equipo,
        ligas=ligas
    )


#debug
@app.route("/debug")
def debug():
    return "FLASK OK"



# ----------- LOGOUT -----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)