from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():

    # Example fake data for MVP
    sales = 5200
    labor_cost = 1450
    waste_cost = 340

    labor_percent = round((labor_cost / sales) * 100, 1)
    waste_percent = round((waste_cost / sales) * 100, 1)
    profit_impact = labor_cost + waste_cost

    return render_template(
        'dashboard.html',
        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        labor_percent=labor_percent,
        waste_percent=waste_percent,
        profit_impact=profit_impact
    )

@app.route("/waste-analytics")
def waste_analytics():
    return render_template("waste_analytics.html")


@app.route("/labour-tracking")
def labour_tracking():
    return render_template("labour_tracking.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    sales = 5200
    labor_cost = 1450
    waste_cost = 340

    labor_percent = round((labor_cost / sales) * 100, 1)

    return render_template(
        "dashboard.html",
        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        labor_percent=labor_percent,
        active_page="dashboard"
    )


@app.route("/waste-analytics")
def waste_analytics():

    return render_template(
        "waste_analytics.html",
        active_page="waste"
    )


@app.route("/labour-tracking")
def labour_tracking():

    return render_template(
        "labour_tracking.html",
        active_page="labour"
    )


@app.route("/reports")
def reports():

    return render_template(
        "reports.html",
        active_page="reports"
    )


if __name__ == "__main__":
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)