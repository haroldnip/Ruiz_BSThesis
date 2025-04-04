allowed_rows_input = [
    (0, {"jeep", "truck"}), # Row 0 allowed for lane changing
    (1, {"jeep", "truck" }),  
    (2, {"jeep", "truck"})  # Row 2 allowed for lane changing
]
jeepney_allowed_rows = [0, 2] #allowed rows for initialization
truck_allowed_rows = [0, 2]  #allowed rows for initialization
safe_stopping_speed = 2
safe_deceleration = 2

case = "A"

#Control Set-Up