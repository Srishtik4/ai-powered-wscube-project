import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import json

# Gemini API Configuration
# Get API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "AIzaSyDjJ5QOOVpEKhpB9muYpCD31lk7D71UCDU"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

def get_career_recommendations(preferences):
    """Generate AI-powered career recommendations based on preferences using Gemini API"""
    
    # Create prompt with user preferences
    prompt = f"""
    Based on the following preferences, recommend 3-5 tech career paths:
    - Technical Interests: {preferences.get('interests', '')}
    - Strengths: {preferences.get('strengths', '')}
    - Work Style: {preferences.get('work_style', '')}
    - Preferred Environment: {preferences.get('environment', '')}
    - Long-term Goals: {preferences.get('goals', '')}
    
    For each career path, provide:
    1. Title (a specific job title)
    2. Brief description
    3. List of 3-5 Key skills required
    4. Specific potential salary range (with actual dollar figures)
    5. Clear growth prospects description

    Format as plain text without headings like "Here are X tech career paths" or "Key Skills:"
    """
    
    # Prepare request data for Gemini API
    request_data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    # Use urllib from standard library
    try:
        # Add API key to URL
        url_with_key = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        # Create request
        data = json.dumps(request_data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add debug output
        print(f"Sending request to Gemini API...")
        print(f"URL: {GEMINI_API_URL}")
        print(f"Headers: {headers}")
        print(f"Request data: {request_data}")
        
        # Build and make request
        req = urllib.request.Request(url_with_key, data=data, headers=headers, method='POST')
        
        # Allow for self-signed certificates (if needed)
        context = ssl._create_unverified_context()
        
        # Get response
        with urllib.request.urlopen(req, context=context) as response:
            response_content = response.read()
            print(f"Response status: {response.status}")
            print(f"Response content: {response_content.decode('utf-8')}")
            
            response_data = json.loads(response_content.decode('utf-8'))
            # Extract the text from Gemini's response structure
            recommendations_text = response_data['candidates'][0]['content']['parts'][0]['text']
            print(f"Extracted text: {recommendations_text}")
            
            # Parse the response text and create structured recommendations
            career_paths = parse_recommendations(recommendations_text)
            
            # If we successfully parsed recommendations, return them
            if career_paths:
                print(f"Parsed career paths: {career_paths}")
                return career_paths
            else:
                print("Failed to parse career paths, using fallback")
                return get_fallback_recommendations()
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return get_fallback_recommendations()

def parse_recommendations(text):
    """Parse the AI response into structured career recommendations"""
    try:
        # This is a simple parsing implementation - you may need to adjust based on 
        # the actual format returned by the AI model
        career_paths = []
        
        # Split by numbered items (looking for "1.", "2.", etc.)
        import re
        careers_text = re.split(r'\d+\.', text)
        # Remove empty strings
        careers_text = [c for c in careers_text if c.strip()]
        
        for i, career_text in enumerate(careers_text):
            lines = career_text.strip().split('\n')
            # First line should be the title
            if not lines:
                continue
                
            title = lines[0].strip()
            description = ""
            skills = []
            salary_range = ""
            growth_prospects = ""
            
            for line in lines[1:]:
                line = line.strip()
                if line.lower().startswith("description") or ":" in line and "description" in line.lower().split(":")[0]:
                    description = line.split(":", 1)[1].strip() if ":" in line else ""
                elif line.lower().startswith("skills") or "skills" in line.lower():
                    skills_text = line.split(":", 1)[1].strip() if ":" in line else ""
                    skills = [s.strip() for s in skills_text.split(",")]
                elif line.lower().startswith("salary") or "salary" in line.lower():
                    salary_range = line.split(":", 1)[1].strip() if ":" in line else ""
                elif line.lower().startswith("growth") or "growth" in line.lower():
                    growth_prospects = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # Skip entries that match the unwanted pattern
            if not skills and salary_range == "Varies by location and experience" and growth_prospects == "Contact a career advisor for details":
                continue
                
            # Generate an ID from the title
            career_id = title.lower().replace(" ", "-")
            
            # Ensure we have valid values for all fields
            if not salary_range:
                salary_range = "$75,000 - $120,000 depending on location and experience"
            if not growth_prospects:
                growth_prospects = "Positive outlook with 15% projected growth over the next 5 years"
            if not skills:
                skills = ["Technical expertise", "Problem solving", "Communication"]
                
            career_paths.append({
                "id": career_id,
                "title": title,
                "description": description,
                "skills": skills[:3], # Take first 3 skills
                "salary_range": salary_range,
                "growth_prospects": growth_prospects
            })
        
        return career_paths
    except Exception as e:
        print(f"Error parsing recommendations: {e}")
        return []

def get_fallback_recommendations():
    """Return hardcoded recommendations in case of API failure"""
    print("Using fallback recommendations")
    return [
        {
            "id": "software-development",
            "title": "Software Development",
            "description": "Design and build computer programs and applications.",
            "skills": ["Programming", "Problem Solving", "Software Design"],
            "salary_range": "$70,000 - $150,000",
            "growth_prospects": "Strong growth expected across industries"
        },
        {
            "id": "data-science",
            "title": "Data Science",
            "description": "Extract insights and knowledge from structured and unstructured data.",
            "skills": ["Statistics", "Machine Learning", "Python/R"],
            "salary_range": "$85,000 - $165,000",
            "growth_prospects": "High demand as organizations become more data-driven"
        },
        {
            "id": "devops",
            "title": "DevOps Engineering",
            "description": "Bridge development and operations to improve deployment efficiency.",
            "skills": ["CI/CD", "Cloud Platforms", "Infrastructure as Code"],
            "salary_range": "$80,000 - $160,000",
            "growth_prospects": "Rapidly growing field as companies adopt cloud technologies"
        }
    ]

def get_career_details(career_id):
    """Get detailed information about a specific career path using Gemini API"""
    
    # First check if we have it in our database
    careers_database = {
        "software-development": {
            "title": "Software Development",
            "description": "Software developers design, build, and maintain computer programs and applications that enable users to perform specific tasks on computers or other devices.",
            "roadmap": [
                "Learn programming fundamentals (Python, JavaScript)",
                "Build projects to apply your skills",
                "Learn about data structures and algorithms",
                "Familiarize yourself with development methodologies",
                "Gain experience with databases and web technologies",
                "Specialize in front-end, back-end, or full-stack development"
            ],
            "required_skills": [
                "Programming languages (Python, JavaScript, Java, etc.)",
                "Data structures and algorithms",
                "Version control (Git)",
                "Problem-solving skills",
                "Software design patterns",
                "Database management"
            ],
            "opportunities": [
                "Web Developer",
                "Mobile App Developer",
                "Game Developer",
                "Enterprise Software Developer",
                "Systems Programmer"
            ],
            "market_trends": "The software development field continues to grow with increasing demand for web and mobile applications. Remote work opportunities have expanded significantly.",
            "resources": [
                {"name": "freeCodeCamp", "url": "https://www.freecodecamp.org/"},
                {"name": "The Odin Project", "url": "https://www.theodinproject.com/"},
                {"name": "LeetCode", "url": "https://leetcode.com/"}
            ]
        },
        "data-science": {
            "title": "Data Science",
            "description": "Data scientists collect, analyze, and interpret large datasets to help organizations make better decisions.",
            "roadmap": [
                "Develop strong math and statistics foundation",
                "Learn programming (Python/R)",
                "Study data manipulation and visualization",
                "Learn machine learning algorithms",
                "Practice with real-world datasets",
                "Build a portfolio of data science projects"
            ],
            "required_skills": [
                "Statistics and probability",
                "Python or R programming",
                "Data visualization",
                "Machine learning",
                "SQL and database knowledge",
                "Domain expertise in your industry"
            ],
            "opportunities": [
                "Data Scientist",
                "Data Analyst",
                "Machine Learning Engineer",
                "Business Intelligence Analyst",
                "Quantitative Analyst"
            ],
            "market_trends": "Data science roles continue to be in high demand as companies leverage data for competitive advantage. Specialization in fields like NLP or computer vision is increasingly valuable.",
            "resources": [
                {"name": "Kaggle", "url": "https://www.kaggle.com/"},
                {"name": "DataCamp", "url": "https://www.datacamp.com/"},
                {"name": "Fast.ai", "url": "https://www.fast.ai/"}
            ]
        },
        "devops": {
            "title": "DevOps Engineering",
            "description": "DevOps engineers bridge software development and IT operations, automating and improving development and deployment processes.",
            "roadmap": [
                "Learn Linux fundamentals",
                "Understand networking basics",
                "Master a scripting language (Python, Bash)",
                "Learn version control and CI/CD",
                "Study cloud platforms (AWS, Azure, GCP)",
                "Learn infrastructure as code (Terraform, Ansible)"
            ],
            "required_skills": [
                "Linux/Unix administration",
                "Scripting languages",
                "Containerization (Docker, Kubernetes)",
                "CI/CD pipelines",
                "Cloud services",
                "Monitoring and logging"
            ],
            "opportunities": [
                "DevOps Engineer",
                "Site Reliability Engineer",
                "Cloud Engineer",
                "Infrastructure Engineer",
                "Platform Engineer"
            ],
            "market_trends": "DevOps practices are becoming standard across the industry. Organizations are increasingly looking for professionals who can implement microservices architectures and manage cloud infrastructure.",
            "resources": [
                {"name": "Linux Academy", "url": "https://linuxacademy.com/"},
                {"name": "DevOps Roadmap", "url": "https://roadmap.sh/devops"},
                {"name": "KodeKloud", "url": "https://kodekloud.com/"}
            ]
        }
    }
    
    # If we have it in our database, return it
    if career_id in careers_database:
        return careers_database.get(career_id)
    
    # If not, generate career details using Gemini API
    try:
        # Create a prompt for the career details
        prompt = f"""
        Generate detailed information about the "{career_id.replace('-', ' ')}" career path in tech. Include:
        
        1. A comprehensive description (2-3 paragraphs)
        2. A learning roadmap (6 steps)
        3. Required skills (6 key skills)
        4. Job opportunities (5 specific roles)
        5. Market trends (1 paragraph)
        6. Learning resources (3 specific resources with names and URLs)
        
        Format as a structured JSON object with these keys: title, description, roadmap (array), 
        required_skills (array), opportunities (array), market_trends, resources (array of objects with name and url).
        """
        
        # Prepare request data for Gemini API
        request_data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024
            }
        }
        
        # Add API key to URL
        url_with_key = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        # Create request
        data = json.dumps(request_data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Build and make request
        req = urllib.request.Request(url_with_key, data=data, headers=headers, method='POST')
        
        # Allow for self-signed certificates (if needed)
        context = ssl._create_unverified_context()
        
        # Get response
        with urllib.request.urlopen(req, context=context) as response:
            response_content = response.read()
            response_data = json.loads(response_content.decode('utf-8'))
            
            # Extract the text from Gemini's response structure
            career_details_text = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', career_details_text)
            if json_match:
                career_details_json = json_match.group(1)
            else:
                career_details_json = career_details_text
                
            # Parse the JSON
            career_details = json.loads(career_details_json)
            
            return career_details
            
    except Exception as e:
        print(f"Error generating career details: {e}")
        # Return a simple fallback with the career ID as title
        return {
            "title": career_id.replace('-', ' ').title(),
            "description": "Detailed information is not available for this career path.",
            "roadmap": ["Research online resources", "Take relevant courses", "Build projects", "Network with professionals", "Gain experience", "Apply for jobs"],
            "required_skills": ["Technical knowledge", "Problem solving", "Communication", "Teamwork", "Continuous learning", "Adaptability"],
            "opportunities": ["Entry-level positions", "Mid-level roles", "Senior positions", "Management", "Consulting"],
            "market_trends": "The field is growing with new opportunities emerging. Keep your skills current to stay competitive.",
            "resources": [
                {"name": "Online Tutorials", "url": "https://www.coursera.org/"},
                {"name": "Industry Publications", "url": "https://medium.com/"},
                {"name": "Professional Networks", "url": "https://www.linkedin.com/"}
            ]
        }

# Example usage
if __name__ == "__main__":
    test_preferences = {
        "interests": "programming, data analysis, cloud computing",
        "strengths": "problem solving, mathematics, communication",
        "work_style": "collaborative, detail-oriented",
        "environment": "startup, remote",
        "goals": "work on innovative projects, learn continuously"
    }
    
    print("Testing career recommendation functionality...")
    recommendations = get_career_recommendations(test_preferences)
    print(f"Recommendations: {json.dumps(recommendations, indent=2)}")