
import os
import math
from flask import Flask, render_template, request
#from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


k2data = {
        "pinpin": 1.74,
        "fixedfixed": 0.41
    }

    
@app.route("/", methods=["GET", "POST"])
def home():
    
    
    k2 = float(request.form.get("k2data", "1.74"))
    length = float(request.form.get("length", "20"))
    
    depth = float(request.form.get("depth", "0.5"))
    width = float(request.form.get("width", "0.5"))
    IZ = (width * depth**3) / 12
    AZ = width * 0.5
    E0 = 20
    G0 = 10
    strength = 30 
    k_mode = float(request.form.get("k_mode", 0.5))
    #partial material properties based on user selection
    gama_factor = 1.5
    dead_load = 1.2
    live_load = 1.6
    wind_load = 1.4
    seismic_load = 1.5
    snow_load = 1.3
    
    #report the utilization ratio based on the selected load types and material properties
    final_report = False
     
    
    
    if request.method == "POST":
            try:
                # Get the selected load types from the form
                selected_load_type = request.form.getlist("load_type")
                if selected_load_type == "office":
                    dead_load = 1.2
                    live_load = 1.6
                if selected_load_type == "garden":
                    dead_load = 1.3
                    live_load = 1.5
                if selected_load_type == "residential":
                    dead_load = 1.4
                    live_load = 1.7
                    wind_load = 1.4
                    seismic_load = 1.5
                    snow_load = 1.3
                if selected_load_type == "building":
                    dead_load = 1.5
                    live_load = 1.8
                    wind_load = 1.5
                    seismic_load = 1.6
                    snow_load = 1.4
            except ValueError:
                selected_load_type = "Error: Invalid load type."
                
    # collect selected load types from checkboxes add rhe corresponding values to the total load
    total_load = 0
    selected_loads = request.form.getlist("options")
    for load in selected_loads:
        if load == "dead_load":
            total_load += dead_load
        elif load == "live_load":
            total_load += live_load
        elif load == "wind_load":
            total_load += wind_load
        elif load == "seismic_load":
            total_load += seismic_load
        elif load == "snow_load":
            total_load += snow_load
    
                    
                    
                
    
    
    if request.method == "POST":
        try:
            material = request.form.get("material", 0)
            if material == "C-30":
                    strength = 30
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "C-40":
                    strength = 40
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "T-35":
                    strength = 35
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "MCG-15":
                    strength = 15
                    E0 = strength - 9
                    G0 = strength * 0.5
        except ValueError:
            material = "Error: Invalid numbers."
            
        
    
    # phi is k2 times AZ over length squere root of E0 times IZ over G0
    
    #phi = k2 * AZ
    
    phi = k2 * AZ * (IZ / length) ** 0.5 * (E0 * IZ / G0) ** 0.5
    
    # Design strength FD is phi times strength
    fd = k_mode * phi * (strength / gama_factor)
    
    #utilization ratio is total load over fd
    utilization_ratio = total_load / fd 
    if utilization_ratio <= 1:
        utilization_ratio = "The design is safe. The utilization ratio is within acceptable limits.", utilization_ratio
    else:
        utilization_ratio = "The design is not safe. The utilization ratio exceeds 1.", utilization_ratio

    final_report = True 
    
    return render_template("index.html", phi=phi, k_mode=k_mode, fd=fd, total_load=total_load, utilization_ratio=utilization_ratio, final_report=final_report)
    
    
 

if __name__ == "__main__":
    app.run(debug=True)
