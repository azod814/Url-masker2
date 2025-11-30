# safe_masker.py
# A SAFE token-based redirector/shortener with clear landing page.
# NOTE: This intentionally DOES NOT provide features to impersonate other domains.
# Use responsibly.

from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

def banner():
    b = r"""
              █    ██  ██▀███   ██▓                          
             ██  ▓██▒▓██ ▒ ██▒▓██▒                          
            ▓██  ▒██░▓██ ░▄█ ▒▒██░                          
            ▓▓█  ░██░▒██▀▀█▄  ▒██░                          
            ▒▒█████▓ ░██▓ ▒██▒░██████▒                      
            ░▒▓▒ ▒ ▒ ░ ▒▓ ░▒▓░░ ▒░▓  ░                      
            ░░▒░ ░ ░   ░▒ ░ ▒░░ ░ ▒  ░                      
             ░░░ ░ ░   ░░   ░   ░ ░                         
               ░        ░         ░  ░                      
                                                            
 ███▄ ▄███▓ ▄▄▄        ██████  ██ ▄█▀ ██▓ ███▄    █   ▄████ 
▓██▒▀█▀ ██▒▒████▄    ▒██    ▒  ██▄█▒ ▓██▒ ██ ▀█   █  ██▒ ▀█▒
▓██    ▓██░▒██  ▀█▄  ░ ▓██▄   ▓███▄░ ▒██▒▓██  ▀█ ██▒▒██░▄▄▄░
▒██    ▒██ ░██▄▄▄▄██   ▒   ██▒▓██ █▄ ░██░▓██▒  ▐▌██▒░▓█  ██▓
▒██▒   ░██▒ ▓█   ▓██▒▒██████▒▒▒██▒ █▄░██░▒██░   ▓██░░▒▓███▀▒
░ ▒░   ░  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░▒ ▒▒ ▓▒░▓  ░ ▒░   ▒ ▒  ░▒   ▒ 
░  ░      ░  ▒   ▒▒ ░░ ░▒  ░ ░░ ░▒ ▒░ ▒ ░░ ░░   ░ ▒░  ░   ░ 
░      ░     ░   ▒   ░  ░  ░  ░ ░░ ░  ▒ ░   ░   ░ ░ ░ ░   ░ 
       ░         ░  ░      ░  ░  ░    ░           ░       ░ 
            SAFE URL Redirector (no impersonation)
    """
    print("\033[92m" + b + "\033[0m")

def gen_token(n=10):
    return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(n))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def ensure_log():
    if not os.path.exists(log_file):
        with open(log_file,'w',newline='') as f:
            csv.writer(f).writerow(["timestamp","token","remote_addr","original"])

def log_click(token, remote):
    ensure_log()
    with open(log_file,'a',newline='') as f:
        csv.writer(f).writerow([time.strftime("%Y-%m-%d %H:%M:%S"), token, remote, url_mapping[token]["original"]])

# Safe landing page: clearly shows ORIGINAL destination, asks for consent (and shows fake-display only as LABEL if provided).
@app.route('/r/<token>')
def landing(token):
    info = url_mapping.get(token)
    if not info:
        return "Mapping not found.", 404
    original = info['original']
    label = info.get('label') or ""
    # log click attempt
    try:
        log_click(token, request.remote_addr)
    except:
        pass
    html = '''
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Redirecting — Confirm</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
          body{font-family:Arial,Helvetica,sans-serif;background:#f7fafc;color:#0f172a;margin:0;padding:0;display:flex;align-items:center;justify-content:center;height:100vh}
          .card{background:#fff;padding:28px;border-radius:8px;box-shadow:0 8px 30px rgba(2,6,23,.08);max-width:720px;width:90%}
          .title{font-size:20px;font-weight:700;margin-bottom:6px}
          .desc{color:#475569;margin-bottom:14px}
          .label{display:inline-block;background:#eef2ff;color:#3730a3;padding:6px 10px;border-radius:6px;margin-bottom:10px}
          .orig{background:#ecfccb;color:#065f46;padding:10px;border-radius:6px;font-weight:600}
          .controls{margin-top:16px}
          button{padding:10px 16px;border-radius:6px;border:0;cursor:pointer}
          .go{background:#0369a1;color:white}
          .cancel{background:#e2e8f0;margin-left:10px}
          .note{color:#94a3b8;margin-top:10px;font-size:13px}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="title">You're about to be redirected</div>
          <div class="desc">For transparency, we show the destination below. If you trust this, click "Proceed".</div>
          {% if label %}
            <div class="label">Label: {{ label }}</div>
          {% endif %}
          <div style="margin:12px 0;">
            <div style="font-size:13px;color:#475569;margin-bottom:6px">Destination (original):</div>
            <div class="orig">{{ original }}</div>
          </div>
          <div class="controls">
            <button class="go" onclick="window.location.replace('{{ original }}')">Proceed — go to destination</button>
            <button class="cancel" onclick="history.back()">Cancel</button>
          </div>
          <div class="note">Note: This redirector intentionally shows the original URL clearly for safety and cannot impersonate other domains.</div>
        </div>
      </body>
    </html>
    '''
    return render_template_string(html, original=original, label=label)

def setup_ngrok(port=5000):
    try:
        t = ngrok.connect(port)
        public = t.public_url
        print(f"\n\033[92m[+]\033[0m Ngrok public URL: {public}\033[0m")
        return public
    except Exception as e:
        print(f"\n\033[91m[-]\033[0m Ngrok start error: {e}\033[0m")
        return None

def mask_flow(public):
    os.system('cls' if os.name=='nt' else 'clear')
    banner()
    print("\nSAFE redirector — create a token link that shows original destination clearly.\n")
    orig = input("Enter ORIGINAL full URL (must be full, e.g. https://example.com/path): ").strip()
    if not orig:
        print("No URL entered.")
        input("Press Enter...")
        return
    # optional label (for your own notes)
    label = input("Optional label to show on landing page (e.g., 'Promo page' ) — leave blank to skip: ").strip()
    token = gen_token = ''.join
    token = ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(10))
    url_mapping[token] = {"original": orig, "created": time.time(), "label": label}
    # ensure public present
    if not public:
        print("\nNo ngrok public URL available — start ngrok manually using 'ngrok http 5000' and paste the forwarding URL here.")
        pub_manual = input("Paste ngrok URL (or press Enter to cancel): ").strip()
        if not pub_manual:
            print("Cancelled.")
            return
        public = pub_manual.rstrip('/')
    working = public.rstrip('/') + '/r/' + token
    # boxed highlight
    border = "+" + "-"*(len(working)+6) + "+"
    print("\n\n\033[1mFinal SAFE working link (share this):\033[0m")
    print("\033[1;32m" + border)
    print("|  " + working + "  |")
    print(border + "\033[0m")
    print("\nIMPORTANT: When a user opens this link, they will see the ORIGINAL destination clearly and must click Proceed to continue.")
    input("\nPress Enter to continue...")

def show_maps():
    if not url_mapping:
        print("No mappings.")
    else:
        for t,i in url_mapping.items():
            print(f"{t} -> {i['original']}  (label: {i.get('label')})")
    input("\nPress Enter...")

def main():
    banner()
    print("Starting ngrok and Flask...")
    public = setup_ngrok(5000)
    # start Flask in thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)).start()
    ensure_log()
    while True:
        os.system('cls' if os.name=='nt' else 'clear')
        banner()
        print(f"Ngrok public: {public}")
        print("\n1) Create safe redirect link\n2) Show mappings\n3) Exit")
        ch = input("Choose: ").strip()
        if ch == '1':
            mask_flow(public)
        elif ch == '2':
            show_maps()
        elif ch == '3':
            print("Exiting.")
            os._exit(0)
        else:
            input("Invalid. Press Enter...")

if __name__ == "__main__":
    main()
