from ast import Bytes
from dataclasses import dataclass
from email import message
from fileinput import filename
import imp
from io import BytesIO
from multiprocessing.dummy import Process
from sqlite3 import Cursor
from tkinter import Image
from flask_mysqldb import MySQL,MySQLdb
import MySQLdb.cursors
import re
import os
import imghdr
from flask import Flask, flash, render_template, request, redirect, url_for, abort, \
    jsonify,session
from matplotlib import image
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import asyncio
import base64
import re
import json


app = Flask(__name__)
#Cambie esto a su clave secreta (puede ser cualquier cosa, es para protección adicional)
app.secret_key = str(os.urandom(12))
# Ingrese los detalles de conexión de su base de datos a continuación
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'FE123'
app.config['MYSQL_DB'] = 'pythonlogin'
# Inicializar MySQL
mysql = MySQL(app)
#Configuracion para la carga de archivo
# UPLOAD_FOLDER = ('/tmp')
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])



@app.route('/',methods=["POST","GET"])
def index():
    return redirect('/pythonlogin/')

@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Mensaje de salida si algo sale mal...
    msg = ''
    # Compruebe si existen solicitudes POST de "nombre de usuario" y "contraseña" (formulario enviado por el usuario)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Crear variables para facilitar el acceso
        username = request.form['username']
        password = request.form['password']
        # Comprobar si existe una cuenta usando MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Obtener un registro y devolver el resultado
        account = cursor.fetchone()
        # Si la cuenta existe en la tabla de cuentas en la base de datos
        if account:
            # Crear datos de sesión, podemos acceder a estos datos en otras rutas
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirigir a la página de inicio
            return redirect(url_for('home'))
        else:
            # La cuenta no existe o el nombre de usuario/contraseña es incorrecto
            msg = 'Incorrect username/password!'
    # Mostrar el formulario de inicio de sesión con el mensaje (si corresponde)
    return render_template('index.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    #Eliminar datos de sesión, esto cerrará la sesión del usuario
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirigir a la página de inicio de sesión
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    #Mensaje de salida si algo sale mal...
    msg = ''
    # Compruebe si existen solicitudes POST de "nombre de usuario", "contraseña" y "correo electrónico" (formulario enviado por el usuario)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Crear variables para facilitar el acceso
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Mostrar formulario de registro con mensaje (si lo hay)
        # Comprobar si existe una cuenta usando MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # Si la cuenta existe, muestra los controles de error y validación.
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # La cuenta no existe y los datos del formulario son válidos, ahora inserte una nueva cuenta en la tabla de cuentas
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'Se ha registrado exitosamente!'
    elif request.method == 'POST':
        # El formulario está vacío... (sin datos POST)
        msg = '¡Por favor rellena el formulario!!'

    return render_template('register.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Comprobar si el usuario ha iniciado sesión
    if 'loggedin' in session:
        # El usuario ha iniciado sesión mostrarles la página de inicio
        return render_template('home.html', username=session['username'])
    # El usuario no ha iniciado sesión redirigir a la página de inicio de sesión
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Comprobar si el usuario ha iniciado sesión
    if 'loggedin' in session:
        # Necesitamos toda la información de la cuenta del usuario para poder mostrarla en la página de perfil.
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        #Mostrar la página de perfil con información de la cuenta
        return render_template('profile.html',account=account)

    #El usuario no ha iniciado sesión redirigir a la página de inicio de sesión
    return redirect(url_for('login'))

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/pythonlogin/profile/upload/<iduser>', methods=['POST',"GET"])
async def upload_files(iduser):
    if request.method =='POST':
        file = request.files['file']
        files= request.files.getlist('files[]')
        print(files)
        idU= int(iduser)
        print("Si ejecuto upload_file")
        # creando una tarea para crear Hilo()
        tarea = asyncio.create_task(creandoHilo(file,idU))
        await tarea
        return redirect('/pythonlogin/profile')


async def creandoHilo(file,idU):
    hilo_1 = threading.Thread(target=ejecutandoHilo,kwargs={'file':file,'idU':idU,})
    hilo_1.start()
    hilo_1.join()

def ejecutandoHilo(file,idU):
    print('Hola ejecutando desde el hilo')
    print('id: ', idU)

    now = datetime.now()
    files_names=[0]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        files_names.append(filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image = file.read()
        image_64_encode= base64.encodestring(image)
        with app.app_context():
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO images (imagen,nombre_img, fecha_creacion,idusuario) VALUES (%s,%s, %s,%s)",(image_64_encode,filename, now,idU))
            mysql.connection.commit()
            cur.close()
            print('File successfully uploaded ' + file.filename + ' to the database!')

    else:
        print('Invalid Uplaod only txt, pdf, png, jpg, jpeg, gif')

    print(files_names)
    print(len(filename))

    # msg = 'Success Uplaod'
    # return jsonify(msg)



@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/pythonlogin/gallery', methods=['POST',"GET"])
def gallery():
    if request.method == 'POST':
        if 'loggedin' in session:
            # Necesitamos toda la información de la cuenta del usuario para poder mostrarla en la página de perfil.
            # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
            # account = cursor.fetchone()
            file_names = []
            idUser= int(session['id'])
            print("idUser---> ",idUser)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT nombre_img FROM images  WHERE idusuario = %s', (idUser,))
            nombresimg = cursor.fetchall()

            for row in cursor:
                file_names.append("{nombre_img}".format(nombre_img=row['nombre_img']))

            print(file_names)


            return render_template('gallery.html',filenames=file_names)
    return render_template('gallery.html')
    # return render_template('gallery.html')