# combined_app.py - Integrated learning platform with career advisor
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
from datetime import datetime
from career_advisor import get_career_recommendations, get_career_details
from video_consultation import initialize_video_session

app = Flask(__name__)
app.secret_key = "wscube_integrated_platform_secret_key"

# File to store user data
DATA_FILE = "user_data.json"

# Initialize data if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def get_data():
    """Load data from JSON file"""
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Sample courses and content
COURSES = {
    "python": {
        "name": "Python Programming",
        "modules": [
            {"id": "py1", "name": "Python Basics", "difficulty": 1},
            {"id": "py2", "name": "Control Flow", "difficulty": 2},
            {"id": "py3", "name": "Functions", "difficulty": 3},
            {"id": "py4", "name": "Object-Oriented Programming", "difficulty": 4}
        ]
    },
    "web": {
        "name": "Web Development",
        "modules": [
            {"id": "web1", "name": "HTML Fundamentals", "difficulty": 1},
            {"id": "web2", "name": "CSS Styling", "difficulty": 2},
            {"id": "web3", "name": "JavaScript Basics", "difficulty": 3},
            {"id": "web4", "name": "Responsive Design", "difficulty": 4}
        ]
    }
}

# Badge definitions
BADGES = {
    "quick_learner": {"name": "Quick Learner", "description": "Complete 3 modules in a single day"},
    "night_owl": {"name": "Night Owl", "description": "Study between 10PM and 5AM"},
    "consistent": {"name": "Consistency King", "description": "Login for 5 consecutive days"},
    "perfectionist": {"name": "Perfectionist", "description": "Score 100% on any module quiz"},
    "helper": {"name": "Helpful Hero", "description": "Help 3 other students in forums"}
}

#
# LEARNING PLATFORM ROUTES
#
@app.route("/")
def index():
    """Home page"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    data = get_data()
    user_data = data.get(session["username"], {
        "points": 0,
        "badges": [],
        "completed_modules": [],
        "learning_style": None,
        "performance": {},
        "login_streak": 0,
        "last_login": None
    })
    
    # Update login streak
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data.get("last_login") != today:
        last_login = user_data.get("last_login")
        if last_login:
            last_date = datetime.strptime(last_login, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            day_diff = (today_date - last_date).days
            if day_diff == 1:
                user_data["login_streak"] += 1
            elif day_diff > 1:
                user_data["login_streak"] = 1
        else:
            user_data["login_streak"] = 1
        
        user_data["last_login"] = today
        
        # Check for consistency badge
        if user_data["login_streak"] >= 5 and "consistent" not in user_data["badges"]:
            user_data["badges"].append("consistent")
            user_data["points"] += 50
    
    # Check for night owl badge
    current_hour = datetime.now().hour
    if 22 <= current_hour or current_hour <= 5:
        if "night_owl" not in user_data["badges"]:
            user_data["badges"].append("night_owl")
            user_data["points"] += 30
    
    data[session["username"]] = user_data
    save_data(data)
    
    # Get leaderboard data
    leaderboard = []
    for username, udata in data.items():
        leaderboard.append({
            "username": username,
            "points": udata.get("points", 0),
            "badge_count": len(udata.get("badges", []))
        })
    
    leaderboard = sorted(leaderboard, key=lambda x: x["points"], reverse=True)[:10]
    recommendations = get_recommendations(user_data)  # Get recommended courses

    return render_template("index.html",
                           user_data=user_data,
                           courses=COURSES,
                           badges=BADGES,
                           leaderboard=leaderboard,
                           recommendations=recommendations)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Simple authentication - in a real app, you'd check credentials properly
        session["username"] = username
        
        # Initialize user if new
        data = get_data()
        if username not in data:
            data[username] = {
                "points": 0,
                "badges": [],
                "completed_modules": [],
                "learning_style": None,
                "performance": {},
                "login_streak": 0,
                "last_login": None
            }
            save_data(data)
        
        return redirect(url_for("index"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for("login"))

@app.route("/course/<course_id>")
def view_course(course_id):
    """View a specific course"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    if course_id not in COURSES:
        return redirect(url_for("index"))
    
    data = get_data()
    user_data = data.get(session["username"])
    
    return render_template("course.html", 
                           course=COURSES[course_id], 
                           user_data=user_data)

@app.route("/module/<module_id>")
def view_module(module_id):
    """View a specific module"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    # Find the module across all courses
    module_data = None
    parent_course = None
    
    for course_id, course in COURSES.items():
        for module in course["modules"]:
            if module["id"] == module_id:
                module_data = module
                parent_course = course
                break
        if module_data:
            break
    
    if not module_data:
        return redirect(url_for("index"))
    
    data = get_data()
    user_data = data.get(session["username"])
    
    # Use AI to adapt content based on learning style
    content = generate_adapted_content(module_data, user_data)
    
    return render_template("module.html", 
                           module=module_data,
                           course=parent_course,
                           content=content,
                           user_data=user_data)

@app.route("/complete_module/<module_id>", methods=["POST"])
def complete_module(module_id):
    """Mark a module as completed and award points"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    quiz_score = int(request.form.get("quiz_score", 0))
    time_spent = int(request.form.get("time_spent", 0))  # in minutes
    
    data = get_data()
    user_data = data.get(session["username"])
    
    # Find module difficulty
    module_difficulty = 1
    for course in COURSES.values():
        for module in course["modules"]:
            if module["id"] == module_id:
                module_difficulty = module["difficulty"]
                break
    
    # Award points based on performance and difficulty
    base_points = 10 * module_difficulty
    performance_multiplier = quiz_score / 100
    awarded_points = int(base_points * performance_multiplier)
    
    # Update user data
    if module_id not in user_data["completed_modules"]:
        user_data["completed_modules"].append(module_id)
    
    user_data["points"] += awarded_points
    user_data["performance"][module_id] = {
        "score": quiz_score,
        "time_spent": time_spent,
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Check for badges
    if quiz_score == 100 and "perfectionist" not in user_data["badges"]:
        user_data["badges"].append("perfectionist")
        user_data["points"] += 50
    
    # Check for quick learner badge
    today_completed = 0
    today = datetime.now().strftime("%Y-%m-%d")
    for module_perf in user_data["performance"].values():
        if module_perf["completed_at"].startswith(today):
            today_completed += 1
    
    if today_completed >= 3 and "quick_learner" not in user_data["badges"]:
        user_data["badges"].append("quick_learner")
        user_data["points"] += 40
    
    # Update learning style based on performance pattern
    user_data["learning_style"] = analyze_learning_style(user_data)
    
    data[session["username"]] = user_data
    save_data(data)
    
    return redirect(url_for("index"))

@app.route("/help_peer", methods=["POST"])
def help_peer():
    """Record when a user helps another student"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    data = get_data()
    user_data = data.get(session["username"])
    
    # Initialize help count if not exists
    if "help_count" not in user_data:
        user_data["help_count"] = 0
    
    user_data["help_count"] += 1
    user_data["points"] += 5  # Small reward for helping
    
    # Check for helper badge
    if user_data["help_count"] >= 3 and "helper" not in user_data["badges"]:
        user_data["badges"].append("helper")
        user_data["points"] += 30
    
    data[session["username"]] = user_data
    save_data(data)
    
    return redirect(url_for("index"))

#
# CAREER ADVISOR ROUTES
#
@app.route('/career_advisor')
def career_advisor():
    """Career advisor main page"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    return render_template('career_advisor_index.html')

@app.route('/assessment')
def assessment():
    """Career assessment page"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    return render_template('assessment.html')

@app.route('/recommendations', methods=['POST'])
def recommendations():
    """Process assessment and show career recommendations"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    preferences = request.form.to_dict()
    session['preferences'] = preferences
    
    career_paths = get_career_recommendations(preferences)
    session['recommendations'] = career_paths
    
    return render_template('recommendations.html', careers=career_paths)

@app.route('/career/<path>')
def career_details(path):
    """Show details for a specific career path"""
    if "username" not in session:
        return redirect(url_for("login"))
    
    career_info = get_career_details(path)
    return render_template('career_details.html', career=career_info)

@app.route('/schedule-consultation', methods=['POST'])
def schedule_consultation():
    """Schedule a video consultation"""
    if "username" not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    user_info = request.form.to_dict()
    user_info['username'] = session["username"]
    
    session_id = initialize_video_session(user_info)
    
    # Update user data to record consultation
    data = get_data()
    user_data = data.get(session["username"])
    
    if "consultations" not in user_data:
        user_data["consultations"] = []
    
    user_data["consultations"].append({
        "session_id": session_id,
        "scheduled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "career"
    })
    
    # Award points for taking initiative
    user_data["points"] += 25
    
    data[session["username"]] = user_data
    save_data(data)
    
    return jsonify({'session_id': session_id, 'status': 'scheduled'})

#
# HELPER FUNCTIONS
#
def generate_adapted_content(module, user_data):
    """
    AI function to generate personalized content based on user's learning style and performance
    In a real implementation, this would use ML models or APIs
    """
    learning_style = user_data.get("learning_style", "visual")
    difficulty_preference = calculate_difficulty_preference(user_data)
    
    # Basic content structure
    content = {
        "theory": f"Module theory content for {module['name']}",
        "examples": [],
        "exercises": [],
        "resources": []
    }
    
    # Adapt examples based on learning style
    if learning_style == "visual":
        content["examples"] = [
            "Visual diagram explaining " + module["name"],
            "Infographic about key concepts",
            "Video tutorial walkthrough"
        ]
    elif learning_style == "auditory":
        content["examples"] = [
            "Audio explanation of " + module["name"],
            "Discussion-based example",
            "Verbal step-by-step process"
        ]
    elif learning_style == "kinesthetic":
        content["examples"] = [
            "Interactive exercise for " + module["name"],
            "Hands-on project example",
            "Practice-based learning activity"
        ]
    else:  # Reading/writing or default
        content["examples"] = [
            "Detailed text explanation of " + module["name"],
            "Written case study example",
            "Reference documentation with examples"
        ]
    
    # Adapt difficulty of exercises
    base_exercises = [
        {"title": "Basic application", "difficulty": 1},
        {"title": "Intermediate challenge", "difficulty": 2},
        {"title": "Advanced problem", "difficulty": 3}
    ]
    
    # Filter exercises based on calculated difficulty preference
    content["exercises"] = [ex for ex in base_exercises 
                           if abs(ex["difficulty"] - difficulty_preference) <= 1]
    
    # Add extra practice for struggling students
    module_id = module["id"]
    if module_id in user_data.get("performance", {}) and user_data["performance"][module_id]["score"] < 70:
        content["exercises"].append({
            "title": "Extra practice exercise", 
            "difficulty": 1,
            "note": "Additional practice to reinforce concepts"
        })
    
    # Add advanced tasks for high achievers
    high_achiever = is_high_achiever(user_data)
    if high_achiever:
        content["exercises"].append({
            "title": "Expert challenge", 
            "difficulty": 4,
            "note": "For advanced students looking for a challenge"
        })
    
    # Adapt resources
    content["resources"] = generate_resources(module, learning_style, difficulty_preference)
    
    return content

def analyze_learning_style(user_data):
    """
    Analyze user performance data to determine learning style
    This is a simplified approximation - a real implementation would use ML
    """
    # In a real implementation, this would analyze:
    # - Time spent on different types of content
    # - Quiz performance on different question types
    # - Explicit style preferences
    
    # For this demo, we'll determine randomly but weighted by past performance
    styles = ["visual", "auditory", "kinesthetic", "reading"]
    
    # Default weights
    weights = [0.25, 0.25, 0.25, 0.25]
    
    # If we have performance data, adjust weights
    if user_data.get("performance"):
        # Just a placeholder for real logic
        # In reality, you'd analyze which content types led to better scores
        fast_modules = 0
        for perf in user_data["performance"].values():
            if perf["time_spent"] < 15 and perf["score"] > 80:
                fast_modules += 1
        
        if fast_modules > len(user_data["performance"]) / 2:
            # User performs well on quick modules - might be visual
            weights = [0.4, 0.2, 0.2, 0.2]
    
    # Return weighted random choice
    return random.choices(styles, weights=weights, k=1)[0]

def get_recommendations(user_data):
    """Generate personalized course recommendations."""
    recommendations = []
    
    # Identify user's learning style and performance
    learning_style = user_data.get("learning_style", "visual")
    avg_score = 0
    if user_data.get("performance"):
        avg_score = sum(perf["score"] for perf in user_data.get("performance", {}).values()) / len(user_data.get("performance"))
    else:
        avg_score = 70
    
    # Recommend courses based on learning style
    if learning_style == "visual":
        recommendations.append("Data Visualization with Python")
        recommendations.append("UX/UI Design Fundamentals")
    elif learning_style == "auditory":
        recommendations.append("Podcasting and Audio Editing")
        recommendations.append("Public Speaking Mastery")
    elif learning_style == "kinesthetic":
        recommendations.append("Arduino & IoT Hands-on Projects")
        recommendations.append("Game Development with Unity")
    else:
        recommendations.append("Technical Writing & Documentation")
        recommendations.append("Academic Research & Essay Writing")
    
    # Adjust recommendations based on performance
    if avg_score > 85:
        recommendations.append("Advanced Machine Learning")
        recommendations.append("Cybersecurity & Ethical Hacking")
    elif avg_score < 60:
        recommendations.append("Intro to Problem-Solving with Python")
        recommendations.append("Basic Web Development Bootcamp")
    
    # Add related courses based on completed modules
    completed_modules = user_data.get("completed_modules", [])
    if "py3" in completed_modules:  # If user completed Python Functions
        recommendations.append("Intermediate Python Projects")
    if "web3" in completed_modules:  # If user completed JavaScript Basics
        recommendations.append("React.js for Beginners")
    
    return list(set(recommendations))  # Remove duplicates

def calculate_difficulty_preference(user_data):
    """Calculate user's preferred difficulty level based on performance"""
    if not user_data.get("performance"):
        return 2  # Default medium difficulty
    
    total_score = 0
    module_count = 0
    
    for module_id, perf in user_data["performance"].items():
        total_score += perf["score"]
        module_count += 1
    
    if module_count == 0:
        return 2
    
    avg_score = total_score / module_count
    
    if avg_score > 90:
        return 3  # Higher difficulty
    elif avg_score > 70:
        return 2  # Medium difficulty
    else:
        return 1  # Lower difficulty

def is_high_achiever(user_data):
    """Determine if user is a high achiever who should get advanced content"""
    if not user_data.get("performance"):
        return False
    
    high_scores = 0
    for perf in user_data["performance"].values():
        if perf["score"] > 90:
            high_scores += 1
    
    return high_scores >= 3 or high_scores >= len(user_data["performance"]) * 0.7

def generate_resources(module, learning_style, difficulty):
    """Generate tailored additional resources"""
    resources = []
    
    # Base resources by difficulty
    if difficulty <= 1:
        resources.append("Beginner's guide to " + module["name"])
    if difficulty == 2:
        resources.append("Intermediate " + module["name"] + " concepts")
    if difficulty >= 3:
        resources.append("Advanced " + module["name"] + " techniques")
    
    # Learning style specific resources
    if learning_style == "visual":
        resources.append("Video tutorial series")
        resources.append("Illustrated guide")
    elif learning_style == "auditory":
        resources.append("Podcast explaining concepts")
        resources.append("Recorded lecture series")
    elif learning_style == "kinesthetic":
        resources.append("Interactive practice environment")
        resources.append("Hands-on project ideas")
    else:  # Reading/writing
        resources.append("Comprehensive textbook chapter")
        resources.append("Written tutorial with examples")
    
    return resources

if __name__ == "__main__":
    app.run(debug=True)