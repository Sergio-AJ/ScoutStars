from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ MODELO USUARIO ------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="jugador")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# ------------------ MODELO LIGA ------------------
class Liga(db.Model):
    __tablename__ = "ligas"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(50))
    categoria = db.Column(db.String(50))

    equipos = db.relationship("Equipo", backref="liga", lazy=True)

    # ---------- AÑADIDO: contar equipos ----------
    def total_equipos(self):
        return len(self.equipos)

    def __repr__(self):
        return f"<Liga {self.nombre}>"

# ------------------ MODELO TEMPORADA ------------------
class Temporada(db.Model):
    __tablename__ = "temporadas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  # Ej: 2025/2026

    liga_id = db.Column(db.Integer, db.ForeignKey("ligas.id"), nullable=False)

    # relación con liga
    liga = db.relationship("Liga", backref="temporadas", lazy=True)

    def __repr__(self):
        return f"<Temporada {self.nombre} - Liga {self.liga.nombre}>"


# ------------------ MODELO EQUIPO ------------------
class Equipo(db.Model):
    __tablename__ = "equipos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    liga_id = db.Column(db.Integer, db.ForeignKey("ligas.id"), nullable=False)
    temporada_id = db.Column(db.Integer, db.ForeignKey("temporadas.id"), nullable=False)

    temporada = db.relationship("Temporada", backref="equipos", lazy=True)

    jugadores = db.relationship("Jugador", backref="equipo", lazy=True)

    # ---------- AÑADIDO: contar jugadores ----------
    def total_jugadores(self):
        return len(self.jugadores)

    # ---------- AÑADIDO: obtener nombre liga ----------
    def nombre_liga(self):
        if self.liga:
            return self.liga.nombre
        return "Sin liga"

    def __repr__(self):
        return f"<Equipo {self.nombre}>"


# ------------------ MODELO JUGADOR ------------------
class Jugador(db.Model):
    __tablename__ = "jugadores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    posicion = db.Column(db.String(20))
    edad = db.Column(db.Integer)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)

    # ---------- AÑADIDO: nombre completo ----------
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"<Jugador {self.nombre} {self.apellido} - Equipo {self.equipo.nombre}>"

# ------------------ MODELO ESTADISTICAS ------------------
class Estadistica(db.Model):
    __tablename__ = "estadisticas"

    id = db.Column(db.Integer, primary_key=True)

    jugador_id = db.Column(db.Integer, db.ForeignKey("jugadores.id"), nullable=False)
    temporada_id = db.Column(db.Integer, db.ForeignKey("temporadas.id"), nullable=False)

    # stats básicas (no te compliques más)
    partidos = db.Column(db.Integer, default=0)
    puntos = db.Column(db.Integer, default=0)
    rebotes = db.Column(db.Integer, default=0)
    asistencias = db.Column(db.Integer, default=0)

    # relaciones
    jugador = db.relationship("Jugador", backref="estadisticas", lazy=True)
    temporada = db.relationship("Temporada", backref="estadisticas", lazy=True)

    def __repr__(self):
        return f"<Stats {self.jugador.nombre} {self.temporada.nombre}>"

# ------------------ LOGIN MANAGER ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))