import json
import os
import requests
from flask import render_template, redirect, request, send_file, flash, abort
from werkzeug.utils import secure_filename
from app import app
from timeit import default_timer as timer

# Stores all the post transaction in the node
request_tx = []
# Store filename
files = {}
# Destination for upload files
UPLOAD_FOLDER = "app/static/Uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Store address
ADDR = "http://127.0.0.1:8800"

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def get_tx_req():
    global request_tx
    chain_addr = "{0}/chain".format(ADDR)
    resp = requests.get(chain_addr)
    if resp.status_code == 200:
        content = []
        chain = json.loads(resp.content.decode())
        for block in chain["chain"]:
            for trans in block["transactions"]:
                trans["index"] = block["index"]
                trans["hash"] = block["prev_hash"]
                content.append(trans)
        request_tx = sorted(content, key=lambda k: k["hash"], reverse=True)


@app.route("/")
def index():
    get_tx_req()
    return render_template("index.html", title="FileStorage", subtitle="A Decentralized Network for File Storage/Sharing",
                           node_address=ADDR, request_tx=request_tx)


@app.route("/submit", methods=["POST"])
def submit():
    start = timer()
    user = request.form["user"]
    up_file = request.files["v_file"]
    
    # Define the destination folder
    destination_folder = os.path.join(app.root_path, "static", "Uploads")
    
    # Create the destination folder if it doesn't exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Save the uploaded file in the destination folder
    filename = secure_filename(up_file.filename)
    file_path = os.path.join(destination_folder, filename)
    up_file.save(file_path)

    # Split the file into chunks
    chunk_size = 1024 * 1024  # 1MB
    chunk_paths = []
    with open(file_path, 'rb') as f:
        chunk_number = 0
        while True:
            chunk_data = f.read(chunk_size)
            if not chunk_data:
                break
            
            # Save the chunk to a separate file
            chunk_filename = f"{filename}_chunk_{chunk_number}"
            chunk_file_path = os.path.join(destination_folder, chunk_filename)
            with open(chunk_file_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            
            # Add the chunk file path to the list
            chunk_paths.append(chunk_file_path)
            
            chunk_number += 1

    # Add each chunk as a transaction to the blockchain
    for chunk_path in chunk_paths:
        with open(chunk_path, 'rb') as chunk_file:
            chunk_data = chunk_file.read()
            file_size = os.path.getsize(chunk_path)
            post_object = {
                "user": user,
                "v_file": chunk_filename,
                "file_data": str(chunk_data),
                "file_size": file_size
            }
            address = f"{ADDR}/new_transaction"
            requests.post(address, json=post_object)

    # Flash a message to display an alert
    flash("File was uploaded. Mine the block to make it visible on the chain.")
    files[up_file.filename] = os.path.join(app.root_path, "static" , "Uploads", up_file.filename)
    
    end = timer()
    print(end - start)
    return redirect("/")



@app.route("/submit/<string:variable>", methods=["GET"])
def download_file(variable):
    print("files: ", files)
    try:
        file_key = variable.split("_chunk_0")[0] if "_chunk_" in variable else variable
        file_path = files[file_key]
        return send_file(file_path, as_attachment=True)
    except:
        abort(404)

