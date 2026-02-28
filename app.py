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
        # check for exact matches, ignoring nulls
        cursor.execute("""
            SELECT * FROM Contact 
            WHERE (email = %s AND %s IS NOT NULL) 
               OR (phoneNumber = %s AND %s IS NOT NULL)
        """, (email, email, phone_number, phone_number))
        
        matches = cursor.fetchall()

        # new customer
        if not matches:
            cursor.execute("""
                INSERT INTO Contact (email, phoneNumber, linkPrecedence)
                VALUES (%s, %s, 'primary')
                RETURNING id, email, phoneNumber;
            """, (email, phone_number))
            new_contact = cursor.fetchone()
            conn.commit()

            return jsonify({
                "contact": {
                    "primaryContatctId": new_contact['id'],
                    "emails": [new_contact['email']] if new_contact['email'] else [],
                    "phoneNumbers": [new_contact['phonenumber']] if new_contact['phonenumber'] else [],
                    "secondaryContactIds": []
                }
            }), 200

        # exact match or overlap found
        # find root
        primary_ids = set()
        for row in matches:
            if row['linkprecedence'] == 'primary':
                primary_ids.add(row['id'])
            else:
                primary_ids.add(row['linkedid'])

        cursor.execute("""
            SELECT * FROM Contact 
            WHERE id = ANY(%s) OR linkedId = ANY(%s)
            ORDER BY createdAt ASC
        """, (list(primary_ids), list(primary_ids)))
        cluster = cursor.fetchall()
        
        primaries = [c for c in cluster if c['linkprecedence'] == 'primary']
        target_primary = primaries[0] if primaries else cluster[0]
        target_primary_id = target_primary['id']

        # merge primaries
        other_primary_ids = [p['id'] for p in primaries[1:]]
        if other_primary_ids:
            # downgrade newer primaries to secondary
            cursor.execute("""
                UPDATE Contact 
                SET linkPrecedence = 'secondary', linkedId = %s, updatedAt = CURRENT_TIMESTAMP
                WHERE id = ANY(%s)
            """, (target_primary_id, other_primary_ids))
            
            # repoint any secondaries that were pointing to the downgraded primaries
            cursor.execute("""
                UPDATE Contact 
                SET linkedId = %s, updatedAt = CURRENT_TIMESTAMP
                WHERE linkedId = ANY(%s)
            """, (target_primary_id, other_primary_ids))

        # check if incoming request has new information
        cluster_emails = set(c['email'] for c in cluster if c['email'])
        cluster_phones = set(c['phonenumber'] for c in cluster if c['phonenumber'])

        # if not a complete duplicate, insert a secondary record
        if (email and email not in cluster_emails) or (phone_number and phone_number not in cluster_phones):
            cursor.execute("""
                INSERT INTO Contact (email, phoneNumber, linkedId, linkPrecedence)
                VALUES (%s, %s, %s, 'secondary')
            """, (email, phone_number, target_primary_id))

        conn.commit()

        # final response
        cursor.execute("""
            SELECT * FROM Contact 
            WHERE id = %s OR linkedId = %s
            ORDER BY createdAt ASC
        """, (target_primary_id, target_primary_id))
        final_cluster = cursor.fetchall()

        emails_list = []
        phones_list = []
        secondary_ids = []

        # ensure target_primary details appear first in the arrays
        if target_primary['email']: emails_list.append(target_primary['email'])
        if target_primary['phonenumber']: phones_list.append(target_primary['phonenumber'])

        for row in final_cluster:
            if row['email'] and row['email'] not in emails_list:
                emails_list.append(row['email'])
            if row['phonenumber'] and row['phonenumber'] not in phones_list:
                phones_list.append(row['phonenumber'])
            if row['id'] != target_primary_id:
                secondary_ids.append(row['id'])

        return jsonify({
            "contact": {
                "primaryContatctId": target_primary_id,
                "emails": emails_list,
                "phoneNumbers": phones_list,
                "secondaryContactIds": secondary_ids
            }
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
