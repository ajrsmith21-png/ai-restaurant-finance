from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    # CORE METRICS

    sales = 5200
    labor_cost = 1450
    waste_cost = 340
    covers = 186

    # PERCENTAGES

    labor_percent = round((labor_cost / sales) * 100, 1)
    waste_percent = round((waste_cost / sales) * 100, 1)

    # PROFIT IMPACT

    profit_impact_percent = round(
        ((labor_cost + waste_cost) / sales) * 100,
        1
    )

    # HOURLY ANALYTICS

    hourly_data = [

        {
            "hour": "11 AM",
            "sales": 420,
            "covers": 18,
            "labor_cost": 110,
            "sales_per_server_hour": 140,
            "covers_per_server_hour": 6,
            "labor_percent": 26
        },

        {
            "hour": "12 PM",
            "sales": 780,
            "covers": 34,
            "labor_cost": 160,
            "sales_per_server_hour": 195,
            "covers_per_server_hour": 8.5,
            "labor_percent": 20
        },

        {
            "hour": "1 PM",
            "sales": 690,
            "covers": 29,
            "labor_cost": 155,
            "sales_per_server_hour": 172,
            "covers_per_server_hour": 7.2,
            "labor_percent": 22
        },

        {
            "hour": "2 PM",
            "sales": 480,
            "covers": 21,
            "labor_cost": 145,
            "sales_per_server_hour": 120,
            "covers_per_server_hour": 5.2,
            "labor_percent": 30
        },

        {
            "hour": "3 PM",
            "sales": 350,
            "covers": 14,
            "labor_cost": 138,
            "sales_per_server_hour": 88,
            "covers_per_server_hour": 3.5,
            "labor_percent": 39
        }

    ]

    return render_template(
        "dashboard.html",

        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        covers=covers,

        labor_percent=labor_percent,
        waste_percent=waste_percent,
        profit_impact_percent=profit_impact_percent,

        hourly_data=hourly_data,

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