import sqlite3 # biblitoeca pentru baza de date
from collections import defaultdict # creeaza dictionare cu valori implicite
from datetime import datetime # lucrul cu date si ore
from flask import Flask, render_template, request, redirect, url_for, flash, session
# Flask - creeaza aplicatia web
# render_template - incarca fisiere html din folderul 'templates'
# request - acceseaza date trimise prin formulare
# redirect - redirectioneaza utilizatorul catre o alta pagina
# url_for - genereaza url-uri dinamice pentru functiile Flask
# flash - trimite mesaje catre utilizator
# session - pastreaza informatii despre utilizator pe parcursul sesiunii
import pandas as pd # lucrul cu date tabelare
import plotly.express as px # crearea graficelor interactive

app = Flask(__name__) # crearea unei instante a aplicatiei Flask
app.secret_key = 'abc123' # se seteaza cheia secreta pentru a putea folosi sesiuni
users = {"admin": "parola123"} # dictionar care stocheaza utilizatorul si parola

@app.before_request # functia se executa inainte de fiecare request
def verificare_autentificare():
    exceptii = ['login', 'static'] # lista cu numele endpointurilor care nu necesita autentificare
    if request.endpoint in exceptii:
        return

    if 'utilizator' not in session: # redirectioneaza catre pagina de login daca utilizatorul nu este autentificat
        return redirect(url_for('login'))

# ruta principala a aplicatiei (HOME)
@app.route('/')
def index():
        # preluarea campului si a ordinii de sortare specificata de utilizator
        # la accesare se face sortarea implicita (alfabetic dupa titlul cartii)
        camp = request.args.get('camp', 'carte')
        ordine = request.args.get('ordine', 'ASC')

        # coloanele pentru care aplicam sortari
        campuri_permise = ['carte', 'autor', 'pagini', 'data_citirii','raft', 'rating', 'anul_publicarii']
        # sortari
        ordine_permise = ['ASC', 'DESC']

        # verificarea valorilor
        if camp not in campuri_permise:
            camp = 'carte'
        if ordine not in ordine_permise:
            ordine = 'ASC'

        # query SQL care selecteaza datele din tabel si le ordoneaza dupa campul si ordinea specificata
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute(f'''
            SELECT carte, autor, pagini, data_citirii, raft, rating, anul_publicarii
            FROM biblioteca
            ORDER BY {camp} {ordine}
        ''')
        carti = c.fetchall()
        conn.close()

        # se returneaza sablonul HTML, trimitand lista de carti si optiunile de sortare
        return render_template('index.html', carti=carti, camp=camp, ordine=ordine)

# ruta pentru autentificare
@app.route('/login', methods=['GET', 'POST'])
def login():
    # se preiau date introduse in formular (username si parola)
    if request.method == 'POST':
        username = request.form['username']
        parola = request.form['password']
        # daca utilizatorul exista si parola este corecta, se salveaza datele in sesiune
        if username in users and users[username] == parola:
            session['utilizator'] = username
            # se trimite mesaj pentru confirmarea autentificarii
            flash("Autentificare reușită!")
            # se redirectioneaza catre pagina principala
            return redirect(url_for('index'))
        # daca datele sunt gresite, apare mesaj
        else:
            flash("Date incorecte. Încearcă din nou.")
    # daca metoda este GET sau autentificarea a esuat, se revine la formularul de login
    return render_template('login.html')

# ruta pentru delogare
@app.route('/logout')
def logout():
    session.pop('utilizator', None) # se sterge utilizatorul din sesiunie, daca exista
    flash("Ai fost delogat.") # mesaj de confirmare a delogarii
    return redirect(url_for('login')) # redirectionare catre login

# ruta pentru adaugarea unei carti in biblioteca
@app.route('/adaugare_carte', methods=['GET','POST'])
def adaugare_carte():
    # preluare datele trimise de utilizator in formular
    if request.method == 'POST':
        carte = request.form['carte']
        carte_autor = request.form['autorul cartii']
        carte_pagini = int(request.form['numarul de pagini al cartii'])
        # datele sunt introduse in format ZI-LUNA-AN, se face transformarea in format standard(AN-LUNA-ZI)
        carte_data = datetime.strptime(request.form['data citirii'], "%Y-%m-%d").strftime("%Y-%m-%d")
        carte_raft = request.form['genul cartii']
        carte_status = request.form['statusul cartii']
        carte_rating = int(request.form['rating-ul cartii'])

        # se creeaza tabela "biblioteca"
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS biblioteca(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carte TEXT,                             -- titlul cartii
            autor TEXT,                             -- autorul cartii
            pagini INTEGER,                         -- numarul de pagini al cartii
            data_citirii DATE,                      -- data la care a fost citita cartea
            raft TEXT,                              -- genul cartii
            status TEXT,                            -- cartea a fost citita
            rating INTEGER                          -- nota(rating-ul) dat cartii
        )''')
        # se introduc datele cartii in baza de date
        c.execute('INSERT INTO biblioteca (carte, autor, pagini, data_citirii, raft, status, rating) VALUES (?,?,?,?,?,?,?)',
                  (carte,carte_autor,carte_pagini,carte_data,carte_raft,carte_status,carte_rating))

        # mesaj de confirmare a adaugarii cartii
        flash(f'Cartea "{carte}" scrisă de {carte_autor} a fost adăugată în bibliotecă!')
        # salveaaza modificarile
        conn.commit()
        conn.close()

        # se obtine numele utiliatorului, o descriere a actiunii si se inregistreaza acestea in jurnal
        utilizator = session.get('utilizator', 'Anonim')
        descriere = f"Utilizatorul {utilizator} a adaugat cartea {carte} in biblioteca sa."
        adauga_jurnal(utilizator, 'adaugare carte', descriere)

        # redirectionare catre aceeasi pagina
        return redirect('/adaugare_carte')
    # daca metoda este GET, se afiseaza formularul de adaugare carte
    return render_template('adaugare_carte.html')

# ruta pentru stergerea unei carti din biblioteca
@app.route('/stergere_carte', methods=['GET','POST'])
def stergere_carte():
    id_carte = request.form.get('id_carte') # se preia id-ul cartii

    if id_carte:
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        # se executa comanda SQL pentru stergerea cartii cu id-ul prezentat
        c.execute('DELETE FROM biblioteca WHERE id=?', (id_carte,))
        conn.commit()
        conn.close()

    # se obtine numele utiliatorului, o descriere a actiunii si se inregistreaza acestea in jurnal
    utilizator = session.get('utilizator', 'Anonim')
    descriere = f"Utilizatorul {utilizator} a șters cartea {id_carte} din biblioteca sa."
    adauga_jurnal(utilizator, 'stergere carte', descriere)

    # redirectionare catre pagina de listare a cartilor
    return redirect(url_for('listare_carti'))

# ruta pentru editarea unei carti, identificata prin id-ul ei (ex: /editare_carte/1)
@app.route('/editare_carte/<int:id_carte>', methods=['GET', 'POST'])
def editare_carte(id_carte):
    # se preiau datele noi introduse de catre utilizator
    if request.method == 'POST':
        carte = request.form['carte']
        autor = request.form['autorul cartii']
        pagini = int(request.form['numarul de pagini al cartii'])
        data_citirii = datetime.strptime(request.form['data citirii'], "%Y-%m-%d").strftime("%Y-%m-%d")
        raft = request.form['genul cartii']
        status = request.form['statusul cartii']
        rating = int(request.form['rating-ul cartii'])

        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        # se actualizeaza inregistrarea din baza de date corespunzatore cartii cu id-ul ales
        c.execute('''
            UPDATE biblioteca
            SET carte=?, autor=?, pagini=?, data_citirii=?, raft=?, status=?, rating=?
            WHERE id=?
        ''', (carte, autor, pagini, data_citirii, raft, status, rating, id_carte))
        conn.commit()
        conn.close()

    # la accesarea paginii (GET), se selecteaza cartea din baza de date dupa id
    else:
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute('SELECT * FROM biblioteca WHERE id=?', (id_carte,))
        carte = c.fetchone()
        conn.close()

        # validare
        if not carte:
            return "Carte negăsită", 404

    # dictionar cu datele cartii pentru sablonul HTML
    carte_dict = {
            'id': carte[0],
            'carte': carte[1],
            'autor': carte[2],
            'pagini': carte[3],
            'data_citirii': carte[4],
            'raft': carte[5],
            'status': carte[6],
            'rating': carte[7]
        }

    # se obtine numele utiliatorului, o descriere a actiunii si se inregistreaza acestea in jurnal
    utilizator = session.get('utilizator', 'Anonim')
    descriere = f"Utilizatorul {utilizator} a editat cartea {carte} din biblioteca sa."
    adauga_jurnal(utilizator, 'editare carte', descriere)

    # se trimite sablonul HTML pentru editare, impreuna cu datele cartii
    return render_template('editare_carte.html', carte=carte_dict)

# ruta pentru filitrarea cartilor in functie de raft (genul cartii)
@app.route('/filtru_raft', methods=['GET','POST'])
def filtru_raft():
    carti1 = [] # lista rafturilor disponibile
    carti2 = [] # lista cartilor filtrate in functie de raftul ales

    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT DISTINCT raft FROM biblioteca') # se extrag doar valorile DISTINCTE ale coloanei raft
    carti1 = c.fetchall()
    if request.method == 'POST':
        raspuns3 = request.form['raspuns3'] # se preia valoarea transmisa de utilizator
        c.execute('SELECT carte, autor, pagini, data_citirii, raft, status, rating FROM biblioteca WHERE raft=?',
                  (raspuns3, )) # se extrag cartile care apartin raftului selectat
        carti2 = c.fetchall()
    conn.close()

    # se trimite catre sablonul HTML lista rafturilor (carti1) si cartile filtrate (carti2)
    return render_template('filtru_raft.html', carti1=carti1, carti2=carti2)

# ruta pentru afisarea tuturor cartilor din biblioteca
@app.route('/listare_carti', methods=['GET'])
def listare_carti():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT id, carte, autor, pagini, data_citirii, raft, status, rating, anul_publicarii FROM biblioteca '
              'ORDER BY data_citirii DESC') # se extrag cartile din tabel, sortate dupa data citirii
    carti_raw = c.fetchall()
    conn.close()

    # lista de dictionare cu datele fiecarei carti pentru sablonul HTML
    carti = []
    for carte in carti_raw:
        carti.append({
            'id': carte[0],
            'carte': carte[1],
            'autor': carte[2],
            'pagini': carte[3],
            'data_citirii': carte[4],
            'raft': carte[5],
            'status': carte[6],
            'rating': carte[7],
            'anul_publicarii': carte[8]
        })

    # se trimite lista de carti catre sablonul HTML
    return render_template('listare_carti.html', carti=carti)

# ruta pentru afisarea mediei rating-urilor tuturor cartilor din biblioteca
@app.route('/avg_rating', methods=['GET'])
def avg_rating():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT AVG(rating) FROM biblioteca') # comanda SQL pentru a calcula media coloanei rating
    medie_rating = c.fetchone()[0] # rezultatul este un tuplu, luam doar primul element (valoarea medie)
    conn.close()
    # se trimite valoarea catre sablonul HTML
    return render_template('avg_rating.html', medie_rating=medie_rating)

# ruta pentru afisarea mediei ratingului pe raft, cu posiblitate de filtrare a rafturilor printr-un formular
@app.route('/avg_rating_raft', methods=['GET', 'POST'])
def avg_rating_raft():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT DISTINCT raft FROM biblioteca') # preluam toate rafturile din tabelul biblioteca
    carti3 = c.fetchall()

    medie_rating_raft = None # media ratingului pentru raftul selectat
    carti14 = [] # lista cu cartile de pe raftul selectat

    if request.method == 'POST':
        raspuns4 = request.form['raspuns4']
        c.execute('SELECT carte, autor, pagini, raft, rating FROM biblioteca WHERE raft=?',
                  (raspuns4,)) # selectam cartile raftului prezentat de utilizator
        carti14 = c.fetchall()
        c.execute('SELECT AVG(rating) FROM biblioteca WHERE raft=?', (raspuns4,))
        medie_rating_raft = c.fetchone()[0] # calculam media cartilor selectate

    conn.close()

    # trimitem catre sablon variabilele pentru afisare
    return render_template(
        'avg_rating_raft.html',
        carti3=carti3,
        carti14=carti14,
        medie_rating_raft=medie_rating_raft
    )

# ruta pentru afisarea mediei rating-ului pe autor, cu posibilitate de filtrare prin formular
@app.route('/avg_rating_autor', methods=['GET', 'POST'])
def avg_rating_autor():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT DISTINCT autor FROM biblioteca') # preluam lista autorilor distincti din baza de date
    autori = c.fetchall()

    medie_rating_autor = None # media rating-ului pentru autorul selectat
    carti_autor = [] # lista cartilor autorului selectat

    if request.method == 'POST':
        raspuns5 = request.form['raspuns5'] # preluam autorul selectat de catre utilizator
        c.execute('SELECT * FROM biblioteca WHERE autor=?', (raspuns5,)) # selectam cartile autorului
        carti_autor = c.fetchall()
        c.execute('SELECT AVG(rating) FROM biblioteca WHERE autor=?', (raspuns5,)) # calculam media rating-urilor
        medie_rating_autor = c.fetchone()[0]

    conn.close()

    # trimitem datele catre sablon
    return render_template(
        'avg_rating_autor.html',
        autori=autori,
        carti_autor=carti_autor,
        medie_rating_autor=medie_rating_autor
    )

# ruta pentru calcularea numarului de pagini citite intr-un interval de timp
@app.route('/pagini_luna', methods=['GET'])
def pagini_luna():
    # preluam datele de la utilizator: inceputul intervalului si sfarsitul intervalului
    start_luna = request.args.get('start_luna')
    sfarsit_luna = request.args.get('sfarsit_luna')

    # verificarea datelor
    if not start_luna or not sfarsit_luna:
        return render_template('pagini_luna.html', mesaj="te rog introdu date")

    try:
        # convertim datele introduse din formatul ZI-LUNA-AN in formatul AN-LUNA-ZI pentru SQL
        start_sql = datetime.strptime(start_luna,'%d/%m/%y').strftime('%Y-%m-%d')
        sfarsit_sql = datetime.strptime(sfarsit_luna,'%d/%m/%y').strftime('%Y-%m-%d')
    except ValueError:
        # mesaj de eroare pentru format introdus gresit
        return render_template('pagini_luna.html', mesaj="format incorect")


    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()

    c.execute('SELECT SUM(pagini) FROM biblioteca WHERE data_citirii BETWEEN ? AND ?',
              (start_sql, sfarsit_sql)) # calculam suma totala de pagini citite intre cele doua date
    total_pagini = c.fetchone()[0]

    c.execute('SELECT carte, autor, pagini, raft, rating FROM biblioteca WHERE data_citirii BETWEEN ? AND ?',
              (start_sql, sfarsit_sql)) # preluam cartile citite in intrevalul furnizat
    carti12 = c.fetchall()

    # daca s-au citit carti in acel interval:
    if total_pagini:
        mesaj = f"Numar de pagini intre {start_luna} si {sfarsit_luna} este {total_pagini}"
    # daca NU s-au citit carti in acel interval:
    else:
        mesaj = "Nu ai citit in aceasta perioada"
    conn.close()

    # returnam pagina HTML cu mesajul si cartile citite in acel interval
    return render_template('pagini_luna.html', mesaj=mesaj,carti12=carti12)

# ruta care afiseaza numarul de carti citite intr-un interval dat
@app.route('/carti_luna', methods=['GET'])
def carti_luna():
    # preluam datele de la utilizator: inceputul intervalului si sfarsitul intervalului
    start_luna = request.args.get('start_luna')
    sfarsit_luna = request.args.get('sfarsit_luna')

    # verificarea datelor
    if not start_luna or not sfarsit_luna:
        return render_template('carti_luna.html', mesaj="te rog introdu date")

    try:
        # convertim datele introduse din formatul ZI-LUNA-AN in formatul AN-LUNA-ZI pentru SQL
        start_sql = datetime.strptime(start_luna, '%d/%m/%y').strftime('%Y-%m-%d')
        sfarsit_sql = datetime.strptime(sfarsit_luna, '%d/%m/%y').strftime('%Y-%m-%d')
    except ValueError:
        # mesaj de eroare pentru format introdus gresit
        return render_template('carti_luna.html', mesaj="format incorect")

    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()

    # interogam baza de date pentru a afla cate carti au fost citite in intervalul furnizat
    c.execute('SELECT COUNT(*) FROM biblioteca WHERE data_citirii BETWEEN ? AND ?',(start_sql, sfarsit_sql))
    numar_carti_luna = c.fetchone()[0]

    # rezultatul interogarii
    mesaj = f"Numarul de carti citite in intervalul {start_luna} - {sfarsit_luna} este {numar_carti_luna}."

    # obtinem lista cu cartile citite in acel interval
    c.execute('SELECT carte, autor, pagini, raft, rating FROM biblioteca WHERE data_citirii BETWEEN ? AND ?',
              (start_sql, sfarsit_sql))
    carti13 = c.fetchall()
    conn.close()

    # returnam pagina HTML cu mesajul si lista cartilor din intervalul specificat
    return render_template('carti_luna.html', mesaj=mesaj, carti13=carti13)

# ruta pentru afisarea unei histograme cu numarul de carti citite in fiecare luna din anul 2025
@app.route('/histograma_carti_luna', methods=['GET'])
def histograma_carti_luna():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()

    c.execute('SELECT data_citirii FROM biblioteca') # obtinem datele de citire ale cartilor
    randuri_cu_dati = c.fetchall()
    conn.close()

    luni = [] # lista care salveaza lunile ca numere pentru anul 2025
    for (data_str,) in randuri_cu_dati:
        try:
            data = datetime.strptime(data_str, "%Y-%m-%d") # convertire string (ZI-LUNA-AN) in AN-LUNA-ZI
            if data.year == 2025: # pastram doar lunile din anul 2025
                luni.append(data.month)
        except Exception as e:
            # validare date
            print(f"Data invalidă: {data_str} - {e}")

    df = pd.DataFrame(luni, columns=['luna']) # transformam lista de luni intr-un DataFrame Pandas

    counts = df['luna'].value_counts().sort_index() # numaram cate carti au fost citite in fiecare luna

    # lista cu luni pentru grafic
    luni_nume = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
                 "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

    # cream un DataFrame pentru histograma, cu luna si numarul de carti
    df_hist = pd.DataFrame({
        'Luna': [luni_nume[i-1] for i in counts.index], # convertim indexul (1-12) in nume de luna
        'Nr_carti': counts.values # valorile sunt numarul de carti pe luna
    })

    # ne asiguram ca toate lunile sunt prezente in grafic (inclusiv cele cu 0 carti)
    toate_lunile = pd.DataFrame({'Luna': luni_nume, 'index': range(1,13)})
    # facem merge intre toate_lunile si cele existente, completand lipsurile cu 0
    df_hist = pd.merge(toate_lunile, df_hist, on='Luna', how='left').fillna(0).sort_values('index')

    # cream histograma cu Plotly
    fig = px.bar(df_hist, x='Luna',
                 y='Nr_carti',
                 title='Număr cărți citite pe lună în anul 2025',
                 labels={'Luna': 'Luna', 'Nr_carti': 'Număr cărți'},
                 text='Nr_carti') # afisam nr de carti direct pe bara

    # formatarea graficului
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside') # afisare text deasupra barelor
    fig.update_layout(yaxis=dict(dtick=1)) # axa Y: trepte de 1

    # convertim graficul in HTML
    graph_html = fig.to_html(full_html=False)

    # trimitem graficul catre sablonul HTML care il va afisa in browser
    return render_template('histograma_carti_luna.html', graph_html=graph_html)

# ruta pentru afisarea unei histograme cu numarul total de pagini citite in fiecare luna
@app.route('/histograma_pagini_luna', methods=['GET'])
def histograma_pagini_luna():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT data_citirii, pagini FROM biblioteca') # selectam coloanele de interes pentru grafic
    date = c.fetchall()
    conn.close()

    # acest dictionar va retine totalul paginilor per luna, initializeaza automat valorila 0 pentru fiecare cheie noua
    nr_pagini = defaultdict(int)

    # pentru fiecare tuplu din "date" se valideaza formatul datelor introduse in coloana "data_citirii"
    for data_str, pagini in date:
        try:
            data = datetime.strptime(data_str, "%Y-%m-%d")
        except ValueError:
            try:
                data = datetime.strptime(data_str, "%d/%m/%y")
            except ValueError:
                print(f"Data invalidă în baza de date: {data_str}")
                continue

        luna = data.strftime("%Y/%m") # extragem anul si luna din data citita in format AN-LUNA
        nr_pagini[luna] += pagini # adaugam numarul de pagini la totalul lunii respective

    # convertim dictionarul intr-un DataFrame Pandas cu doua coloane: luna si nr_pagini
    df = pd.DataFrame({
        'luna': list(nr_pagini.keys()),
        'nr_pagini': list(nr_pagini.values())
    })

    df = df.sort_values('luna') # sortam datele dupa luna pentru afisare cronologica

    # cream graficul folosind Plotly Express
    fig = px.bar(df, x='luna',
                 y='nr_pagini',
                 labels={'luna': 'Luna', 'nr_pagini': 'Nr. pagini'},
                 title='Număr pagini pe lună')

    # convertim graficul in HTML
    graph_html = fig.to_html(full_html=False)

    # trimitem sablonul HTML pentru afisare in browser
    return render_template('histograma_pagini_luna.html', graph_html=graph_html)

# ruta pentru adaugarea anului publicarii unei carti
@app.route('/anul_publicarii', methods=['GET', 'POST'])
def anul_publicarii():
    mesaj = None # variabila pentru mesajul afisat utilizatorului

    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()

    # selecteaza toate cartile din baza de date
    c.execute('SELECT carte FROM biblioteca')
    carti = c.fetchall()

    if request.method == 'POST': # verifica daca formularul a fost trimis de utilizator
        carte = request.form['carte'] # preia cartea selectata din formular
        anul = int(request.form['anul']) # preia anul introdus
        c.execute('SELECT COUNT(*) FROM biblioteca WHERE carte=?', (carte,))
        rezultat = c.fetchone()[0]

        # actualizeaza anul publicarii pentru cartea selectata si ofera un mesaj de confirmare
        if rezultat:
            c.execute('UPDATE biblioteca SET anul_publicarii=? WHERE carte=?', (anul,carte))
            mesaj = f'Anul publicarii cartii {carte} a fost actualizat, acesta fiind {anul}'

    # obtinem lista actualizata a cartilor si a anilor de publicare
    c.execute('SELECT carte, anul_publicarii FROM biblioteca')
    carti_actualizate = c.fetchall()
    conn.commit()
    conn.close()

    # trimitem datele catre sablonul HTML pentru afisare
    return render_template('/anul_publicarii.html',
                           mesaj=mesaj, # mesajul de confirmare
                           carti=carti, # lista de carti pentru formular
                           carti_actualizate=carti_actualizate) # lista de carti cu anul publicarii actualizat

# creeaza tabela "jurnal"
def tabela_jurnal():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jurnal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,     -- id pentru fiecare intrare
        timestamp TEXT DEFAULT (datetime('now')), -- timpul actiunii
        utilizator TEXT,                          -- numele utilizatorului care face actiunea  
        actiune TEXT,                             -- tipul actiunii
        descriere TEXT                            -- descrierea actiunii
    )
    ''')

    conn.commit()
    conn.close()

# functie pentru adaugarea unei intrari noi in jurnal
def adauga_jurnal(utilizator, actiune, descriere):
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO jurnal (utilizator, actiune, descriere) VALUES (?, ?, ?)',
        (utilizator, actiune, descriere) # comanda SQL care executa inserarea unei noi inregistrari in tabela
    )
    conn.commit()
    conn.close()

# ruta pentru afisarea tuturor intrarilor in jurnal
@app.route('/jurnal')
def jurnal():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()
    # selecteaza toate inregistrarile din jurnal, ordonate crescator dupa timp
    cursor.execute('SELECT timestamp, utilizator, actiune, descriere FROM jurnal ORDER BY timestamp DESC')
    intrari = cursor.fetchall()
    conn.close()

    # trimite lista de inregistrari catre sablonul HTML
    return render_template('jurnal.html', intrari=intrari)

# ruta pentru adaugarea cartilor in TBR (carti planificate)
@app.route('/aduagare_carte_planificata', methods=['GET','POST'])
def adaugare_carte_planificata():
    # verificam daca formularul a fost trimis si se preiau datele introduse
    if request.method == 'POST':
        carte = request.form['carte']
        carte_autor = request.form['autorul cartii']
        carte_pagini = int(request.form['numarul de pagini al cartii'])
        carte_raft = request.form['genul cartii']
        carte_status = "Carte planificată(în TBR)"

        # crearea tabelului nou "tbr"
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS tbr(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carte TEXT,
            autor TEXT,
            pagini INTEGER,
            raft TEXT,
            status TEXT            
        )''')

        # inserarea cartii in tabel
        c.execute(
            'INSERT INTO tbr (carte, autor, pagini, raft, status) VALUES (?,?,?,?,?)',
            (carte, carte_autor, carte_pagini, carte_raft, carte_status))
        flash(f'Cartea "{carte}" scrisă de {carte_autor} a fost adăugată la TBR!') # mesaj de confirmare
        conn.commit()
        conn.close()

        # se obtine numele utiliatorului, o descriere a actiunii si se inregistreaza acestea in jurnal
        utilizator = session.get('utilizator', 'Anonim')
        descriere = f"Utilizatorul {utilizator} a adaugat cartea {carte} la TBR."
        adauga_jurnal(utilizator, 'adaugare carte la TBR', descriere)

    # se incarca pagina cu formularul de adaugare
    return render_template('adaugare_carte_planificata.html')

# ruta pentru afisarea cartilor din TBR (carti planificate)
@app.route('/listare_carti_tbr', methods=['GET'])
def listare_carti_tbr():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()

    # se selecteaza cartile din tabela "tbr"
    c.execute('SELECT id, carte, autor, pagini, raft FROM tbr')
    carti_raw = c.fetchall()
    conn.close()

    # dictionar pentru HTML
    carti = []
    for carte in carti_raw:
        carti.append({
            'id': carte[0],
            'carte': carte[1],
            'autor': carte[2],
            'pagini': carte[3],
            'raft': carte[4]
        })

    # trimitem lista de carti catre sablonul HTML
    return render_template('listare_carti_tbr.html', carti=carti)

# ruta pentru transferarea cartilor din TBR in lista cartilor citite
@app.route('/din_tbr_in_citita/<int:id_carte>', methods=['GET','POST'])
def din_tbr_in_citita(id_carte):
    if request.method == 'GET':
        # se preiau cartile din tabela "tbr" impreuna cu datele despre acestea
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute('SELECT carte, autor, pagini, raft from tbr WHERE id=?', (id_carte,))
        carte = c.fetchone()
        conn.close()

        # se trimit datele catre sablonul HTML pentru afisarea formularului
        return render_template('din_tbr_in_citita.html',
                               carte=carte,
                               id_carte=id_carte)

    # se verifica trimiterea formularului de catre utilizator (selectarea unei carti tinta)
    elif request.method == 'POST':
        conn = sqlite3.connect("biblioteca.db")
        c = conn.cursor()
        c.execute('SELECT carte, autor, pagini, raft FROM tbr WHERE id=?', (id_carte,))
        carte = c.fetchone()


        carte_status = 'Citit' # statusul nou, implicit al cartii
        # se face conversia pentru data citirii, utiliatorul completand in formular data la care a fost citita cartea
        carte_data = datetime.strptime(request.form['data citirii'], "%Y-%m-%d").strftime("%Y-%m-%d")
        rating = int(request.form['rating-ul cartii']) # utilizatorul introduce un rating pentru carte

        # se insereaza toate datele noi, impreuna cu cele vechi din tabela "tbr" in tabela "biblioteca"
        c.execute('INSERT INTO biblioteca (carte, autor, pagini, raft, status, data_citirii, rating) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (carte[0], carte[1], carte[2], carte[3], carte_status, carte_data, rating))
        # se sterge cartea din TBR, deoarece a fost citita
        c.execute('DELETE FROM tbr WHERE id = ?', (id_carte,))
        conn.commit()
        conn.close()

        # se obtine numele utiliatorului, o descriere a actiunii si se inregistreaza acestea in jurnal
        utilizator = session.get('utilizator', 'Anonim')
        descriere = f"Utilizatorul {utilizator} a terminat de citit {carte}."
        adauga_jurnal(utilizator, 'carte din TBR citita', descriere)

        # redirectioneaza utilizatorul inapoi la lista cartilor din TBR
        return redirect(url_for('listare_carti_tbr'))

# ruta pentru afisarea unui grafic ce contine titlul cartilor citite si anul in care acestea au fost publicate
@app.route('/histograma_anul_publicarii', methods=['GET','POST'])
def histograma_anul_publicarii():
    conn = sqlite3.connect("biblioteca.db")
    c = conn.cursor()
    c.execute('SELECT carte, anul_publicarii FROM biblioteca') # selectam titlul cartii si anul publicarii din tabela
    publicare = c.fetchall()
    conn.close()

    # creeaza un DataFrame Pandas cu coloanele "carte" si "anul publicarii"
    df = pd.DataFrame(publicare, columns=['carte', 'anul_publicarii'])
    df = df.dropna() # elimina inregistrarile care au valori lipsa(NaN) pentru anul publicarii

    # creeaza o diagrama scatter(puncte) cu Plotly Express
    fig = px.scatter(df, x='carte', # titlul cartii este afisat pe axa X
                     y='anul_publicarii', # anul publicarii este afisat pe axa Y
                     hover_name='carte', # la trecerea cu mouse-ul se afiseaza titlul cartii
                     title='Titlul cărții vs. Anul publicării', # titlul graficului
                     labels={'carte': 'Titlul cărții', 'anul_publicarii': 'Anul publicării'}) # etichete pentru axe

    # Ajustari pentru dimensiunea graficului
    fig.update_layout(
        width=750,
        height=750,
        xaxis=dict(showticklabels=False) # ascunde etichetele cartilor pentru claritate
    )

    graph_html = fig.to_html(full_html=False) # converteste figura Plotly in HTML

    # trimitem HTML-ul graficului catre sablonul de afisare
    return render_template('histograma_anul_publicarii.html', graph_html=graph_html)

if __name__ == '__main__': # se verifica daca fisierul este rulat direct
    tabela_jurnal() # se apeleaza functia care creeaza tabela "jurnal" in baza de date daca nu exista deja
    app.run(debug=True) # se porneste serverul Flask, permite afisarea erorilor direct in browser