from transformers import MarianMTModel, MarianTokenizer
from helpers import generate_uuid
from flask import jsonify, request, Response
from queries import queryEnrichableDescriptions, updateEnrichableDescriptions

tokenizer = MarianTokenizer.from_pretrained("/data/tokenizer")
model = MarianMTModel.from_pretrained("/data/model", torch_dtype="auto")

@app.route("/translate/", methods=["GET"])
def translate():
    prompts = [">>en<< {}".format(request.args.get('source'))]
    tokenized = tokenizer(prompts, return_tensors="pt", padding=True)
    translated = model.generate(**tokenized)

    return jsonify({
        "id": generate_uuid(),
        "type": "translations",
        "attributes": {
            "target": tokenizer.decode(translated[0], skip_special_tokens=True),
            "source": request.args.get("source") }
    })

@app.route("/delta/", methods=["POST"])
def delta():
    query_results = queryEnrichableDescriptions()

    if query_results:
        source_strings = [f">>en<< {string}" for (_thing, string) in query_results]
        source_uris = [thing for (thing, _string) in query_results]

        tokenized = tokenizer(source_strings, return_tensors="pt", padding=True)
        translated = model.generate(**tokenized)
        decoded = [tokenizer.decode(t, skip_special_tokens=True) for t in translated]

        updateEnrichableDescriptions(zip(source_uris, decoded))

        return Response("Execution finished", 200)
    else:
        return Response("No results found", 204)