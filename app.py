import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

@app.route('/identify', methods=['POST'])
def identify():
    data = request.get_json()
    
    email = data.get('email')
    phone_number = data.get('phoneNumber')
    
    if not email and not phone_number:
        return jsonify({"error": "Missing contact info"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # just insert everything as a new primary contact.
        insert_query = """
            INSERT INTO Contact (email, phoneNumber, linkPrecedence)
            VALUES (%s, %s, 'primary')
            RETURNING id, email, phoneNumber;
        """
        # convert phone_number to string if passed as an integer
        cursor.execute(insert_query, (email, str(phone_number) if phone_number else None))
        new_row = cursor.fetchone()
        conn.commit()

        response = {
            "contact": {
                "primaryContatctId": new_row['id'],
                "emails": [new_row['email']] if new_row['email'] else [],
                "phoneNumbers": [new_row['phonenumber']] if new_row['phonenumber'] else [],
                "secondaryContactIds": []
            }
        }
        
        return jsonify(response), 200

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
