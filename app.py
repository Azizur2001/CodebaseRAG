# Main
from flask import Flask, render_template, request, jsonify
from rag_pipeline import perform_rag

app = Flask(__name__, static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()  # Receive JSON payload
    query = data.get("query")  # Extract the query parameter
    if not query:
        return jsonify({"response": "Please provide a valid question."})

    # Call perform_rag to get the response
    response = perform_rag(query)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)



# from flask import Flask, render_template, request, jsonify
# from codebase_rag import perform_rag

# app = Flask(__name__, static_folder="static")

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     query = data.get("query")
#     codebase = data.get("codebase")

#     if not query:
#         return jsonify({"response": "Error: Query cannot be empty."})
#     if not codebase:
#         return jsonify({"response": "Error: Codebase not selected."})

#     # Pass query and codebase namespace to perform_rag
#     response = perform_rag(query)
#     return jsonify({"response": response})

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5001)
