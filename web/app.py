from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess

app = Flask(__name__)

# Route to display the HTML form (optional)
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission and run the Python script
@app.route('/run-mission', methods=['POST'])
def run_mission():
    try:
        # Get form data
        number_of_drones = request.form.get('number-drone')
        
        # for each drone, get the model type
        drone_models = []
        for i in range(int(number_of_drones)):
            drone_models.append(request.form.get(f'drone-{i}-model'))
        
        mission_type = request.form.get('mission-type')

        
        if mission_type == 'autonomous':
            # get autonomous mission type
            autonomous_mission_type = request.form.get('autonomous-mission-type')
            model = request.form.get('model')
        elif mission_type == 'waypoint':
            # get waypoint file 
            waypoint_file = request.form['waypoint-file']
        else:
            # return error message
            return jsonify({"error": "Invalid mission type"}), 400

        # Run the script and capture the output
        result = subprocess.run(
            ['./launch.sh', number_of_drones, mission_type, waypoint_file, autonomous_mission_type, model],
            capture_output=True,
            text=True,
            check=True
        )

        # Process the output or return a response
        return jsonify({
            "message": f"Mission started with {number_of_drones} drones.",
            "mission_type": mission_type,
            "script_output": result.stdout
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Script failed with error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)