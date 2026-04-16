from flask import Flask, render_template_string, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "smart_saqya_key"

# ================= USERS =================
USERS = {"admin": "1234"}

# ================= STATE =================
pump_state = False
zones = [False, False, False]
mode = "AUTO"
manual_override = False

# ================= HISTORY =================
temp_history = []
soil_history = []
well_history = []

# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SCADA LOGIN</title>
</head>
<body style="background:#0a0f1a;color:white;text-align:center;font-family:Arial;padding:40px;">

<h2>🏭 Smart Saqya SCADA</h2>

<form method="post">
<input name="username" placeholder="Username" style="padding:10px;width:80%;"><br><br>
<input name="password" type="password" placeholder="Password" style="padding:10px;width:80%;"><br><br>
<button style="padding:10px 20px;background:#22c55e;color:white;">Login</button>
</form>

{% if error %}
<p style="color:red;">Wrong credentials</p>
{% endif %}

</body>
</html>
"""

# ================= SCADA DASHBOARD =================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SCADA PRO</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body{
    margin:0;
    font-family:Arial;
    background:#0a0f1a;
    color:#e5e7eb;
}

/* HEADER */
.header{
    padding:15px;
    background:#111827;
    text-align:center;
    font-size:20px;
    font-weight:bold;
    border-bottom:1px solid #1f2937;
}

/* GRID */
.grid{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap:10px;
    padding:10px;
}

/* CARDS */
.card{
    background:#111827;
    border:1px solid #1f2937;
    padding:15px;
    border-radius:12px;
}

/* COLORS */
.green{color:#22c55e;}
.red{color:#ef4444;}
.yellow{color:#f59e0b;}
.small{color:#9ca3af;font-size:13px;}

/* LED */
.led{
    width:12px;
    height:12px;
    border-radius:50%;
    display:inline-block;
}
.on{background:#22c55e; box-shadow:0 0 8px #22c55e;}
.off{background:#ef4444; box-shadow:0 0 8px #ef4444;}

a{color:#22c55e;text-decoration:none;margin:5px;}
</style>
</head>

<body>

<div class="header">
🏭 INDUSTRIAL SMART SAQYA SCADA SYSTEM
</div>

<!-- STATUS -->
<div class="grid">

<div class="card">
<h3>⚙ MODE</h3>
<p class="{% if mode=='AUTO' %}green{% else %}yellow{% endif %}">{{mode}}</p>
<a href="/mode/AUTO">AUTO</a> |
<a href="/mode/MANUAL">MANUAL</a>
</div>

<div class="card">
<h3>⚡ PUMP STATUS</h3>
<p>
<span class="led {% if pump=='ON' %}on{% else %}off{% endif %}"></span>
<b class="{% if pump=='ON' %}green{% else %}red{% endif %}">{{pump}}</b>
</p>
<a href="/pump/on">ON</a> |
<a href="/pump/off">OFF</a>
</div>

<div class="card">
<h3>📡 LIVE DATA</h3>
🌡 {{temp}} °C<br>
💧 {{soil}}<br>
🏞 {{well}}
</div>

</div>

<!-- AI -->
<div class="grid">

<div class="card">
<h3>🤖 FAILURE AI</h3>
<p>{{failure_status}}</p>
<p class="small">Risk: {{risk}}</p>

{% for r in failure_reasons %}
<p class="red">⚠ {{r}}</p>
{% endfor %}
</div>

<div class="card">
<h3>🌦 WEATHER AI</h3>
<p>{{weather}}</p>
</div>

<div class="card">
<h3>🚨 SYSTEM STATUS</h3>

{% if risk < 40 %}
<p class="green">🟢 STABLE</p>
{% elif risk < 70 %}
<p class="yellow">🟡 WARNING</p>
{% else %}
<p class="red">🔴 CRITICAL</p>
{% endif %}
</div>

</div>

<!-- ZONES -->
<div class="card" style="margin:10px;">
<h3>🌿 ZONES CONTROL</h3>

{% for i in range(3) %}
<p>
Zone {{i+1}}:
{% if zones[i] %}
<span class="green">🟢 ON</span>
{% else %}
<span class="red">🔴 OFF</span>
{% endif %}
<a href="/zone/{{i}}/on">ON</a>
<a href="/zone/{{i}}/off">OFF</a>
</p>
{% endfor %}
</div>

<!-- CHART -->
<div class="card" style="margin:10px;">
<h3>📊 SCADA ANALYTICS</h3>
<canvas id="chart"></canvas>
</div>

<script>
new Chart(document.getElementById("chart"), {
    type: 'line',
    data: {
        labels: {{labels}},
        datasets: [
            {
                label: 'Temp',
                data: {{temp_data}},
                borderColor: '#22c55e'
            },
            {
                label: 'Soil',
                data: {{soil_data}},
                borderColor: '#f59e0b'
            },
            {
                label: 'Well',
                data: {{well_data}},
                borderColor: '#ef4444'
            }
        ]
    }
});
</script>

</body>
</html>
"""

# ================= AI FUNCTIONS =================
def failure_ai(temp, soil, well, pump):
    risk = 0
    reasons = []

    if soil > 750:
        risk += 40
        reasons.append("Soil too dry")

    if well < 25:
        risk += 40
        reasons.append("Low water level")

    if temp > 38:
        risk += 20
        reasons.append("High temperature")

    if pump and well < 20:
        risk += 30
        reasons.append("Pump stress")

    if risk >= 70:
        status = "🔴 CRITICAL"
    elif risk >= 40:
        status = "🟡 WARNING"
    else:
        status = "🟢 SAFE"

    return status, reasons, risk


def weather_ai(history):
    if len(history) < 5:
        return "🌤 Collecting data..."

    avg = sum(history[-5:]) / 5

    if avg > 35:
        return "☀ Hot & Dry Tomorrow"
    elif avg > 25:
        return "🌤 Normal Weather"
    else:
        return "🌧 Rain Possible"


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

    global pump_state, zones, mode, manual_override

    temp = random.randint(20, 40)
    soil = random.randint(400, 800)
    well = random.randint(10, 100)

    temp_history.append(temp)
    soil_history.append(soil)
    well_history.append(well)

    if len(temp_history) > 15:
        temp_history.pop(0)
        soil_history.pop(0)
        well_history.pop(0)

    # AUTO CONTROL
    if mode == "AUTO" and not manual_override:
        pump_state = any(zones) and soil < 700 and well > 30

    # AI
    failure_status, failure_reasons, risk = failure_ai(temp, soil, well, pump_state)
    weather = weather_ai(temp_history)

    labels = list(range(len(temp_history)))

    return render_template_string(
        DASHBOARD_HTML,
        mode=mode,
        pump="ON" if pump_state else "OFF",
        zones=zones,
        temp=temp,
        soil=soil,
        well=well,
        failure_status=failure_status,
        failure_reasons=failure_reasons,
        risk=risk,
        weather=weather,
        labels=labels,
        temp_data=temp_history,
        soil_data=soil_history,
        well_data=well_history
    )


# ================= CONTROL =================
@app.route("/pump/on")
def pump_on():
    global pump_state, manual_override
    pump_state = True
    manual_override = True
    return redirect("/dashboard")

@app.route("/pump/off")
def pump_off():
    global pump_state, zones, manual_override
    pump_state = False
    zones = [False, False, False]
    manual_override = True
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

@app.route("/mode/<m>")
def set_mode(m):
    global mode, manual_override
    mode = m
    manual_override = False
    return redirect("/dashboard")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
