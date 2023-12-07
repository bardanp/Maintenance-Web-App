"""
Author: Bardan Phuyel
E-mail: bvp5359@psu.edu
Course: CMPSC 487W
Assignment: Project 3
Due date: 12/6/2023
File: main.py
Purpose: Python application that handles Flask, Firebase Database
and Firebase Storage. The web-app allows users to submit maintenance requests,
staff to view and update requests, and staff to manage tenants.
Reference(s):
1. Flask Documentation: https://flask.palletsprojects.com/en/2.1.x/
2. Firebase Admin SDK: https://firebase.google.com/docs/admin/setup
3. Python Datetime: https://docs.python.org/3/library/datetime.html
4. Firestore Querying Data: https://firebase.google.com/docs/firestore/query-data/queries
5. Flask Request Object: https://flask.palletsprojects.com/en/2.1.x/api/#incoming-request-data
6. Python String Methods: https://docs.python.org/3/library/stdtypes.html#string-methods
7. Flask URL Building: https://flask.palletsprojects.com/en/2.1.x/quickstart/#url-building
8. Python sys library: https://docs.python.org/3/library/sys.html
9. Flask Mega-Tutorial: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
10. https://realpython.com/flask-by-example-part-1-project-setup/
11. https://flask.palletsprojects.com/en/2.1.x/tutorial/views/
"""
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import uuid

# Firebase Initialization
cred = credentials.Certificate('firebaseKey.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'proj3-ff6e0.appspot.com'
})
FirebaseDB = firestore.client()
FirebaseBucket = storage.bucket()

# Flask Initialization
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Routes for home page/login page
@app.route('/')
def index():
    return render_template('index.html')

# Called whenever the user inputs information to amke a new maintenance request and submits it, it will
# update firebase and update the table below
@app.route('/submit-request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        optionalImageFile = request.files.get('optionalImageFile')
        requestData = {
            "request_id": str(uuid.uuid4()),
            "apartment_number": request.form['apartment_number'],
            "problem_area": request.form['problem_area'],
            "description": request.form['description'],
            "date_time": datetime.utcnow().isoformat(),
            "status": "pending",
            "photo_url": None
        }
        # if there is a optionalImageFile, uplaod it to firebase bucket and set the image url
        if optionalImageFile:
            filename = f"{requestData['request_id']}_{optionalImageFile.filename}"
            bucketBlob = FirebaseBucket.blob(filename)
            bucketBlob.upload_from_file(optionalImageFile, content_type=optionalImageFile.content_type)
            requestData["photo_url"] = bucketBlob.public_url

        FirebaseDB.collection('maintenance_requests').document(requestData['request_id']).set(requestData)
        return redirect(url_for('index'))
    return render_template('submit_request.html')

# Called whenever the user wants to search for a maintenance request by name, apartment number, or problem area
@app.route('/view-requests', methods=['GET'])
def view_requests():
    searchInput = request.args.get('search', '').lower()
    requestsFromFirebase = FirebaseDB.collection('maintenance_requests').stream()
    requestsAfterFilter = []
    for doc in requestsFromFirebase:
        doc_dict = doc.to_dict()
        if any(searchInput in str(value).lower() for value in doc_dict.values()):
            requestsAfterFilter.append(doc_dict)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(requestsAfterFilter)
    return render_template('view_requests.html', requests=requestsAfterFilter, search_query=searchInput)

# Called whenever the user wants to manage tenants, it will redirect to the manage_tenants.html page
# and display all the tenants in the database
@app.route('/manage-tenants')
def manage_tenants():
    tenantsFromFirebase = FirebaseDB.collection('tenants').stream()
    allTenants = [doc.to_dict() for doc in tenantsFromFirebase]
    return render_template('manage_tenants.html', tenants=allTenants)

# called whenever the user wants to update a maintenance request from pending to completed
# it will update the database and redirect to the view_requests.html page
@app.route('/update-request/<request_id>', methods=['POST'])
def update_request(request_id):
    FirebaseDB.collection('maintenance_requests').document(request_id).update({"status": "completed"})
    return redirect(url_for('view_requests'))

# called whenever the manager wants to add a tenant to the database
# it will update the database and redirect to the manage_tenants.html page
@app.route('/add-tenant', methods=['POST'])
def add_tenant():
    tenant_data = {
        "tenant_id": request.form['tenant_id'],
        "name": request.form['name'],
        "phone_number": request.form['phone_number'],
        "email": request.form['email'],
        "check_in_date": request.form['check_in_date'],
        "check_out_date": request.form['check_out_date'],
        "apartment_number": request.form['apartment_number']
    }
    FirebaseDB.collection('tenants').document(tenant_data['tenant_id']).set(tenant_data)
    return redirect(url_for('manage_tenants'))

# called whenever the manager wants to delete a tenant from the database
# it will update the database and redirect to the manage_tenants.html page
@app.route('/delete-tenant/<tenant_id>', methods=['POST', 'DELETE'])
def delete_tenant(tenant_id):
    if request.method in ['POST', 'DELETE']:
        # Check if the tenant exists
        tenantsFromFirebase = FirebaseDB.collection('tenants').document(tenant_id)
        allTenants = tenantsFromFirebase.get()
        if allTenants.exists:
            tenantsFromFirebase.delete()
    return redirect(url_for('manage_tenants'))

# called whenever the manager wants to move a tenant to a different apartment number
# it will update the database and redirect to the manage_tenants.html page
@app.route('/move-tenant/<tenant_id>', methods=['POST'])
def move_tenant(tenant_id):
    newAptNumber = request.form.get('new_apartment_number')
    if newAptNumber:
        tenantsFromFirebase = FirebaseDB.collection('tenants').document(tenant_id)
        tenant_doc = tenantsFromFirebase.get()
        if not tenant_doc.exists:
            return jsonify(message='Tenant not found', isError=True)
        else:
            tenantsFromFirebase.update({"apartment_number": newAptNumber})
            return jsonify(message='Tenant moved successfully', isError=False)
    return jsonify(message='Tenant not found', isError=True)

@app.route('/tenant_login', methods=['POST'])
def tenant_login():
    tenant_id = request.form['tenant_id']
    tenant = FirebaseDB.collection('tenants').document(tenant_id).get()
    if tenant.exists:
        return redirect(url_for('submit_request'))
    else:
        flash('Tenant ID does not exist.', 'error')
        return redirect(url_for('index'))

@app.route('/staff_login', methods=['POST'])
def staff_login():
    staff_pin = request.form['staff_pin']
    if staff_pin == 'staff' or staff_pin == 'manager':
        return redirect(url_for('view_requests'))
    else:
        flash('Incorrect Staff Pin.', 'error')
        return redirect(url_for('index'))

@app.route('/manager_login', methods=['POST'])
def manager_login():
    manager_pin = request.form['manager_pin']
    if manager_pin == 'manager':
        return redirect(url_for('manage_tenants'))
    else:
        flash('Incorrect Manager Pin.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
