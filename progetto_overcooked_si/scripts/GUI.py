import re                       #Gestione ricerca e manipolazione stringhe
import turtle                   #Grafica vettoriale semplice per disegnare a video
import subprocess               #Esecuzione di comandi di sistema e gestione processi esterni
import os                       #Fornisce funzioni per interagire con il sistema operativo
import textwrap                 #Wrapping automatico del testo per andare a capo
import tkinter.messagebox       #La parte di tkinter che genera finestre di avviso

#CONFIGURAZIONE PERCORSI
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  #Identifica la cartella principale del progetto
PDDL_DIR = os.path.join(BASE_DIR, "pddl")                               #Identifica la sottocartella "pddl"
PLANNER_JAR = os.path.join(PDDL_DIR, "enhsp25.jar")                     #Punta il file eseguibile Java del pianificatore
DOMAIN_PDDL = os.path.join(PDDL_DIR, "domain.pddl")                     #Punta il file pddl che contiene la logica del dominio
OUTPUT_FILE = os.path.join(BASE_DIR, "piano_generato.txt")              #Punta il file di testo dove verrà salvato il piano finale

#VARIABILI DI STATO
agents_plan = {}                                #Mappa ogni agente al rispettivo piano
cooks = {}                                      #Traccia lo stato dei cuochi
graphic_objects = {}                            #Necessario per aggiornare la grafica a schermo quando lo stato cambia
time_list = []                                  #Memorizza i passaggi temporali del piano
time_index = 0                                  #Puntatore per sapere in quale esatto istante ci si trova
is_paused = True                                #Controlla il flusso della simulazione
who_holds_what = {"c1": None, "c2": None}       #Tiene traccia delle risorse che i cuochi hanno in mano
total_orders = 0                                #Contatore numerico per tracciare gli ordini totali
completed_orders = 0                            #Contatore numerico per tracciare gli ordini completati

#MAPPA DI INTERAZIONE TRA CUOCO E ZONE
interaction_map = { 
    "delivery_area": (-13, 265), 
    "storage": (230, 250),
    "plate_table": (-280, 250),
    "chopping_station": (-300, -5),
    "ing_table": (270, 140),
    "grill": (320, -17),
    "dish_washer": (-175, -60),
    "dirty_area": (150, -65)
}

#MAPPA DEGLI SLOT
slot_map = {
    "is1": (350, 155),
    "is2": (475, 155),
    "is3": (600, 155),
    "ps1": (-420, 270),
    "ps2": (-530, 270),
    "dwc": (-240, -130),
    "dwd": (-110, -130),
    "da": (130, -120)
}

#DIZIONARI
#Contiene le liste dei tipi degli ingredienti presenti sul plate_slot (bread, tomato, ecc)
ps_comp = {
    "ps1": [],
    "ps2": []
}

#Contiene le liste degli ingredienti presenti sul plate_slot (i1, i2, i3)
ps_comp_in = {
    "ps1": [],
    "ps2": []
}

#Associa ogni ingrediente al suo tipo
i_n = {
    "i1": "bread",
    "i2": "tomato",
    "i3": "meat",
    "i4": "salad",
    "i5": "meat"
}

#Tiene traccia dell'ultimo ingrediente inserito su un piatto
last_ing = {
    "p1": None,
    "p2": None
}

#Tiene traccia dei piatti sporchi presenti alla dishwasher
p_dirty_at_dw = {
    "p1": False,
    "p2": False
}

#Mappa di configurazione che associa combinazioni di ingredienti a specifici file grafici
ingredients_to_images_map = {
    frozenset(["bread"]): "plate_bread.gif",
    frozenset(["meat"]): "plate_meat.gif",
    frozenset(["salad"]): "plate_salad.gif",
    frozenset(["tomato"]): "plate_tomato.gif",
    frozenset(["bread", "meat"]): "plate_bread_meat.gif",
    frozenset(["bread", "tomato"]): "plate_bread_tomato.gif",
    frozenset(["bread", "salad"]): "plate_bread_salad.gif",
    frozenset(["meat", "tomato"]): "plate_meat_tomato.gif",
    frozenset(["meat", "salad"]): "plate_meat_salad.gif",
    frozenset(["salad", "tomato"]): "plate_tomato_salad.gif",
    frozenset(["bread", "meat", "tomato"]): "plate_bread_meat_tomato.gif",
    frozenset(["bread", "meat", "salad"]): "plate_bread_meat_salad.gif",
    frozenset(["tomato", "meat", "salad"]): "plate_tomato_meat_salad.gif",
    frozenset(["bread", "meat", "tomato", "salad"]): "plate_bread_meat_tomato_salad.gif"
}

#PARSER: analizza l'output testuale di un pianificatore PDDL per estrarre il piano d'azione
#Popola le variabili globali agents_plan e time_list
def parse_pddl_output(stdout_text):
    global agents_plan, time_list
    agents_plan = {}
    time_list = []
    pattern = re.compile(r"(\d+\.\d+):\s*\((.*?)\)")    #Cattura righe nel formato: "0.000: (move c1 loc1 loc2)"
    found = False
    for line in stdout_text.splitlines():
        match = pattern.search(line)
        if match:
            found = True
            t = float(match.group(1))       #Converte il primo gruppo catturato (stringa) in un numero decimale
            if t not in time_list:          #Se il timestamp non è ancora presente nella lista dei tempi, lo aggiunge
                time_list.append(t)
            parts = match.group(2).split()  #Divide il contenuto del secondo gruppo (move c1 l1 l2) in una lista di parole
            action_name = parts[0]
            args = parts[1:]
            agent = next((a for a in args if a.startswith('c')), "c1")  #Identifica agente: primo argomento che inizia con 'c'; default 'c1'
            if agent not in agents_plan:        #Se l'agente identificato non ha ancora una voce nel dizionario, crea una lista vuota
                agents_plan[agent] = []     
            #Aggiunge un dizionario con i dettagli dell'azione alla lista dell'agente specifico
            agents_plan[agent].append({"time": t, "action": action_name, "args": args}) 
    return found

#LOGICA DI GIOCO
#Funzione per visualizzare il timestamp
def show_timestamp():
    timestamp_pen.clear()
    #Se time_list non è vuota e l'indice corrente è nei limiti della lista, estrae il valore; in caso contrario usa 0.0
    current_time = time_list[time_index] if time_list and time_index < len(time_list) else 0.0
    timestamp_pen.write(f"TIMESTAMP: {current_time}", align="center", font=("Courier New", 19, "bold"))

#Funzione play
#Al click del mouse, turtle invia alla funzione play le coordinate precise (X e Y) del punto in cui il mouse ha cliccato
#Senza coordinate, il programma andrebbe in crash perché turtle invierebbe le coordinate a una funzione che non è pronta a riceverle
def play(x=0, y=0):   
    global is_paused                  
    if agents_plan and is_paused:       #Procede solo se esiste un piano d'azione caricato e se la simulazione è attualmente in pausa
        is_paused = False
        btn_resume.shape("play_premuto.gif")
        btn_stop.shape("stop_normale.gif")
        messenger.clear()
        if time_index == 0:
            print("Simulazione avviata.", flush=True)
        else:
            print("Simulazione ripresa.", flush=True)
        animation_cycle()       #Avvia il loop principale dell'animazione

#Funzione stop
def stop(x=0, y=0):
    global is_paused
    is_paused = True
    btn_stop.shape("stop_premuto.gif")
    btn_resume.shape("play_normale.gif")
    print("Simulazione in pausa.", flush=True)
    change_level = tkinter.messagebox.askyesno(     #Genera una finestra popup con pulsanti Sì/No
        "Pausa", 
        "Vuoi cambiare livello?\n\nScegli 'Sì' per caricare un nuovo livello, oppure 'No' per riprendere questo."
    )
    if change_level:
        ask_next_level()

#Funzione restart
def restart(x=0, y=0):
    global time_index, is_paused, who_holds_what, completed_orders
    is_paused = True
    btn_stop.shape("stop_normale.gif")
    btn_resume.shape("play_normale.gif")
    time_index = 0                                  #Reset dei contatori logici
    completed_orders = 0
    who_holds_what = {"c1": None, "c2": None}       #Svuota lo stato degli agenti: nessuno sta trasportando nulla all'inizio
    
    for key in ps_comp:                             ##Cicli di pulizia per i dizionari che tracciano piatti e ingredienti
        ps_comp[key].clear()
    for key in ps_comp_in:
        ps_comp_in[key].clear()
    for key in last_ing:
        last_ing[key] = None
    screen.tracer(0)                                #Disabilita l'aggiornamento grafico
    
    for c_id in cooks:                              #Riposiziona tutti i cuochi alla delivery_area e li rende visibili
        cooks[c_id].goto(interaction_map["delivery_area"])
        cooks[c_id].showturtle()
    
    for obj_id in graphic_objects:
        if "p" in obj_id:                           #Se l'oggetto è un piatto, lo riposiziona pulito alla dishwasher
            graphic_objects[obj_id].goto(slot_map["dwc"])
            graphic_objects[obj_id].shape("plate.gif")
        else:                                       #Se è un altro tipo di oggetto, lo nasconde
            graphic_objects[obj_id].hideturtle() 
    
    action_writer.clear()
    order_writer.clear()
    order_writer.write(
        f"Ordini totali:     {total_orders}\nOrdini completati: 0",
        font=("Courier New", 14, "bold")
    )
    show_timestamp()
    screen.update()                                 #Forza l'aggiornamento della schermata per mostrare le nuove posizioni
    screen.tracer(1)                                #Forza l'aggiornamento grafico
    print("Simulazione resettata al tempo 0.", flush=True)

#Funzione exit
def exit_app(x=0, y=0):
    print("Chiusura dell'applicazione.", flush=True)
    os._exit(0)

#Funzione ciclo di animazione
def animation_cycle():
    global time_index, is_paused, completed_orders
    if is_paused: return    #Se l'animazione viene bloccata esce dalla funzione

    if time_index >= len(time_list):    #Verifica se time_index ha raggiunto o superato il numero max di elementi di time_list
        is_paused = True
        btn_resume.shape("play_normale.gif")
        print("Simulazione completata.", flush=True)
        screen.ontimer(ask_next_level, 800)     #Chiede, dopo 800 ms, quale livello eseguire successivamente
        return

    show_timestamp()
    current_time = time_list[time_index]

    #Aggiorna taccuino
    log_lines = []
    for c_id in sorted(agents_plan.keys()):     #Inizia un ciclo ordinato sugli ID dei cuochi
        current = [a for a in agents_plan[c_id] if a["time"] == current_time]   #Selezionata azione corrente
        desc = f"{current[0]['action']} {' '.join(current[0]['args'])}" if current else "waiting..."    #Formatta la stringa da stampare a schermo relativa all'azione eseguita dal cuoco al timestamp corrente
        line = f"{c_id}: ({desc})"
        log_lines.extend(textwrap.wrap(line, width=20))     #Spezzetta line in sotto stringhe di lunghezza 20
        log_lines.append("")  #line vuota di separazione tra agenti

    action_writer.clear()
    action_writer.write("\n".join(log_lines), font=("Courier New", 14, "bold"))     #Azioni scritte a schermo

    for c_id, actions in agents_plan.items():
        current = [a for a in actions if a["time"] == current_time]     #Estrae azione corrente
        for act in current:
            name, args = act["action"].lower(), act["args"]     #name contiene il nome dell'azione, args è una lista di parametri

            #Se l'azione è moveTo:
            if "moveto" in name:
                cook_id, destination = args[0], args[2]
                if destination in interaction_map and cook_id in cooks:
                    start_pos = cooks[cook_id].pos()
                    end_pos = interaction_map[destination]
                    
                    grasped_object = who_holds_what.get(cook_id)
         
                    steps = 80     #Questo parametro influenza la velocità dello spostamento

                    #Ciclo che fa muovere il cuoco di un passo alla volta
                    for i in range(1, steps + 1):
                        screen.tracer(0)        #Permette di muovere il cuoco e ciò che ha in mano contemporaneamente
                        ratio = i / steps
         
                        curr_x = start_pos[0] + (end_pos[0] - start_pos[0]) * ratio
                        curr_y = start_pos[1] + (end_pos[1] - start_pos[1]) * ratio
                        cooks[cook_id].goto(curr_x, curr_y)
         
                        if grasped_object in graphic_objects:
                            graphic_objects[grasped_object].goto(curr_x + 30, curr_y - 30)
          
                        screen.update()
                 
                    screen.tracer(1)

            #Se l'azione è pickup_ingredient_from_storage o pickup_ingredient_from_ing_table:
            elif "pickup" in name:
                obj_id = args[0]
                cook_id = args[1]
                
                if obj_id in graphic_objects:
                    who_holds_what[cook_id] = obj_id
         
                    cx, cy = cooks[cook_id].pos()
                    graphic_objects[obj_id].goto(cx + 30, cy - 30)      #Per posizionare l'oggetto nella mano del cuoco
              
                    graphic_objects[obj_id].showturtle()
                    
                    args_str = str(args)    #Converte una lista in stringa

                    #Assegna l'immagine corretta in base al tipo di ingrediente
                    if "tomato" in args_str: graphic_objects[obj_id].shape("tomato.gif")
                    elif "salad" in args_str: graphic_objects[obj_id].shape("salad.gif")
                    elif "meat" in args_str: graphic_objects[obj_id].shape("meat.gif")
                    elif "bread" in args_str: graphic_objects[obj_id].shape("bread.gif")

            #Se l'azione è pick_up_ready_order:
            elif "pick_up" in name:
                obj_id = args[1]
                cook_id = args[0]
                plate_slot = args[2]
            
                cx, cy = cooks[cook_id].pos()

                #Ogni ingrediente sul piatto viene spostato in mano del cuoco
                for i in ps_comp_in[plate_slot]:
                    graphic_objects[i].goto(cx + 25, cy - 15)

                who_holds_what[cook_id] = ps_comp_in[plate_slot][-1]    #Assegnato l'ultimo ingrediente aggiunto al piatto
                
                graphic_objects[obj_id].hideturtle()

                #Reset dict di tracciamento di composizione ordini 
                ps_comp[plate_slot].clear()
                ps_comp_in[plate_slot].clear()

            #Se l'azione è drop_clean_plate, drop_ingredient o deposit_plate_at_dish_washer:
            elif "drop" in name or "deposit" in name:
                cook_id = args[1] if "drop" in name else args[0]
                obj_id = args[0] if "drop" in name else args[1]
         
                location = args[2] if "drop" in name else next((s for s in interaction_map if s in name), None)
                who_holds_what[cook_id] = None
                target = slot_map.get(location) or interaction_map.get(location)
                if "deposit" in name:
                    target = slot_map["dwd"]
                    p_dirty_at_dw[obj_id] = True
                if target and obj_id in graphic_objects:
                    graphic_objects[obj_id].goto(target)

            #Se l'azione è cook_meat:
            elif "cook_meat" in name: graphic_objects[args[0]].shape("cooked_meat.gif")

            #Se l'azione è chop_ing:
            elif "chop_ing" in name:
                att = graphic_objects[args[0]].shape()
                if "tomato" in att: graphic_objects[args[0]].shape("chopped_tomato.gif")
                elif "salad" in att: graphic_objects[args[0]].shape("chopped_salad.gif")

            #Se l'azione è prepare_bread:
            elif "prepare_bread" in name: graphic_objects[args[0]].shape("prepared_bread.gif")

            #Se l'azione è add_ingredient_to_plate:
            elif "add_ingredient" in name:
                cook_id = args[1] 
                ing = args[3]
                plate_slot = args[0]
                plate = args[2]
                ps_comp[plate_slot].append(i_n[ing])    #Aggiunge al dict il tipo di ingrediente appena aggiunto (bread, tomato, ..)
                
                #Logica di visualizzazione dell'ultima versione dell'ordine
                if len(ps_comp_in[plate_slot]) == 0:
                    graphic_objects[plate].hideturtle()
                else:
                    last_ing[plate] = ps_comp_in[plate_slot][-1]
                    graphic_objects[last_ing[plate]].hideturtle()


                ps_comp_in[plate_slot].append(ing)    

                target = slot_map.get(plate_slot)
                graphic_objects[ing].goto(target)

                who_holds_what[cook_id] = None

                shape = ingredients_to_images_map.get(frozenset(ps_comp[plate_slot]))
                if shape:
                    graphic_objects[ing].shape(shape)

            #Se l'azione è deliver_order:   
            elif "deliver" in name: 
                cook_id = args[0]
                obj_id = args[1]
                held_object = who_holds_what[cook_id]
                graphic_objects[held_object].hideturtle()
                last_ing[obj_id] = None
                who_holds_what[cook_id] = None
                graphic_objects[obj_id].shape("dirty_plate.gif")    #Assegnata immagine del piatto sporco
                graphic_objects[obj_id].goto(slot_map["da"])    #Il piatto ora sporco va alla dirty_area
                graphic_objects[obj_id].showturtle()
                #Aggiorna notebook — ordini
                completed_orders += 1
                order_writer.clear()
                order_writer.write(
                    f"Ordini totali:     {total_orders}\nOrdini completati: {completed_orders}",
                    font=("Courier New", 14, "bold")
                )
            #Se l'azione è start_dish_washer:
            elif "start_dish_washer" in name:
                for key in p_dirty_at_dw:
                    if p_dirty_at_dw[key]:
                        graphic_objects[key].shape("plate.gif")     #Assegnata immagine del piatto pulito
                        graphic_objects[key].goto(slot_map["dwc"])  #Il piatto viene spostato nella pila dei piatti puliti
                        p_dirty_at_dw[key] = False

    time_index += 1
    screen.ontimer(animation_cycle, 500)    #Stabilisce la durata di ogni step

#Funzione per creare i pulsanti
def make_button(x, y, shape, callback):
    t = turtle.Turtle()
    t.penup()
    t.goto(x, y)
    t.shape(shape)
    t.onclick(callback) #Callback rappresenta la funzione da eseguire quando un pulsante viene premuto
    return t

#Funzione per caricare un livello
def load_level(chosen_level):
    global time_index, is_paused, who_holds_what, total_orders, completed_orders

    #Reset stato
    is_paused = True    #Rimane a true finchè non viene premuto play
    time_index = 0
    completed_orders = 0
    who_holds_what = {"c1": None, "c2": None}
    #Azzera i dict relativi al tracciamento della composizione degli ordini e della posizione dei piatti
    for key in ps_comp: ps_comp[key].clear()    
    for key in ps_comp_in: ps_comp_in[key].clear()
    for key in last_ing: last_ing[key] = None
    for key in p_dirty_at_dw: p_dirty_at_dw[key] = False

    #Azzera oggetti grafici precedenti
    screen.tracer(0)
    for t in cooks.values(): t.hideturtle()
    for t in graphic_objects.values(): t.hideturtle()
    cooks.clear()
    graphic_objects.clear()
    action_writer.clear()
    order_writer.clear()
    btn_resume.shape("play_normale.gif")
    btn_stop.shape("stop_normale.gif")
    screen.update()
    screen.tracer(1)

    messenger.clear()
    #Scritta di caricamento del livello
    messenger.write("Calcolo del piano...", align="center", font=("Courier New", 20, "bold"))

    #Costruisce il percorso del file problem corrispondente al livello selezionato dalla cartella pddl
    prob_file = os.path.join(PDDL_DIR, f"problem{int(chosen_level)}.pddl")
    #Comando terminale per lanciare il planner con euristica hadd 
    command = ["java", "-jar", PLANNER_JAR, "-o", DOMAIN_PDDL, "-f", prob_file, "-h", "hadd"]

    try:
        #Istruzione per eseguire il planner
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        #Risultato salvato in un file di testo
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"--- PIANO GENERATO PER IL LIVELLO {int(chosen_level)} ---\n\n")
            f.write(result.stdout)

        if parse_pddl_output(result.stdout):
            #Calcola ordini totali dal piano
            total_orders = sum(
                1 for actions in agents_plan.values()
                for a in actions if "deliver" in a["action"].lower()
            )
            order_writer.clear()

            #Fa comparire le scritte di tracciamento ordini
            order_writer.write(
                f"Ordini totali:     {total_orders}\nOrdini completati: 0",
                font=("Courier New", 14, "bold")
            )
            show_timestamp()

            messenger.clear()   #Eliminata scritta di caricamento piano
            screen.tracer(0)

            first_cook = True

            #Inizializzazione cuochi
            for c_id in agents_plan.keys():
                if c_id not in cooks:
                    t = turtle.Turtle()
                    if first_cook:
                        t.shape("cook.gif")
                        first_cook = False
                    else:
                        t.shape("cook2.gif")
                    t.penup()
                    cooks[c_id] = t
                cooks[c_id].goto(interaction_map["delivery_area"])
                cooks[c_id].showturtle()

            #Creazione ingredienti (massimo 5 nelle istanze più complesse)
            for i in range(1, 6):
                o = turtle.Turtle()
                o.shape("circle")
                o.penup()
                o.hideturtle()
                graphic_objects[f"i{i}"] = o
            
            #Creazione piatti (sempre 2)
            for p in range(1, 3):
                o = turtle.Turtle()
                o.shape("plate.gif")
                o.penup()
                o.goto(slot_map["dwc"])
                o.showturtle()
                graphic_objects[f"p{p}"] = o

            screen.update()     #Aggiornamento sincronizzato dello schermo
            screen.tracer(1)    #Sbloccate animazioni istantanee
            messenger.write("Piano pronto. Premi Play per iniziare.", align="center", font=("Courier New", 16, "italic"))

    except Exception as e:
        messenger.clear()
        messenger.write(f"Errore: {e}", align="center", font=("Courier New", 14, "normal"))
        print(f"Errore: {e}")

#Funzione per chiedere il prossimo livello
def ask_next_level():
    level = screen.numinput("Overcooked", "Scegli il livello (1-5):", minval=1, maxval=5)
    if level:
        load_level(level)

#AVVIO GUI
screen = turtle.Screen()        #Inizializza l'oggetto Screen, che rappresenta la finestra in cui avverrà il disegno
screen.setup(1800, 867, startx=0, starty=None)
screen.tracer(0)       #Blocca l'aggiornamento dello schermo
screen.setworldcoordinates(-650, -433, 1150, 433)       #Sx, inferiore, dx, superiore

#Immagine del taccuino
screen.register_shape("sfondo_taccuino.gif")
img_background_notebook = turtle.Turtle()
img_background_notebook.penup()     #Evita che l'oggetto lasci una striscia nera mentre si sposta verso le coordinate target
img_background_notebook.shape("sfondo_taccuino.gif")
img_background_notebook.goto(900, -60)   
img_background_notebook.showturtle()

#Immagine di sfondo
screen.register_shape("sfondo_cucina.gif")
bg = turtle.Turtle()
bg.shape("sfondo_cucina.gif")
bg.penup()
bg.goto(0, 0)
bg.showturtle()

for img in ["cook.gif", "meat.gif", "cooked_meat.gif", "tomato.gif", "chopped_tomato.gif", 
            "salad.gif", "chopped_salad.gif", "bread.gif", "prepared_bread.gif",
            "play_normale.gif", "play_premuto.gif", "stop_normale.gif", "stop_premuto.gif", 
            "restart.gif", "exit.gif", "plate.gif", "plate_bread.gif", "plate_tomato.gif", 
            "plate_salad.gif", "plate_meat.gif", "plate_bread_meat.gif", "plate_bread_tomato.gif", 
            "plate_bread_salad.gif", "plate_meat_tomato.gif", "plate_meat_salad.gif", "plate_tomato_salad.gif",
            "plate_bread_meat_tomato.gif", "plate_bread_meat_salad.gif", "plate_tomato_meat_salad.gif",
            "plate_bread_meat_tomato_salad.gif", "dirty_plate.gif", "taccuino.gif", "cook2.gif"]:
    screen.register_shape(img)

#Scrittura del timestamp
timestamp_pen = turtle.Turtle()
timestamp_pen.hideturtle()
timestamp_pen.penup()
timestamp_pen.color("black")
timestamp_pen.goto(960, -265)

#Scrittura di "Caricamento..." e "Premi Play per iniziare..."
messenger = turtle.Turtle()
messenger.hideturtle()
messenger.penup()
messenger.color("white")
messenger.goto(0, 0)

#Taccuino 
img_notebook = turtle.Turtle()
img_notebook.penup()
img_notebook.shape("taccuino.gif")
img_notebook.goto(960, 0)
img_notebook.showturtle()

#Scrittura delle azioni dei cuochi ad ogni timestamp sul taccuino
action_writer = turtle.Turtle()
action_writer.hideturtle()
action_writer.penup()
action_writer.color("black")
action_writer.goto(825, 100)

#Scrittura per la gestione degli ordini
order_writer = turtle.Turtle()
order_writer.hideturtle()
order_writer.penup()
order_writer.color("black")
order_writer.goto(830, -62)

#Bottoni
btn_restart = make_button(-300, -360, "restart.gif", restart)
btn_resume = make_button(-100, -360, "play_normale.gif", play)
btn_stop = make_button( 100, -360, "stop_normale.gif", stop)
btn_exit = make_button( 300, -360, "exit.gif", exit_app)

#Linea di separazione
separator = turtle.Turtle()
separator.penup()                
separator.shape("square")        
separator.color("black")         
separator.shapesize(stretch_wid=44, stretch_len=0.70)
separator.goto(770, 0)
separator.showturtle()

screen.update()
screen.tracer(1)

#Avvio iniziale
chosen_level = screen.numinput("Overcooked", "Scegli il livello (1-5):", minval=1, maxval=5)
if chosen_level:
    load_level(chosen_level)

turtle.done()