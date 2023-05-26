
from flask import Flask,  render_template, request, redirect, url_for, session, flash, make_response
import mysql.connector
import logging
import openai
from gtts import gTTS
from datetime import datetime, timedelta

from flask import jsonify
import time
import speech_recognition as sr
import pyttsx3

import pygame
from io import BytesIO

from flask import jsonify
from pydub import AudioSegment
from pydub.playback import play
from audioplayer import AudioPlayer
from playsound import playsound

from pydub import AudioSegment
import sounddevice as sd
from scipy.io import wavfile

import os
import uuid

# coding=utf-8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar la API de OpenAI
openai.api_key = "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"

# Configurar la base de datos de MySQL
app = Flask(__name__)
app.debug = True
app.secret_key = 'miguelklariancontreras2510196110'


# Configurar el motor de texto a voz
engine = pyttsx3.init()

engine.setProperty('rate', 170)
engine.setProperty('volume', 2.0)  # Agregar esta línea para aumentar el volumen
r= sr.Recognizer()
mic = sr.Microphone(device_index=0)
#r.language = "es"
r.pause_threshold = 0.8
r.energy_threshold = 4000
r.dynamic_energy_threshold= False


app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gpt'

mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB'],
    port=3306
)

fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def text_to_speech(id, text,lang):
    filename = f'respuesta_{id}.wav'  # Agrega el ID de usuario al nombre del archivo
    filepath = os.path.join('static/audio', filename)

    tts = gTTS(text, lang=lang)
    tts.save(filepath)

  
    return filepath

def play_audio(filepath):
    audio = AudioSegment.from_mp3(filepath)
    audio.export('temp.wav', format='wav')
    fs, data = wavfile.read('temp.wav')
    sd.play(data, fs)
    sd.wait()


# Ruta para borrar la conversación actual
@app.route('/borrar-conversacion', methods=['POST'])
def borrar_conversacion():
    session.pop('conversations', None)
    return redirect(url_for('consulta'))



# Ruta para la página principal
@app.route('/')
def home():
    return render_template("contenido.html")

# Ruta para el cierre de sesión
@app.route("/salir")
def salir():
    session.clear()
    session.pop("logged_in", None)
    return render_template("contenido.html")
    

# Ruta para el formulario de registro
@app.route('/registro', methods=["GET", "POST"])
def registro():
    cur = mysql.cursor(dictionary=True)
    cur.execute("SELECT * FROM tip_usu")
    tipo = cur.fetchall()
    cur.close()
    
    cur = mysql.cursor(dictionary=True)
    cur.execute("SELECT * FROM idioma")
    idioma = cur.fetchall()
    cur.close()

    if request.method == 'GET':
        return render_template("registro.html", tipo = tipo, idioma = idioma )
    else:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        tip = request.form['tipo']
        idioma = request.form['idioma']

        cur = mysql.cursor()
        cur.execute("INSERT INTO users (name, email, password, id_tip_usu, idioma) VALUES (%s,%s,%s,%s,%s)", (name, email, password,tip,idioma,))
        mysql.commit()
        cur.close()

        return redirect(url_for('login'))
    
@app.route('/actualiza', methods=["GET", "POST"])
def actualiza():
    cur = mysql.cursor(dictionary=True)
    cur.execute("SELECT * FROM tip_usu")
    tipo = cur.fetchall()
    cur.close()
    
    cur = mysql.cursor(dictionary=True)
    cur.execute("SELECT * FROM idioma")
    idioma = cur.fetchall()
    cur.close()

    email = session['email']
    
    if request.method == 'GET':
        return render_template("actualiza.html", tipo = tipo, idioma = idioma )
    else:

        idioma = request.form['idioma']

        email = session['email']
 

        cur = mysql.cursor()
        cur.execute("UPDATE users SET idioma = %s WHERE email = %s", (idioma, email))
        print(consulta)
        mysql.commit()
        cur.close()
        session['idioma'] = idioma
        return redirect(url_for('consulta'))
    


@app.route('/login', methods= ["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        try:
            email = request.form['email']
        except KeyError:
            error = "No se ha ingresado un correo electrónico"
            return render_template("login.html", error=error)

        password = request.form['password']
        
        cur = mysql.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cur.fetchone()
        cur.close()

        if user and user['password'] == password:
            session['id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['tipo'] = user['id_tip_usu']
            session['idioma'] = user['idioma']
            session.pop('temp_var', None)
            return redirect(url_for("consulta"))
                       
        else:
            error = "Email o clave incorrecta"
            return render_template("login.html", error=error)          
    else:
        return render_template("login.html", error=error)


# Ruta para el chatbot

app.permanent_session_lifetime = timedelta(minutes=30)

conversations = []
chat = []


@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    id = session['id']
    fecha = datetime.now()
    data = []
    audio = None
    answer = None
    lang=""

    
    if session['idioma'] == 'Español':
            lang='es'
    if session['idioma'] == 'Ingles':
            lang='en'
    if session['idioma'] == 'Frances':
            lang='fr'
    
    def speak(text):
        
        if session['idioma'] == 'Español':
            lang='es'
        if session['idioma'] == 'Ingles':
            lang='en'
        if session['idioma'] == 'Frances':
            lang='fr'

        pygame.mixer.init()

        tts = gTTS(text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()

    
    if 'Borrar_conversacion' in request.form and request.form['Borrar_conversacion'] == 'true':
        cur = mysql.cursor(dictionary=True)
        print("Deleting conversation")
        cur.execute("DELETE FROM conversaciones WHERE email = %s", (email,))
        mysql.commit()
        cur.close()
        
        if not data:
            data = []
            return render_template('consulta.html', chat=data)
        else:   
            return render_template('consulta.html', chat=data)

    
    if 'Cargar_conversacion' in request.form and request.form['Cargar_conversacion'] == 'true':
        cur = mysql.cursor(dictionary=True)
        cur.execute("SELECT * FROM conversaciones WHERE email = %s ORDER BY id DESC", (email,))
        data = cur.fetchall()
        cur.close()
    
        if not data:
            data = []
            return render_template('consulta.html', chat=data)
        else:   
            return render_template('consulta.html', chat=data)
    
    if request.method == 'POST' and request.form['question']:
        
        if session['idioma'] == 'Español':
                lang='es'
        if session['idioma'] == 'Ingles':
                lang='en'
        if session['idioma'] == 'Frances':
                lang='fr'
                
      
        
        question = request.form['question']

        cur = mysql.cursor(dictionary=True)
        cur.execute("INSERT INTO conversaciones (email, text, speaker, created_at) VALUES (%s, %s, %s, %s)", (email, question, 'user', fecha))
        mysql.commit()
        cur.close()

        try:
            # Obtener la respuesta del chatbot utilizando OpenAI
            response = openai.Completion.create(
                engine='text-davinci-003',
                prompt=question,
                temperature=0.5,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            answer = response.choices[0].text

        except:
            answer = "Lo siento, no he podido entender la pregunta"
            
 
        cur = mysql.cursor(dictionary=True)
        cur.execute("INSERT INTO conversaciones (email, text, speaker, created_at) VALUES (%s, %s, %s, %s)", (email, answer, 'bot', fecha))
        mysql.commit()
        cur.close()
        
        
        audio_filepath = text_to_speech(id,answer,lang)
 
        play_audio(audio_filepath)
        
        
        #speak(answer)
        
        cur = mysql.cursor(dictionary=True)
        cur.execute("SELECT * FROM conversaciones WHERE email = %s ORDER BY id DESC", (email,))
        data = cur.fetchall()
        cur.close()
        
        answer=""   
        return jsonify({"status": "success", "message": "Consulta procesada", "answer": answer})
        
        return render_template('consulta.html', chat=data)
      
   
    if request.method == 'POST' and request.form.get('audio') == 'true':
        
        if session['idioma'] == 'Español':
            lang='es'
        if session['idioma'] == 'Ingles':
            lang='en'
        if session['idioma'] == 'Frances':
            lang='fr'
        
        print(lang)
        
        text = None # Inicializa la variable 'text'
        stop = False # Inicializa la variable 'stop' en False
        start_time = time.time() # Inicializa el temporizador
 
        while not stop:
      
            try:
            
                with mic as source:
                    
                                       
                    print(session['idioma'])
                    
                    
                    if session['idioma'] == 'Español':
                           
                            r.language = "es"
                            escucha = "escuchando... hable claro por el micrófono..."
                            speak(escucha) 
                            print("\nescuchando... hable claro por el micrófono...")
                    
                    if session['idioma'] == 'Ingles':
                           
                            r.language = "en"
                            escucha = "listening... speak clearly into the microphone..."
                            speak(escucha) 
                            print("\nlistening... speak clearly into the microphone...")
                        
                    if session['idioma'] == 'Frances':
                          
                            r.language = "fr"
                            escucha = "Écoute... Parlez clairement dans le microphone..."
                            speak(escucha)
                            print("\nlÉcoute... Parlez clairement dans le microphone...")
                                
                    r.adjust_for_ambient_noise(source, duration=1)
                    r.pause_threshold = 0.8
                    audio = r.listen(source, timeout=8)
                    print(audio)

                    
            except sr.WaitTimeoutError:
                    if session['idioma'] == 'Español':
                        speak("Se agotó el tiempo de espera para hablar")
                        text = None
                        stop = True
                    if session['idioma'] == 'Ingles':
                        speak("Timed out to talk")
                        text = None
                        stop = True
                    if session['idioma'] == 'Frances':
                        speak("Temps mort pour parler")
                        text = None
                        stop = True
                                    
            except OSError as e:
                speak("Ocurrió un error al acceder al micrófono:", e)
                text = None
                stop = True
            
            except sr.UnknownValueError:
                speak("Lo siento, no he podido entender lo que dijo. ¿Podría repetirlo, por favor?")
                text = None
                stop = True
               
            else:
                
                if text =="":
                    stop = True # Establece la variable "stop" en True para salir del ciclo while
                    break
                    
                
                text = r.recognize_google(audio, language=lang)

                print(text)
                start_time = time.time() # Reinicia el temporizador
                
           
            # Verificar que se ha obtenido texto antes de insertar en la tabla 'conversaciones'
                if text:
                    cur = mysql.cursor(dictionary=True)
                    cur.execute("INSERT INTO conversaciones (email, text, speaker, created_at) VALUES (%s, %s, %s, %s)", (email, text, 'user', fecha))
                    mysql.commit()
                    cur.close()

                try:
            # Obtener la respuesta del chatbot utilizando OpenAI
                    response = openai.Completion.create(
                    engine='text-davinci-003',
                    prompt=text,
                    temperature=0.5,
                    max_tokens=2048,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                    answer = response.choices[0].text
                except:
                    answer = "Lo siento, no he podido entender la pregunta"
                

                # Insertar la respuesta del chatbot en la tabla 'conversaciones'
                cur = mysql.cursor(dictionary=True)
                cur.execute("INSERT INTO conversaciones (email, text, speaker, created_at) VALUES (%s, %s, %s, %s)", (email, answer, 'bot', fecha))
                mysql.commit()
                cur.close()
                           
                print(time.time())
                print(start_time)
                print(time.time() - start_time)
                if time.time() - start_time > 12:
                    stop = True # Establece la variable "stop" en True para salir del ciclo while
                    break
           
                audio_filepath = text_to_speech(id,answer,lang)
 
                play_audio(audio_filepath)


                
                #speak(answer)
            
        return jsonify({"status": "success", "message": "Consulta procesada", "answer": answer})
    
    
    cur = mysql.cursor(dictionary=True)
    cur.execute("SELECT * FROM conversaciones WHERE email = %s ORDER BY id DESC", (email,))
    data = cur.fetchall()
    cur.close()
    
           
    if not data:
        data = []
        return render_template('consulta.html', chat=data)
    else:   
        return render_template('consulta.html', chat=data)


if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000)



