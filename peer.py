import json
from Blockchain import Blockchain
from Block import Block
from flask import Flask, request

app = Flask(__name__)
blockchain = Blockchain()
peers = []

@app.route("/new_transaction", methods=["POST"])
def new_transaction():
    file_data = request.get_json()
    required_fields = ["user", "v_file", "file_data", "file_size"]
    for field in required_fields:
        if not file_data.get(field):
            return "Transaction does not have valid fields!", 404

    # Add the transaction data to the pending transactions
    blockchain.add_pending(file_data)

    return "Success", 201

@app.route("/mine", methods=["GET"])
def mine_uncofirmed_transactions():
    result = blockchain.mine()
    if result:
        return f"Block #{result} mined successfully."
    else:
        return "No pending transactions to mine."

@app.route("/chain", methods=["GET"])
def get_chain():
    chain = []
    for block in blockchain.chain:
        chain.append(block.__dict__)
    return json.dumps({"length": len(chain), "chain": chain})

@app.route("/pending_tx")
def get_pending_tx():
    return json.dumps(blockchain.pending)

@app.route("/add_block", methods=["POST"])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"], block_data["transactions"], block_data["prev_hash"])
    hashl = block_data["hash"]
    added = blockchain.add_block(block, hashl)
    if not added:
        return "The Block was discarded by the node.", 400
    return "The block was added to the chain.", 201

app.run(port=8800, debug=True)
