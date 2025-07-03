import os
import warnings
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Suppress warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

try:
    from main import PersonalHealthAssistant
    pha = PersonalHealthAssistant(openai_key=os.getenv("OPENROUTER_API_KEY"))
except ImportError as e:
    print(f"Backend initialization error: {str(e)}")
    pha = None

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user_id = pha.register_user(data)
        return jsonify({"success": True, "user_id": user_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/add_medication', methods=['POST'])
def add_medication():
    try:
        data = request.get_json()
        med_id = pha.add_medication(data['user_id'], data['med_data'])
        return jsonify({"success": True, "med_id": med_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/log_food', methods=['POST'])
def log_food():
    try:
        data = request.get_json()
        food_id = pha.log_food(data['user_id'], data['food_data'])
        return jsonify({"success": True, "food_id": food_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        report_path = pha.generate_health_report(data['user_id'])
        return jsonify({"success": True, "report_path": report_path})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.get_json()
        response = pha.chat(data['message'])
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    required_vars = ['OPENROUTER_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if not missing_vars:
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print(f"Missing environment variables: {missing_vars}")