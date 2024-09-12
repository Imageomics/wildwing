from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import subprocess

app = Flask(__name__)
app.secret_key = 'secret_key' 

# Route to display the HTML form (optional)
@app.route('/')
def index():
    return render_template('setup.html')

# Route to handle form submission and run the Python script
# @app.route('/templates/run_mission', methods=['POST'])
#def run_mission():
@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Get form data
        number_of_drones = request.form.get('number-drone')
        
        # # for each drone, get the model type
        # drone_models = []
        # for i in range(int(number_of_drones)):
        #     drone_models.append(request.form.get(f'drone-{i}-model'))
        
        drone_models = [request.form.get(f'drone-{i}-model') for i in range(int(number_of_drones))]
        drone_models = [model for model in drone_models if model]  # Remove any None or empty strings
        
        mission_type = request.form.get('mission-type')
        
        # Store form data in session
        session['mission_data'] = {
            'number_of_drones': number_of_drones,
            'drone_models': drone_models,
            'mission_type': mission_type
        }
        
        if mission_type == 'autonomous':
            # get autonomous mission type
            autonomous_mission_type = request.form.get('autonomous-mission-type')
            cv_model = request.form.get('model')
            session['mission_data']['autonomous_mission_type'] = autonomous_mission_type
            session['mission_data']['cv_model'] = cv_model
            
            # # launch the autonomous mission TEST THIS
            # result = subprocess.run(
            #     ['./launch_scripts/autonomous_mission.sh', autonomous_mission_type, number_of_drones, drone_models, cv_model],
            #     capture_output=True,
            #     text=True,
            #     check=True
            # )
        elif mission_type == 'waypoint':
            # get waypoint file 
            waypoint_file = request.files['waypoint-file'].filename
            session['mission_date']['waypoint_file'] = waypoint_file
            
            # # launch the waypoint mission TEST THIS 
            # result = subprocess.run(
            #     ['./launch_scripts/waypoint_mission.sh', number_of_drones, drone_models, waypoint_file],
            #     capture_output=True,
            #     text=True,
            #     check=True
            # )
        # else:
        #     # return error message
        #     return jsonify({"error": "Invalid mission type"}), 400

        return redirect(url_for('run_mission'))
        # Process the output or return a response
        # return jsonify({
        #     "message": f"Mission started with {number_of_drones} drones.",
        #     "mission_type": mission_type,
        #     #"script_output": result.stdout
        # })

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Script failed with error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/run_mission')
def run_mission():
    mission_data = session.get('mission_data')
    if mission_data is None:
        # If mission_data is not in session, redirect to the setup page
        return redirect(url_for('index', message="Please set up your mission first"))
    return render_template('run_mission.html', mission_data=mission_data)

@app.route('/end_mission')
def end_mission():
    # TO DO: add code to stop the drones, save data, etc.
    return redirect(url_for('analysis'))

@app.route('/analysis')
def analysis():
    # Retrieve mission data from session
    mission_data = session.get('mission_data', {})
    return render_template('analysis.html', mission_data=mission_data)

if __name__ == '__main__':
    app.run(debug=True, port=8080)