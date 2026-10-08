import os
import time
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Gauge

app = Flask(__name__)

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/helpdesk"
)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)

ticket_created = Counter(
    "helpdesk_ticket_created_total",
    "Total number of tickets created"
)
tickets_total = Gauge(
    "helpdesk_tickets_total",
    "Total tickets currently stored"
)
tickets_open = Gauge(
    "helpdesk_tickets_open",
    "Number of open tickets"
)
tickets_resolved = Gauge(
    "helpdesk_tickets_resolved",
    "Number of resolved tickets"
)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def update_ticket_metrics():
    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status="Open").count()
    resolved_count = Ticket.query.filter_by(status="Resolved").count()
    tickets_total.set(total)
    tickets_open.set(open_count)
    tickets_resolved.set(resolved_count)


def init_db():
    last_error = None
    for _ in range(15):
        try:
            db.create_all()
            update_ticket_metrics()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


@app.route("/")
def index():
    update_ticket_metrics()
    return render_template(
        "index.html",
        total=Ticket.query.count(),
        open_count=Ticket.query.filter_by(status="Open").count(),
        resolved=Ticket.query.filter_by(status="Resolved").count(),
    )


@app.route("/tickets")
def tickets():
    return render_template("tickets.html", tickets=Ticket.query.order_by(Ticket.id.desc()).all())


@app.route("/tickets/create", methods=["POST"])
def create_ticket():
    ticket = Ticket(
        name=request.form["name"],
        title=request.form["title"],
        description=request.form["description"],
        category=request.form["category"],
        priority=request.form["priority"],
        status="Open",
    )
    db.session.add(ticket)
    db.session.commit()
    ticket_created.inc()
    update_ticket_metrics()
    return redirect(url_for("tickets"))


@app.route("/tickets/<int:ticket_id>/resolve", methods=["POST"])
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = "Resolved"
    db.session.commit()
    update_ticket_metrics()
    return redirect(url_for("tickets"))


@app.route("/api/tickets")
def api_tickets():
    rows = Ticket.query.order_by(Ticket.id.desc()).all()
    return jsonify([
        {
            "id": t.id,
            "name": t.name,
            "title": t.title,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in rows
    ])


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "smart-helpdesk"})


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
