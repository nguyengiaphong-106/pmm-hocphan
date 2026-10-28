from flask import Flask, render_template, request

app = Flask(__name__)

# ---------------------------------------------------------
# 1. TRANG CHỦ
# ---------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------------------------------------------------
# 2. MÁY TÍNH CƠ BẢN
# ---------------------------------------------------------
@app.route('/bai1', methods=['GET', 'POST'])
def bai1_calculator():
    values = {'a': '', 'b': '', 'op': '+'}
    errors = {'a': '', 'b': '', 'general': ''}
    result = None

    if request.method == 'POST':
        raw_a = request.form.get('a', '').strip()
        raw_b = request.form.get('b', '').strip()
        op = request.form.get('op', '+')

        values['a'], values['b'], values['op'] = raw_a, raw_b, op
        val_a, val_b = None, None

        if not raw_a and not raw_b:
            errors['a'] = "Lỗi cả hai ô"
        else:
            if not raw_a:
                errors['a'] = "Vui lòng nhập một số."
            else:
                try:
                    val_a = float(raw_a.replace(',', '.'))
                except ValueError:
                    errors['a'] = "Vui lòng nhập một số."

            if not raw_b:
                errors['b'] = "Vui lòng nhập một số."
            else:
                try:
                    val_b = float(raw_b.replace(',', '.'))
                except ValueError:
                    errors['b'] = "Vui lòng nhập một số."

            if val_a is not None and val_b is not None:
                if op == '+': res_val = val_a + val_b
                elif op == '-': res_val = val_a - val_b
                elif op == '*': res_val = val_a * val_b
                elif op == '/':
                    if val_b == 0: errors['b'] = "Không thể chia cho 0."
                    else: res_val = val_a / val_b
                else: errors['general'] = "Phép toán không hợp lệ."

                if 'res_val' in locals() and not errors['b']:
                    result = f"{val_a:g} {op} {val_b:g} = {res_val:g}"

    return render_template('calc.html', values=values, errors=errors, result=result)

# ---------------------------------------------------------
# 3. TÍNH ĐIỂM HỌC PHẦN
# ---------------------------------------------------------
def validate_score(val_str):
    if not val_str:
        return None, "Vui lòng nhập một số."
    try:
        val = float(val_str.replace(',', '.'))
    except ValueError:
        return None, "Vui lòng nhập một số."
    if val < 0 or val > 10:
        return None, "Điểm phải từ 0 đến 10."
    return val, None

@app.route('/bai2', methods=['GET', 'POST'])
def bai2_tinh_diem():
    values = {'cc': '', 'gk': '', 'ck': ''}
    errors = {'cc': '', 'gk': '', 'ck': ''}
    result = None

    if request.method == 'POST':
        raw_cc = request.form.get('cc', '').strip()
        raw_gk = request.form.get('gk', '').strip()
        raw_ck = request.form.get('ck', '').strip()

        values['cc'], values['gk'], values['ck'] = raw_cc, raw_gk, raw_ck

        if not raw_cc and not raw_gk and not raw_ck:
            errors['cc'] = "Lỗi cả 3 ô"
        else:
            val_cc, errors['cc'] = validate_score(raw_cc)
            val_gk, errors['gk'] = validate_score(raw_gk)
            val_ck, errors['ck'] = validate_score(raw_ck)

            if val_cc is not None and val_gk is not None and val_ck is not None:
                score = round(val_cc * 0.1 + val_gk * 0.3 + val_ck * 0.6, 1)
                if val_ck < 1: grade = "F (điểm thi dưới 1)"
                elif score >= 8.5: grade = "A"
                elif score >= 7.0: grade = "B"
                elif score >= 5.5: grade = "C"
                elif score >= 4.0: grade = "D"
                else: grade = "F"

                result = f"{score} {grade}"

    return render_template('diem.html', values=values, errors=errors, result=result)

# ---------------------------------------------------------
# 4. TÍNH CHỈ SỐ BMI
# ---------------------------------------------------------
@app.route('/bmi', methods=['GET', 'POST'])
def tinh_bmi():
    values = {'height': '', 'weight': ''}
    errors = {'height': '', 'weight': ''}
    result = None

    if request.method == 'POST':
        raw_h = request.form.get('height', '').strip()
        raw_w = request.form.get('weight', '').strip()

        values['height'], values['weight'] = raw_h, raw_w

        if not raw_h and not raw_w:
            errors['height'] = "Lỗi cả hai ô"
        else:
            val_h, val_w = None, None

            if not raw_h:
                errors['height'] = "Vui lòng nhập một số."
            else:
                try:
                    val_h = float(raw_h.replace(',', '.'))
                    if val_h < 50 or val_h > 250:
                        if 0 < val_h < 50:
                            errors['height'] = "Giá trị phải từ 50 đến 250. (nhập mét thay vì cm)"
                        else:
                            errors['height'] = "Giá trị phải từ 50 đến 250."
                except ValueError:
                    errors['height'] = "Vui lòng nhập một số."

            if not raw_w:
                errors['weight'] = "Vui lòng nhập một số."
            else:
                try:
                    val_w = float(raw_w.replace(',', '.'))
                    if val_w < 10 or val_w > 300:
                        errors['weight'] = "Giá trị phải từ 10 đến 300."
                except ValueError:
                    errors['weight'] = "Vui lòng nhập một số."

            if val_h is not None and val_w is not None and not errors['height'] and not errors['weight']:
                h_m = val_h / 100.0
                bmi = round(val_w / (h_m ** 2), 1)

                min_w = round(18.5 * (h_m ** 2), 1)
                max_w = round(22.9 * (h_m ** 2), 1)

                if bmi < 18.5:
                    cat = "Thiếu cân"
                    color_class = "orange"
                elif bmi < 23.0:
                    cat = "Bình thường"
                    color_class = "green"
                elif bmi < 25.0:
                    cat = "Thừa cân"
                    color_class = "orange"
                else:
                    cat = "Béo phì"
                    color_class = "red"

                result = {
                    'bmi': bmi,
                    'category': cat,
                    'color_class': color_class,
                    'ideal_range': f"{min_w} – {max_w} kg"
                }

    return render_template('bmi.html', values=values, errors=errors, result=result)

if __name__ == '__main__':
    app.run(debug=True)