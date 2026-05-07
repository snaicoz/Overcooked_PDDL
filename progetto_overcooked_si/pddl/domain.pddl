(define (domain overcooked)
    (:requirements :strips :typing :negative-preconditions :fluents :conditional-effects :disjunctive-preconditions)

    (:types
      support location slot ingredient_type - object
      plate ingredient - support
      choppable meat bread - ingredient
      salad tomato - choppable
      ing_slot plate_slot - slot
      cook
      order
    )

    (:constants
        storage dish_washer dirty_area grill ing_table plate_table delivery_area chopping_station - location
        type_tomato type_salad type_meat type_bread - ingredient_type
    )

    (:predicates
        
        ; Stato del Cuoco
        (hands_free ?c - cook)
        (grasping ?i - support ?c - cook)
        (grasping_ready_order ?c - cook  ?o - order)
        (at ?l - location ?c - cook)
        (must_deliver ?c)
        (is_preparer ?c - cook)
        (is_runner ?c - cook)
        
        ; Stato dei Piatti
        (dirty ?p - plate)
        (in_slot ?p - plate ?s - plate_slot)
        (p_at_dish_washer ?p - plate)
        (p_at_dirty_area ?p - plate)
        (p_ready ?p - plate)

        ; Gestione Ordini
        (served ?o - order)
        (first ?o1 - order)   ;è completamente inutile ma per qualche motivo riduce notevolmente i tempi di search  
        (next ?o1 ?o2 - order)
        (last ?o - order)
        (current_order ?o - order)
        (ready ?o - order)
        (order_needs_type ?o - order ?it - ingredient_type)
        (plate_order ?p - plate ?o - order)
        
        
        ; Gestione Ingredienti Generici
        (prepared ?i - ingredient)
        (is_type ?i - ingredient ?it - ingredient_type)
        (in_game ?i - ingredient) 

        ; Gestione Slot
        (is_free ?s - slot)
        (ing_in_slot ?i - ingredient ?s - ing_slot)
        (ing_on_plate ?i - ingredient ?p - plate)
    )

    (:functions
        (in_storage ?it - ingredient_type) ;tiene conto quanti ingredienti sono rimasti in dispensa per tipo
        (plates_carried ?c - cook)      ;è completamente inutile ma per qualche motivo riduce notevolmente i tempi di search
    )

    
    
    ;Permette ai cuochi di muoversi da una zona ad un'altra della mappa
    (:action moveTo
        :parameters (?c - cook ?l1 ?l2 - location)
        :precondition (at ?l1 ?c)
        :effect (and
            (not (at ?l1 ?c)) 
            (at ?l2 ?c)
        )
    )

    
    ;Permette al cuoco preparer di prelevare un ingrediente dalla dispensa
    (:action pickup_ingredient_from_storage
        :parameters (?i - ingredient ?c - cook ?it - ingredient_type ?o - order)
        :precondition (and
            (is_preparer ?c)
            (current_order ?o)
            (order_needs_type ?o ?it)
            (not (must_deliver ?c))
            (at storage ?c)
            (hands_free ?c)
            (is_type ?i ?it)
            (not (in_game ?i))     ; L'oggetto i deve essere "libero"
            (> (in_storage ?it) 0) ; Deve esserci disponibilità in dispensa
        )
        :effect (and
            (not (hands_free ?c))
            (grasping ?i ?c)
            (in_game ?i)           ; L'oggetto entra nel mondo fisico
            (decrease (in_storage ?it) 1)
        )
    )

    ;Permette al cuoco preparer di appoggiare un ingrediente sul tavolo degli ingredienti se gli slot non sono tutti pieni
    (:action drop_ingredient
        :parameters (?i - ingredient ?c - cook ?s - ing_slot)
        :precondition (and
            (is_preparer ?c)
            (not (must_deliver ?c)) 
            (grasping ?i ?c)
            (at ing_table ?c) 
            (is_free ?s)      
        )
        :effect (and 
            (not (grasping ?i ?c))
            (hands_free ?c) 
            (not (is_free ?s))
            (ing_in_slot ?i ?s)
        )
    )

    ;Permette al cuoco preparer di prendere un oggetto dal tavolo degli ingredienti
    (:action pickup_ingredient_from_ing_table
        :parameters (?i - ingredient ?c - cook ?s - ing_slot)
        :precondition (and
            (is_preparer ?c)
            (not (must_deliver ?c))
            (at ing_table ?c)
            (hands_free ?c)
            (ing_in_slot ?i ?s)
        )
        :effect (and
            (not (hands_free ?c))
            (grasping ?i ?c)
            (is_free ?s)
            (not (ing_in_slot ?i ?s))
        )
    )

    ;Permette al cuoco preparer di tagliare pomodori e insalata
    (:action chop_ing
        :parameters (?ch - choppable ?c - cook)
        :precondition (and
            (is_preparer ?c)
            (not (must_deliver ?c))
            (grasping ?ch ?c) 
            (at chopping_station ?c)
            (in_game ?ch) 
        )
        :effect (and (prepared ?ch))
    )

    ;Permette al cuoco preparer di preparare il pane
    (:action prepare_bread
        :parameters (?b - bread ?c - cook)
        :precondition (and
            (is_preparer ?c)
            (not (must_deliver ?c))
            (grasping ?b ?c) 
            (at chopping_station ?c)
            (in_game ?b) 
        )
        :effect (and (prepared ?b))
    )



    ;Permette al cuoco preparer di cuocere la carne
    (:action cook_meat
        :parameters (?m - meat ?c - cook)
        :precondition (and
            (is_preparer ?c)
            (not (must_deliver ?c)) 
            (grasping ?m ?c) 
            (at grill ?c)
            (in_game ?m) 
        )
        :effect (and (prepared ?m))
    )

   
    ;Permette di raccogliere un piatto pulito dalla lavastoviglie
    (:action pickup_plate_from_dish_washer
        :parameters (?p - plate ?c - cook)
        :precondition (and
            (is_runner ?c)
            (not (must_deliver ?c))
            (at dish_washer ?c)
            (hands_free ?c)
            (p_at_dish_washer ?p)
            (not (dirty ?p))
        )   
        :effect (and
            (not (hands_free ?c))
            (grasping ?p ?c)
            (not (p_at_dish_washer ?p))
        )
    )

    ;Permette al cuoco runner di rilasciare un piatto pulito al tavolo dei piatti
    (:action drop_clean_plate
        :parameters (?p - plate ?c - cook ?s - plate_slot)
        :precondition (and 
            (is_runner ?c)
            (not (must_deliver ?c))
            (not (p_ready ?p))
            (grasping ?p ?c)
            (not (dirty ?p))
            (at plate_table ?c)
            (is_free ?s)       
        )
        :effect (and 
            (not (grasping ?p ?c))
            (hands_free ?c)
            (not (is_free ?s))
            (in_slot ?p ?s)
        )
    )

    ;Permette al cuoco runner di raccogliere un piatto dalla zona dei piatti sporchi
    (:action pickup_plate_from_dirty_area
        :parameters (?p - plate ?c - cook)
        :precondition (and
            (is_runner ?c)
            (not (must_deliver ?c))
            (at dirty_area ?c)
            (hands_free ?c)
            (p_at_dirty_area ?p)
        )
        :effect (and
            (not (hands_free ?c))
            (grasping ?p ?c)
            (not (p_at_dirty_area ?p))
            (assign (plates_carried ?c) 1)
        )
    )

    ;Permette al cuoco runner di depositare un piatto sporco alla lavastoviglie
    (:action deposit_plate_at_dish_washer
        :parameters (?c - cook ?p - plate)
        :precondition (and 
            (is_runner ?c)
            (not (must_deliver ?c))
            (at dish_washer ?c)
            (grasping ?p ?c)
            (dirty ?p)
        )
        :effect (and 
            (not (grasping ?p ?c))
            (decrease (plates_carried ?c) 1)
            (p_at_dish_washer ?p)
            (when (= (plates_carried ?c) 1) (hands_free ?c))
        )
    )

    ;Permette al cuoco runner di far partire la lavastoviglie e lavare tutti i piatti sporchi
    (:action start_dish_washer
        :parameters (?c - cook)
        :precondition (and
            (is_runner ?c)
            (not (must_deliver ?c))
            (at dish_washer ?c)
        )
        :effect (and 
            (forall (?p - plate)
                (when (p_at_dish_washer ?p) 
                    (not (dirty ?p)))
            )
        )
    )

    
    ;Permette al cuoco preparer di aggiungere un ingrediente sopra un piatto dell'ordine corrente
    (:action add_ingredient_to_plate
        :parameters (?s - plate_slot ?c - cook ?p - plate ?i - ingredient ?o - order ?it - ingredient_type)
        :precondition (and
            (is_preparer ?c)
            (current_order ?o)
            (order_needs_type ?o ?it)
            (is_type ?i ?it)
            (not (must_deliver ?c))
            (prepared ?i)
            (in_slot ?p ?s)
            (at plate_table ?c)
            (grasping ?i ?c)
            (not (p_ready ?p))
        )
        :effect (and
            (not (grasping ?i ?c))
            (hands_free ?c)
            (ing_on_plate ?i ?p)
         )
    )

    ;Permette di stabilire che un ordine è pronto ad essere consegnato
    (:action order_ready
        :parameters (?o - order ?p - plate)
        :precondition (and 
            (not (p_ready ?p))
            (current_order ?o)
            ; Controllo che ogni tipo richiesto dall'ordine sia sul piatto
            (forall (?it - ingredient_type)
                (or 
                    (not (order_needs_type ?o ?it))
                    (exists (?i - ingredient)
                        (and 
                            (is_type ?i ?it)
                            (ing_on_plate ?i ?p)
                            (prepared ?i)
                        )
                    )
                )
            )
        )
        :effect (and
            (ready ?o)
            (p_ready ?p)
            (plate_order ?p ?o)
        )
    )

    ;Permette al cuoco runner di prendere in mano l'ordine pronto
    (:action pick_up_ready_order
        :parameters (?c - cook ?p - plate ?s - plate_slot ?o - order)
        :precondition (and 
            (is_runner ?c)
            (not (must_deliver ?c))
            (at plate_table ?c)
            (hands_free ?c)
            (in_slot ?p ?s)
            (ready ?o)
            (current_order ?o)
            (plate_order ?p ?o)
        )
        :effect (and 
            (not (hands_free ?c))
            (grasping ?p ?c)
            (not (in_slot ?p ?s))
            (is_free ?s)
            (grasping_ready_order ?c ?o)
            (must_deliver ?c)
        )
    )

    ;Permette al cuoco runner di consegnare al cliente l'ordine pronto
    (:action deliver_order
        :parameters (?c - cook ?p - plate ?o_current - order ?o_next - order)
        :precondition (and 
            (is_runner ?c)
            (at delivery_area ?c)
            (grasping ?p ?c)
            (grasping_ready_order ?c ?o_current)
            (or (next ?o_current ?o_next) (last ?o_current))
        )
        :effect (and 
            (forall (?i - ingredient)
                (when (ing_on_plate ?i ?p)
                    (and
                        (not (ing_on_plate ?i ?p))
                        (not (in_game ?i))    ; L'oggetto i torna disponibile
                        (not (prepared ?i))   ; Resetta lo stato
                    )
                )
            )
            (not (grasping ?p ?c))
            (not (grasping_ready_order ?c ?o_current))
            (not (current_order ?o_current))
            (hands_free ?c)
            (when (next ?o_current ?o_next)
                (current_order ?o_next)
            )
            (served ?o_current)
            (dirty ?p)
            (p_at_dirty_area ?p)
            (not (p_ready ?p))
            (not (plate_order ?p ?o_current))
            (not (must_deliver ?c))
        )
    )
)