<p align="center">
  <a href="" rel="noopener">
    <img width=200px0px src="static/GrütteChat.png" alt="GrütteChat logo">
  </a>
</p>

<h3 align="center">GrütteChat</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> Python web chat app with an AI chat bot using Flask, Django, AJAX, SQL
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [ToDo](#todo)
- [Authors](#authors)
- [Screenshots](#screenshots)

## 🧐 About <a name = "about"></a>

GrütteChat is a web chat app. Messages are saved in a SQL database. New messages are fetched from the database using AJAX. Messages as well as user passwords are encrypted using the Python cryptography library. But the key is stored on the same machine as the database so thats not really secure. To make the chat more interesting, an AI chat bot is included. The chat bot is built using the openAI GPT-3.5 API. A special bot personality can be used if the signed in GrütteChat user has bought an upgraded version of GrütteChat - GrütteChat PLUS. Currently the PayPal sandbox API is used to process the purchase (so not a real purchase).

## 🚀 ToDo <a name = "todo"></a>
- Use Flasks socketio to update the chat in real time
- Better encryption
- CSS needs some work

## ✍️ Authors <a name = "authors"></a>
- [@jan](https://github.com/xelemir) - Development and design
- [@sophia](https://tiktok.com/@sophiaxkn) - Initial idea and name inspiration

## 🎉 Screenshots <a name = "screenshots"></a>
<br>
<p align="center">
<img width=100% src="static/ad.png" alt="GrütteChat ad"><br>
An ad for GrütteChat.<br><br>
</p>
<br>
<p align="center">
  <img width=200px src="static/img1.png" alt="GrütteChat" style="padding:10px;">
  <img width=200px src="static/img2.png" alt="GrütteChat" style="padding:10px;">
  <img width=200px src="static/img3.png" alt="GrütteChat" style="padding:10px;"><
  <br> The login page, MyAI chat bot with the pirate personality (with dark mode) and chat layout on mobile.<br><br>
</p>
<p align="center">
  <img width=100% src="static/img5.png" alt="GrütteChat">
  <br> The chat on desktop.<br><br>
</p>
<p align="center">
  <img width=100% src="static/img4.png" alt="GrütteChat">
  <br> The login page on desktop.
</p>