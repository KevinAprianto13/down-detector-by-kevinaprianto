from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site_status.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class SiteStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SiteStatus(url={self.url}, status={self.status}, timestamp={self.timestamp})>"

@app.route('/')
def index():
    # Display the latest status for each unique URL
    latest_statuses = db.session.query(SiteStatus.url, db.func.max(SiteStatus.timestamp).label('max_time')).group_by(SiteStatus.url)
    statuses = [SiteStatus.query.filter_by(url=url, timestamp=max_time).first() for url, max_time in latest_statuses]
    return render_template('index.html', statuses=statuses)

@app.route('/check_status', methods=['POST'])
def check_status():
    website_url = request.form.get('website_url')
    status = check_website(website_url)

    # Simpan status ke database
    site_status = SiteStatus(url=website_url, status=status)
    db.session.add(site_status)
    db.session.commit()

    return render_template('index.html', status=status, website_url=website_url)

def check_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return "UP"
        else:
            return f"DOWN, Status Code: {response.status_code}"
    except requests.ConnectionError:
        return "DOWN, Connection Error"
    except Exception as e:
        return f"DOWN, Exception: {e}"

if __name__ == '__main__':
    app.run(host='192.168.137.2', port=8000, debug=True)
