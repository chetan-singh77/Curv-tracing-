import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import numpy as np
from flask import Flask, render_template, request, jsonify
import plotly.graph_objects as go
import plotly.utils
import json
import os

app = Flask(__name__)

# x, y, a को ग्लोबल सिम्बल्स बनाना
x, y, a = sp.symbols('x y a', real=True)

class FinalTracer:
    def __init__(self, eq_str, p_val):
        # ^ को ** में बदलना
        clean_eq = eq_str.replace('^', '**')
        
        # ऑटोमैटिक गुणा (जैसे 4ax को 4*a*x समझना) के लिए ट्रांसफॉर्मेशन
        transformations = (standard_transformations + (implicit_multiplication_application,))
        
        try:
            if '=' in clean_eq:
                lhs_str, rhs_str = clean_eq.split('=')
                self.expr = parse_expr(lhs_str, transformations=transformations) - parse_expr(rhs_str, transformations=transformations)
            else:
                self.expr = parse_expr(clean_eq, transformations=transformations)
            
            # 'a' की वैल्यू भरना
            self.expr = self.expr.subs('a', p_val)
        except Exception as e:
            print(f"Parsing Error: {e}")
            self.expr = None

    def analyze(self):
        if self.expr is None: return {"error": "समीकरण गलत है"}
        
        # Origin Check: (0,0) पर वैल्यू 0 होनी चाहिए
        try:
            origin_val = sp.simplify(self.expr.subs([(x, 0), (y, 0)]))
            at_o = (origin_val == 0)
        except: at_o = False

        # Symmetry Logic
        try:
            x_sym = sp.simplify(self.expr.subs(y, -y) - self.expr) == 0
            y_sym = sp.simplify(self.expr.subs(x, -x) - self.expr) == 0
        except: x_sym = y_sym = False

        return {
            "मूल बिंदु (Origin)": {
                "रिजल्ट": "✅ हाँ, (0,0) से गुजरता है" if at_o else "❌ नहीं गुजरता",
                "मतलब": "अगर हाँ, तो ग्राफ सेंटर पॉइंट से शुरू होगा।"
            },
            "सममिति (Symmetry)": {
                "रिजल्ट": f"X-axis: {'हाँ' if x_sym else 'नहीं'}, Y-axis: {'हाँ' if y_sym else 'नहीं'}",
                "मतलब": "Symmetry बताती है कि ग्राफ का कौन सा हिस्सा Mirror Image है।"
            }
        }

    def get_graph(self):
        if self.expr is None: return None
        
        # ग्राफ के लिए कोआर्डिनेट्स
        grid_res = 150
        x_range = np.linspace(-10, 10, grid_res)
        y_range = np.linspace(-10, 10, grid_res)
        X, Y = np.meshgrid(x_range, y_range)
        
        # गणना के लिए फंक्शन बनाना
        f_vals = sp.lambdify((x, y), self.expr, modules=['numpy', 'sympy'])
        
        try:
            Z = f_vals(X, Y)
            # सिर्फ असली (Real) हिस्से को रखना
            if np.iscomplexobj(Z): Z = np.real(Z)
            # एरर वाली वैल्यूज को संभालना
            Z = np.nan_to_num(Z, nan=1e10, posinf=1e10, neginf=-1e10)
        except: return None

        fig = go.Figure(data=go.Contour(
            x=x_range, y=y_range, z=Z,
            contours=dict(start=0, end=0, size=0.1, showlines=True),
            line_width=4,
            colorscale=[[0, '#4f46e5'], [1, '#4f46e5']],
            showscale=False
        ))
        
        fig.update_layout(
            xaxis=dict(range=[-10, 10], zeroline=True, zerolinewidth=2, zerolinecolor='black'),
            yaxis=dict(range=[-10, 10], zeroline=True, zerolinewidth=2, zerolinecolor='black'),
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/trace', methods=['POST'])
def trace():
    data = request.json
    tracer = FinalTracer(data['eq'], float(data['p']))
    return jsonify({'report': tracer.analyze(), 'graph': tracer.get_graph()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
