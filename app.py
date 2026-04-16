from flask import Flask, render_template_string, request, redirect, session
import random

app = Flask(__name__)
app.secret_key = "safe_key_123"

# ================= USERS =================
USERS = {"admin": "1234"}

# ================= STATE =================
pump = False
zones = [False, False, False]
mode = "AUTO"

# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
</head>
<body style="background:#0b1220;color:white;text-align:center;font-family:Arial;padding:40px;">

<h2>🌱 Smart Saqya SCADA</h2>

<form method="post">
<input name="username" placeholder="Username" style="padding:10px;width:80%;"><br><br>
<input name="password" type="password" placeholder="Password" style="padding:10px;width:80%;"><br><br>
<button style="padding:10px 20px;background:#22c55e;color:white;">Login</button>
</form>

{% if error %}
<p style="color:red;">Wrong login</p>
{% endif %}

</body>
</html>
"""

# ================= DASHBOARD =================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SCADA</title>
</head>

<body style="background:#0b1220;color:white;font-family:Arial;text-align:center;">

<h2>🏭 SCADA SYSTEM</h2>

<p>⚙ Mode: {{mode}}</p>
<p>⚡ Pump: {{pump}}</p>

<a href="/pump/on">ON</a> |
<a href="/pump/off">OFF</a>

<hr>

<h3>🌿 Zones</h3>

{% for i in range(3) %}
<p>
Zone {{i+1}}:
{% if zones[i] %}
🟢 ON
{% else %}
🔴 OFF
{% endif %}

<a href="/zone/{{i}}/on">ON</a>
<a href="/zone/{{i}}/off">OFF</a>
</p>
{% endfor %}

<hr>

<p>🌡 Temp: {{temp}}</p>
<p>💧 Soil: {{soil}}</p>
<p>🏞 Well: {{well}}</p>

</body>
</html>
"""

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    error = False

    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in USERS and USERS[u] == p:
            session["user"] = u
            return redirect("/dashboard")
        else:
            error = True

    return render_template_string(LOGIN_HTML, error=error)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    global pump, zones, mode

    temp = random.randint(20,40)
    soil = random.randint(400,800)
    well = random.randint(10,100)

    if mode == "AUTO":
        pump = any(zones) and soil < 700 and well > 30

    return render_template_string(
        DASHBOARD_HTML,
        mode=mode,
        pump="ON" if pump else "OFF",
        zones=zones,
        temp=temp,
        soil=soil,
        well=well
    )

# ================= CONTROL =================
@app.route("/pump/on")
def pump_on():
    global pump
    pump = True
    return redirect("/dashboard")

@app.route("/pump/off")
def pump_off():
    global pump, zones
    pump = False
    zones = [False, False, False]
    return redirect("/dashboard")

@app.route("/zone/<int:z>/on")
def zone_on(z):
    global zones
    zones[z] = True
    return redirect("/dashboard")

@app.route("/zone/<int:z>/off")
def zone_off(z):
    global zones
    zones[z] = False
    return redirect("/dashboard")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
