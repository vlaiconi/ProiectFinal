		  📚 Jurnalul Meu de Lectură
    
  Jurnalul Meu de Lectură este o aplicație web care permite gestionarea cărților citite și planificate (TBR - To Be Read), vizualizarea statisticilor de lectură și urmărirea activității printr-un jurnal automat. Este ideală pentru cititorii care doresc să-și organizeze lecturile într-un mod eficient, interactiv și vizual.


  Funcționalități principale

•	Autentificare cu sesiune (admin)

•	Adăugare, editare și ștergere cărți

•	Filtrare cărți după gen (raft)

•	Căutare cărți citite într-un interval de timp

  o	Numar de pagini citite

  o	Număr de cărți citite

•	Statistici:

  o	Rating mediu general
  
  o	Rating mediu în funcție de autor
  
  o	Rating mediu în funcție de gen
  
  o	Histogramă: cărți citite pe lună
  
  o	Histogramă: pagini citite pe lună
  
  o	Diagramă: anul publicării cărților citite
  
•	Gestionare TBR (cărți planificate pentru citit)

•	Istoric al acțiunilor (jurnal)


Tehnologii utilizate

•	Python — limbajul principal

•	Flask — framework web

•	SQLite3 — bază de date locală

•	Pandas — procesare și analiză date

•	Plotly — generare de grafice interactive

•	HTML/CSS (cu Jinja2) — interfață web

•	Bootstrap — stilizare și layout responsive


Structura aplicației (rute Flask)

Rută	Metode	Descriere

/	GET	Pagina principală cu listarea cărților

/login	GET, POST	Autentificare utilizator (admin)

/logout	GET	Delogare

/adaugare_carte	GET, POST	Adăugare carte în bibliotecă

/editare_carte/<int:id>	GET, POST	Editarea unei cărți existente

/stergere_carte	GET, POST	Ștergerea unei cărți

/filtru_raft	GET, POST	Filtrare cărți după gen

/listare_carti	GET	Listarea tuturor cărților cu informații complete

/avg_rating	GET	Afișare rating mediu general

/avg_rating_raft	GET, POST	Afișare rating mediu pe un gen

/avg_rating_autor	GET, POST	Afișare rating mediu pentru un autor

/pagini_luna	GET	Pagini citite într-un interval

/carti_luna	GET	Cărți citite într-un interval

/histograma_carti_luna	GET	Histogramă: număr de cărți citite pe lună (2025)

/histograma_pagini_luna	GET	Histogramă: număr total pagini pe lună

/histograma_anul_publicarii	GET	Diagramă: anii de publicare ai cărților citite

/anul_publicarii	GET, POST	Setare/actualizare an publicare pentru o carte

/jurnal	GET	Vizualizare jurnal al acțiunilor utilizatorului

/aduagare_carte_planificata	GET, POST	Adăugare carte în lista TBR

/listare_carti_tbr	GET	Listare cărți planificate (TBR)

/din_tbr_in_citita/<id>	GET, POST	Mutare carte din TBR în lista de cărți citite


Observații

•	Aplicația rulează local în browser: http://127.0.0.1:5000/

•	Pentru rulare, trebuie să instalezi manual dependențele necesare (Flask, pandas, Plotly). Exemplu:

pip install Flask pandas plotly

•	Autentificarea este simplă (fără baze de date de utilizatori):

o	Username: admin

o	Parolă: parola123

•	Pentru a adăuga o nouă coloană (anul_publicarii) în tabela biblioteca, s-a folosit aplicația DB Browser for SQLite. Comanda SQL folosită:

ALTER TABLE biblioteca ADD COLUMN anul_publicarii INTEGER;
