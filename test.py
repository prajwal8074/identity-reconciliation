import unittest
import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class TestBitespeedAPI(unittest.TestCase):
    
    BASE_URL = "http://127.0.0.1:3000/identify"
    
    def get_db_connection(self):
        return psycopg2.connect(os.environ['DATABASE_URL'])

    def setUp(self):
        # clean the database before each test
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Contact;")
        conn.commit()
        cursor.close()
        conn.close()

    def test_01_new_contact_creation(self):
        """first time user, should create a primary contact."""
        payload = {"email": "doc@delorean.com", "phoneNumber": "12345"}
        response = requests.post(self.BASE_URL, json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()['contact']
        
        self.assertEqual(len(data['secondaryContactIds']), 0)
        self.assertIn("doc@delorean.com", data['emails'])
        self.assertIn("12345", data['phoneNumbers'])
    
    def test_02_secondary_contact_creation(self):
        """existing email, new phone."""
        # initial req
        first_res = requests.post(self.BASE_URL, json={"email": "mcfly@u.edu", "phoneNumber": "111"})
        initial_primary_id = first_res.json()['contact']['primaryContatctId']
        
        # same email, different phone
        payload = {"email": "mcfly@u.edu", "phoneNumber": "222"}
        response = requests.post(self.BASE_URL, json=payload)
        
        data = response.json()['contact']
        self.assertEqual(data['primaryContatctId'], initial_primary_id)
        self.assertEqual(len(data['secondaryContactIds']), 1)
        self.assertEqual(data['secondaryContactIds'][0], initial_primary_id+1)
        self.assertIn("111", data['phoneNumbers'])
        self.assertIn("222", data['phoneNumbers'])
        
    def test_03_primary_to_secondary_merge(self):
        """Scenario: Merging two existing primary accounts. Older should prevail."""
        # create primary A
        res_a = requests.post(self.BASE_URL, json={"email": "george@u.edu", "phoneNumber": "999"})
        id_a = res_a.json()['contact']['primaryContatctId']
        
        # create primary B
        res_b = requests.post(self.BASE_URL, json={"email": "biff@u.edu", "phoneNumber": "888"})
        id_b = res_b.json()['contact']['primaryContatctId']
        
        # merge request
        payload = {"email": "george@u.edu", "phoneNumber": "888"}
        response = requests.post(self.BASE_URL, json=payload)
        
        data = response.json()['contact']
        # the older ID (id_a) must be the primaryContatctId
        self.assertEqual(data['primaryContatctId'], id_a)
        # the newer ID (id_b) should now be in the secondary list
        self.assertIn(id_b, data['secondaryContactIds'])

if __name__ == '__main__':
    unittest.main()
