from flask import Flask, render_template_string, request, redirect, url_for
import random

app = Flask(_name_)

# 🔐 بيانات الدخول
USERNAME = "smart soqya"
PASSWORD = "1234"

# ---------------- LOGIN PAGE ----------------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Smart Saqya</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        body{
            margin:0;
            font-family:Arial;
            background: linear-gradient(135deg,#0f172a,#1e293b);
            color:white;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
        }

        .box{
            background: rgba(255,255,255,0.08);
            padding:25px;
            border-radius:15px;
            width:85%;
            max-width:350px;
            text-align:center;
            backdrop-filter: blur(10px);
        }

        input{
            width:90%;
            padding:12px;
            margin:10px 0;
            border:none;
            border-radius:10px;
        }

        button{
            width:95%;
            padding:12px;
            border:none;
            border-radius:10px;
            background:#22c55e;
            color:white;
            font-size:16px;
        }

        .title{
            font-size:22px;
            margin-bottom:15px;
        }

        .error{
            color:#ef4444;
            margin-top:10px;
        }
    </style>
</head>
<body>
