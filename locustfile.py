from locust import HttpUser, task, between
import random
import string

class ScoutingUser(HttpUser):
    wait_time = between(1, 3)

    def generate_password(self):
        # Asegura: mayúscula + minúscula + número + símbolo + mínimo 8 chars

        upper = random.choice(string.ascii_uppercase)
        lower = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        symbol = random.choice("!@#$%&*?")
        
        बाकी = ''.join(random.choices(string.ascii_letters + string.digits, k=4))

        password_list = list(upper + lower + digit + symbol + बाकी)
        random.shuffle(password_list)

        return ''.join(password_list)

    def on_start(self):
        # usuario único
        self.username = f"user_{random.randint(1, 1000000)}"

        # contraseña segura
        self.password = self.generate_password()

        # registro
        self.client.post("/register", data={
            "username": self.username,
            "password": self.password
        })

        # login
        self.client.post("/login", data={
            "username": self.username,
            "password": self.password
        })

  

    @task(2)
    def ver_jugadores(self):
        self.client.get("/jugadores")

    @task(1)
    def comparar(self):
        self.client.get("/comparador?j1=1&j2=2")