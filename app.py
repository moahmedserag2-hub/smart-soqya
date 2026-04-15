from flask import Flask, jsonify, request

app = Flask(_name_)

system_state = {
    "pump": True,
    "mode": "AUTO",
    "zones": [True, True, True]
}

@app.route("/")
def home():
    return "Smart Saqya Running 🚀"

@app.route("/api/status")
def status():
    return jsonify(system_state)

@app.route("/api/command")
def command():
    action = request.args.get("action")

    if action == "pump":
        system_state["pump"] = request.args.get("value") == "1"

    elif action == "zone":
        z = int(request.args.get("z"))
        system_state["zones"][z] = not system_state["zones"][z]

    elif action == "mode":
        system_state["mode"] = request.args.get("value")

    return jsonify(system_state)

if _name_ == "_main_":
    app.run()
