
from flask import Flask, render_template_string, request, redirect, session, jsonify
import random

app = Flask(__name__)
app.secret_key = "smart_saqya_key"

# ================= USERS =================
USERS = {"admin": "1234"}

# ================= STATE =================
pump_state = False
zones = [False, False, False]
mode = "AUTO"

# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SCADA LOGIN</title>
</head>
<body style="background:#020617;color:white;text-align:center;font-family:Arial;padding:40px;">
<h2>🏭 SMART SAQYA SCADA</h2>

<form method="post">
<input name="username" placeholder="Username" style="padding:10px;width:80%;"><br><br>
<input name="password" type="password" placeholder="Password" style="padding:10px;width:80%;"><br><br>
<button style="padding:10px 20px;background:#22c55e;color:white;">LOGIN</button>
</form>

{% if error %}
<p style="color:red;">❌ Wrong credentials</p>
{% endif %}

</body>
</html>
"""

# ================= DASHBOARD =================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SCADA CONTROL ROOM</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body{margin:0;background:#020617;color:#e5e7eb;font-family:Arial;}

.topbar{
    background:#0b1220;
    padding:15px;
    text-align:center;
    font-weight:bold;
    color:#38bdf8;
}

.card{
    background:#0b1220;
    margin:10px;
    padding:15px;
    border-radius:10px;
    border:1px solid #1f2937;
}

h3{color:#38bdf8;}

a{
    display:inline-block;
    padding:8px 12px;
    margin:5px;
    border-radius:8px;
    text-decoration:none;
    font-weight:bold;
}

/* BUTTONS */
.start{background:#16a34a;color:white;box-shadow:0 0 10px #16a34a;}
.stop{background:#dc2626;color:white;box-shadow:0 0 10px #dc2626;}

.led{width:12px;height:12px;border-radius:50%;display:inline-block;}
.on{background:#22c55e;box-shadow:0 0 10px #22c55e;}
.off{background:#ef4444;box-shadow:0 0 10px #ef4444;}

/* ALARM */
.alarm{
    position:fixed;
    top:20px;
    right:20px;
    background:red;
    color:white;
    padding:15px;
    border-radius:10px;
    font-weight:bold;
    display:none;
    animation:flash 0.5s infinite;
}

@keyframes flash{
    0%{opacity:1;}
    50%{opacity:0.2;}
    100%{opacity:1;}
}

/* ZONES */
.zone{
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
    border:1px solid #1f2937;
}

.zone0{background:rgba(34,197,94,0.08);}
.zone1{background:rgba(59,130,246,0.08);}
.zone2{background:rgba(245,158,11,0.08);}

.bar{
    width:100%;
    height:10px;
    background:#111827;
    border-radius:10px;
    overflow:hidden;
    margin:5px 0;
}

.fill{
    height:100%;
    width:0%;
    transition:0.5s;
}

#bar0{background:#22c55e;}
#bar1{background:#3b82f6;}
#bar2{background:#f59e0b;}

.dry-flash{
    animation:flash 0.6s infinite;
}
</style>
</head>

<body>

<div class="topbar">🏭 SMART SAQYA SCADA CONTROL ROOM</div>

<div id="alarm" class="alarm">🚨 CRITICAL ALERT</div>

<audio id="sound" loop>
<source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg">
</audio>

<!-- MODE -->
<div class="card">
<h3>⚙ MODE</h3>
<b id="modeBox">{{mode}}</b><br><br>

<a href="/mode/AUTO" class="start">AUTO</a>
<a href="/mode/MANUAL" class="stop">MANUAL</a>
</div>

<!-- PUMP -->
<div class="card">
<h3>⚡ PUMP CONTROL</h3>
<span class="led {% if pump=='ON' %}on{% else %}off{% endif %}"></span>
<b>{{pump}}</b><br><br>

<a href="/pump/on" class="start">▶ START</a>
<a href="/pump/off" class="stop">⛔ STOP</a>
</div>

<!-- LIVE -->
<div class="card">
<h3>📡 LIVE DATA</h3>
🌡 Temp: <span id="temp">--</span><br>
💧 Soil: <span id="soil">--</span><br>
🏞 Water: <span id="well">--</span>
</div>

<!-- ZONES -->
<div class="card">
<h3>🌿 ZONES CONTROL</h3>

{% for i in range(3) %}
<div class="zone zone{{i}}">
<b>Zone {{i+1}}</b> : <span id="z{{i}}">--</span>

<div class="bar">
<div id="bar{{i}}" class="fill"></div>
</div>

<a href="/zone/{{i}}/on">ON</a>
<a href="/zone/{{i}}/off">OFF</a>
</div>
{% endfor %}
</div>

<!-- CHART -->
<div class="card">
<h3>📊 ANALYTICS</h3>
<canvas id="chart"></canvas>
</div>

<script>
let chart;

function initChart(){
    chart = new Chart(document.getElementById("chart"),{
        type:'line',
        data:{
            labels:[],
            datasets:[
                {label:'Temp',data:[],borderColor:'#22c55e'},
                {label:'Soil',data:[],borderColor:'#facc15'},
                {label:'Water',data:[],borderColor:'#ef4444'}
            ]
        }
    });
}

function updateChart(d){
    let t = new Date().toLocaleTimeString();

    if(chart.data.labels.length > 15){
        chart.data.labels.shift();
        chart.data.datasets.forEach(ds => ds.data.shift());
    }

    chart.data.labels.push(t);
    chart.data.datasets[0].data.push(d.temp);
    chart.data.datasets[1].data.push(d.soil);
    chart.data.datasets[2].data.push(d.well);

    chart.update();
}

function alarm(risk){
    let a = document.getElementById("alarm");
    let s = document.getElementById("sound");

    if(risk >= 70){
        a.style.display="block";
        s.play().catch(()=>{});
    } else {
        a.style.display="none";
        s.pause();
        s.currentTime=0;
    }
}

async function fetchData(){
    const res = await fetch("/api/live");
    const d = await res.json();

    if(!d.active) return;

    document.getElementById("modeBox").innerText = d.mode;

    document.getElementById("temp").innerText = d.temp;
    document.getElementById("soil").innerText = d.soil;
    document.getElementById("well").innerText = d.well;

    // ZONES
    d.zones.forEach((z,i)=>{
        let label = document.getElementById("z"+i);
        let bar = document.getElementById("bar"+i);

        if(z){
            label.innerText = "ON 🟢";
            bar.style.width = "100%";
            document.querySelector(".zone"+i).classList.remove("dry-flash");
        }else{
            label.innerText = "DRY 🔴";
            bar.style.width = "20%";
            document.querySelector(".zone"+i).classList.add("dry-flash");
        }
    });

    let risk = 0;
    if(d.soil > 750) risk += 40;
    if(d.well < 25) risk += 40;
    if(d.temp > 38) risk += 20;

    updateChart(d);
    alarm(risk);
}

initChart();
fetchData();
setInterval(fetchData, 60000);
</script>

</body>
</html>
"""

# ================= API =================
@app.route("/api/live")
def api_live():
    global pump_state, zones, mode

    if not pump_state:
        return jsonify({"active": False, "mode": mode, "zones": zones})

    temp = random.randint(20,40)
    soil = random.randint(400,800)
    well = random.randint(10,100)

    # AUTO MODE
    if mode == "AUTO":
        zones[0] = soil < 700
        zones[1] = soil < 650
        zones[2] = soil < 600

    return jsonify({
        "active": True,
        "temp": temp,
        "soil": soil,
        "well": well,
        "zones": zones,
        "mode": mode
    })

# ================= AUTH =================
@app.route("/", methods=["GET","POST"])
def login():
    error=False
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        if u in USERS and USERS[u]==p:
            session["user"]=u
            return redirect("/dashboard")
        error=True
    return render_template_string(LOGIN_HTML,error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template_string(DASHBOARD_HTML, pump="ON" if pump_state else "OFF", mode=mode)

# ================= CONTROL =================
@app.route("/pump/on")
def pump_on():
    global pump_state
    pump_state=True
    return redirect("/dashboard")

@app.route("/pump/off")
def pump_off():
    global pump_state, zones
    pump_state=False
    zones=[False,False,False]
    return redirect("/dashboard")

@app.route("/zone/<int:z>/on")
def zone_on(z):
    zones[z]=True
    return redirect("/dashboard")

@app.route("/zone/<int:z>/off")
def zone_off(z):
    zones[z]=False
    return redirect("/dashboard")

@app.route("/mode/<m>")
def set_mode(m):
    global mode
    if m in ["AUTO","MANUAL"]:
        mode=m
    return redirect("/dashboard")

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
    
