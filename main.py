import sympy as sp
import numpy as np
from flask import Flask, render_template, request, jsonify
import plotly.graph_objects as go
import plotly.utils
import json
import os

app = Flask(__name__)
x, y, a = sp.symbols('x y a', real=True)

class CurveTracer:
    def __init__(self, eq_str, p_val):
        eq_str = eq_str.replace('^', '**')
        try:
            if '=' in eq_str:
                lhs, rhs = eq_str.split('=')
                self.expr = sp.sympify(lhs) - sp.sympify(rhs)
            else:
                self.expr = sp.sympify(eq_str)
            self.expr = self.expr.subs(a, p_val)
        except: self.expr = None

    def analyze(self):
        if self.expr is None: return {"error": "समीकरण सही नहीं है"}
        # Symmetry Logic
        x_s = sp.simplify(self.expr.subs(y, -y) - self.expr) == 0
        y_s = sp.simplify(self.expr.subs(x, -x) - self.expr) == 0
        at_o = self.expr.subs([(x,0), (y,0)]) == 0
        
        return {
            "सममिति (Symmetry)": {
                "क्यों?": "ताकि पता चले ग्राफ किस अक्ष के चारों ओर एक जैसा है।",
                "रिजल्ट": f"X-axis: {'हाँ' if x_s else 'नहीं'}, Y-axis: {'हाँ' if y_s else 'नहीं'}",
                "मतलब": "अगर 'हाँ' है, तो ग्राफ ऊपर-नीचे या दाएं-बाएं बिल्कुल एक जैसा दिखेगा।"
            },
            "मूल बिंदु (Origin)": {
                "क्यों?": "देखने के लिए कि ग्राफ (0,0) से गुजरता है या नहीं।",
                "रिजल्ट": "हाँ, गुजरता है" if at_o else "नहीं, नहीं गुजरता",
                "मतलब": "अगर हाँ, तो चित्र की शुरुआत सेंटर से करें।"
            }
        }

    def get_plot(self):
        res = 100
        x_v = np.linspace(-10, 10, res)
        y_v = np.linspace(-10, 10, res)
        X, Y = np.meshgrid(x_v, y_v)
        f = sp.lambdify((x, y), self.expr, 'numpy')
        try: Z = f(X, Y)
        except: return None
        fig = go.Figure(data=go.Contour(x=x_v, y=y_v, z=Z, contours=dict(start=0, end=0, size=0.1, coloring='lines'), line_width=3))
        fig.update_layout(title="कर्व का ग्राफ", template="plotly_white")
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def home(): return render_template('index.html')

@app.route('/trace', methods=['POST'])
def trace():
    data = request.json
    t = CurveTracer(data['eq'], float(data['p']))
    return jsonify({'report': t.analyze(), 'graph': t.get_plot()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
