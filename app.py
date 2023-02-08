from flask import Flask,  render_template, request, redirect, url_for, session, flash # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from os import path #pip install notify-py
from notifypy import Notify
import openai
from flask_cors import CORS

openai.api_key = "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"


app = Flask(__name__)
app.debug = True

app.config['MYSQL_HOST'] = '51.222.240.18'
app.config['MYSQL_USER'] = 'futurodc_robot'
app.config['MYSQL_PASSWORD'] = 'Maklarian2510'
app.config['MYSQL_DB'] = 'futurodc_gpt'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template("contenido.html")    

@app.route('/layout', methods = ["GET", "POST"])
def layout():
    session.clear()
    return render_template("contenido.html")


@app.route('/login', methods= ["GET", "POST"])
def login():

    notificacion = Notify()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cur.fetchone()
        
        if user:
            if user is not None and user['password'] == password:
                
                session['name'] = user['name']
                session['email'] = user['email']
                session['tipo'] = user['id_tip_usu']
                
                return render_template("consulta.html")
                # Iniciar sesión del usuario
            else:
                error = "Email o clave incorrecta"
                return render_template("login.html", error=error)
                
              
                
        else:
                error = "Email o clave incorrecta"
                return render_template("login.html", error=error)

        cur.close()
        
        
    else:
        
        return render_template("login.html")



@app.route('/registro', methods = ["GET", "POST"])
def registro():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tip_usu")
    tipo = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sexo_interes")
    interes = cur.fetchall()

    cur.close()

    notificacion = Notify()
    
    

    if request.method == 'GET':
        return render_template("registro.html", tipo = tipo, interes = interes )
    
    else:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        tip = request.form['tipo']
        interes = request.form['interes']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password, id_tip_usu, interes) VALUES (%s,%s,%s,%s,%s)", (name, email, password,tip,interes,))
        mysql.connection.commit()
        notificacion.title = "Registro Exitoso"
        notificacion.message="ya te encuentras registrado en 🤵 CHAT ROBOT 👰, por favor inicia sesión y empieza a descubrir este nuevo mundo."
        notificacion.send()
        return redirect(url_for('login'))
    

conversations = []

@app.route('/consulta', methods=["GET", "POST"])

def consulta():
    
    if request.method == 'GET':
        return render_template('consulta.html')
    if request.form['question']:
        question = 'Yo: ' + request.form['question']

        response = openai.Completion.create(
            engine = 'text-davinci-003',
            prompt = question,
            temperature = 0.5,
            max_tokens = 1000,
            top_p = 1,
            frequency_penalty = 0,
            presence_penalty = 0.6
        )

        answer = 'AI: ' + response.choices[0].text.strip()

        conversations.append(question)
        conversations.append(answer)

        return render_template('consulta.html', chat = conversations)
    else:
        return render_template('consulta.html')


@app.route("/salir")

def salir():
    session.pop("logged_in", None)
    return redirect(url_for("layout"))

if __name__ == '__main__':
    app.secret_key = "pinchellave"
    app.run(debug=True)