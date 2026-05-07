(define (problem istance3)

    (:domain overcooked)

    
    (:objects
        c1 c2 - cook
        o1 o2 o3 o4 - order
        p1 p2 - plate
        is1 is2 is3 - ing_slot
        ps1 ps2 - plate_slot
        
        i1 - bread
        i2 - tomato
        i3 - meat
        i4 - salad
        i5 - meat
    )

    (:init
        ; Stato del Cuoco
        (hands_free c1)
        (at delivery_area c1)
        (= (plates_carried c1) 0)
        (is_runner c1)
        (is_preparer c1)
        
        (hands_free c2)
        (at delivery_area c2)
        (= (plates_carried c2) 0)
        (is_runner c2)
        (is_preparer c2)

        ; Stato dei Piatti
        (p_at_dish_washer p1)
        (p_at_dish_washer p2)

        ; Flusso degli Ordini
        (first o1)
        (next o1 o2)
        (next o2 o3)
        (next o3 o4)
        (last o4)
        (current_order o1)

        ; Requisiti Ordine 1
        (order_needs_type o1 type_bread)
        (order_needs_type o1 type_tomato)
        (order_needs_type o1 type_meat)
        (order_needs_type o1 type_salad)

        ; Requisiti Ordine 2
        (order_needs_type o2 type_bread)
        (order_needs_type o2 type_meat)
        (order_needs_type o2 type_salad)

        ; Requisiti Ordine 3
        (order_needs_type o3 type_bread)
        (order_needs_type o3 type_meat)
        (order_needs_type o3 type_salad)

        ; Requisiti Ordine 4
        (order_needs_type o4 type_bread)
        (order_needs_type o4 type_meat)

        (is_type i1 type_bread)
        (is_type i2 type_tomato)
        (is_type i3 type_meat)
        (is_type i4 type_salad)
        (is_type i5 type_meat)

        ; Contatori storage
        (= (in_storage type_bread) 4)
        (= (in_storage type_tomato) 1)
        (= (in_storage type_meat) 4)
        (= (in_storage type_salad) 3)

        ; Stato degli Slot
        (is_free is1)
        (is_free is2)
        (is_free is3)
        (is_free ps1)
        (is_free ps2)
    )

    (:goal 
        (forall (?o - order) (served ?o))    
    )

    (:metric minimize 
        (total-time)
    )
)