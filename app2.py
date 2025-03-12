from flask import Flask, render_template, request, jsonify, session
import json
from career_advisor import get_career_recommendations, get_career_details
from video_consultation import initialize_video_session

app = Flask(__name__)
app.secret_key = 'wscube_career_mapper_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assessment')
def assessment():
    return render_template('assessment.html')

@app.route('/recommendations', methods=['POST'])
def recommendations():
    preferences = request.form.to_dict()
    session['preferences'] = preferences
    
    career_paths = get_career_recommendations(preferences)
    session['recommendations'] = career_paths
    
    return render_template('recommendations.html', careers=career_paths)

@app.route('/career/<path>')
def career_details(path):
    career_info = get_career_details(path)
    return render_template('career_details.html', career=career_info)

@app.route('/schedule-consultation', methods=['POST'])
def schedule_consultation():
    user_info = request.form.to_dict()
    session_id = initialize_video_session(user_info)
    return jsonify({'session_id': session_id, 'status': 'scheduled'})

if __name__ == '__main__':
    app.run(debug=True)