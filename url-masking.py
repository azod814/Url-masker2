from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>URL Masker & Modifier</title>
</head>
<body>
    <h1>URL Masker & Modifier Tool</h1>
    <form method="POST">
        <input type="text" name="original_url" placeholder="Enter Original URL (e.g., http://example.com)" required>
        <input type="text" name="fake_url" placeholder="Enter Fake URL (e.g., http://hello.com)" required>
        <button type="submit">Generate Masked URL</button>
    </form>
    {% if masked_url %}
    <p>Masked URL: <a href="{{ masked_url }}">{{ masked_url }}</a></p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    masked_url = None
    if request.method == "POST":
        original_url = request.form.get("original_url")
        fake_url = request.form.get("fake_url")
        if original_url and fake_url:
            # Masked URL banaye jo user ko fake_url dikhata hai, lekin original_url par redirect karta hai
            masked_url = f"http://your-server-ip:5000/redirect?fake={fake_url}&original={original_url}"
    return render_template_string(HTML_FORM, masked_url=masked_url)

@app.route("/redirect")
def redirect_to_url():
    fake_url = request.args.get("fake")
    original_url = request.args.get("original")
    if original_url:
        # User ko fake_url dikhata hai, lekin original_url par redirect karta hai
        return f"""
        <script>
            document.title = "Redirecting to {fake_url}";
            window.location.href = "{original_url}";
        </script>
        <p>Redirecting to {fake_url}...</p>
        """
    else:
        return "Invalid URL", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)