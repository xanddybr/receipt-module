import os
import re
import tempfile
from datetime import datetime
from flask import Flask, render_template_string, request, send_file
from weasyprint import HTML

app = Flask(__name__)

# HTML layout combining both the input form and the printable receipt style
TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gerador de Recibo</title>
    <style>
        body { font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 40px; }
        .container { max-width: 80%; background: white; margin: 0 auto; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 8px; }
        h2 { border-bottom: 2px solid #2c3e50; padding-bottom: 10px; color: #2c3e50; margin-top: 0; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-weight: bold; margin-bottom: 6px; font-size: 14px; color: #555; }
        label.required::after { content: " *"; color: #e74c3c; }
        .required-note { font-size: 12px; color: #777; margin-bottom: 18px; }
        input[type="text"], input[type="date"], input[type="number"], select, textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 15px; }
        textarea { height: 80px; resize: vertical; }
        button { background-color: #27ae60; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; width: 100%; font-weight: bold; transition: background 0.2s; }
        button:hover { background-color: #219653; }
        .radio-group label { display: inline-flex; align-items: center; gap: 6px; font-weight: normal; margin-right: 24px; cursor: pointer; }
        .total-box { margin-bottom: 18px; padding: 12px; background: #eafaf1; border: 1px solid #27ae60; border-radius: 4px; font-size: 16px; font-weight: bold; color: #2c3e50; }
        .complemento-group { border: 1px solid #ddd; border-radius: 4px; padding: 12px; background: #fafafa; }
        .complemento-row { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
        .complemento-row:last-child { margin-bottom: 0; }
        .complemento-row > * { flex: 1; }
        .complemento-row button.remove-btn { flex: 0 0 38px; width: 38px; padding: 8px 0; background: #e74c3c; font-size: 16px; }
        .complemento-row button.remove-btn:hover { background: #c0392b; }
        .complemento-row:last-child button.remove-btn { visibility: hidden; }

        /* PDF specific layout rules */
        @page { size: letter; margin: 12mm; }
        body.pdf { padding: 0; background: white; }
        body.pdf .container { max-width: none; margin: 0; padding: 0; box-shadow: none; border-radius: 0; }
        .receipt-print { width: 100%; background: white; page-break-inside: avoid; }
        .receipt-via { display: flex; justify-content: space-between; font-size: 11px; color: #777; text-transform: uppercase; }
        .receipt-header { text-align: center; font-size: 16px; font-weight: bold; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px; color: #2c3e50; border-bottom: 3px double #2c3e50; padding-bottom: 8px; }
        .receipt-body { font-size: 13px; line-height: 1.7; margin-bottom: 10px; text-align: justify; }
        .highlight { font-weight: bold; border-bottom: 1px dotted #000; padding: 0 5px; }
        .receipt-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px; }
        .receipt-table th { background: #2c3e50; color: white; text-align: left; padding: 6px 8px; font-weight: bold; }
        .receipt-table td { border-bottom: 1px solid #ddd; padding: 6px 8px; vertical-align: top; }
        .receipt-table .num { text-align: right; white-space: nowrap; }
        .receipt-table tfoot td { font-weight: bold; border-top: 2px solid #2c3e50; border-bottom: none; background: #f4f7f6; }
        .receipt-footer { margin-top: 16px; text-align: center; font-size: 13px; }
        .signatures { display: flex; justify-content: space-around; gap: 40px; margin-top: 32px; }
        .signature-line { width: 280px; border-top: 1px solid #333; padding-top: 6px; font-size: 12px; text-transform: uppercase; color: #555; }
        .signature-role { display: block; font-size: 10px; color: #999; margin-top: 2px; }
        .cut-line { border-top: 1px dashed #999; margin: 20px 0; text-align: center; font-size: 10px; color: #999; }

        /* Secondary buttons */
        button.secondary { background-color: #2c3e50; }
        button.secondary:hover { background-color: #1a252f; }

        /* Browser print preview: shows the receipt as a letter-size sheet */
        .print-toolbar { width: 216mm; margin: 0 auto 15px; display: flex; gap: 10px; justify-content: flex-end; }
        .print-toolbar button { width: auto; }
        @media screen {
            body.browser { background: #d5d8dc; padding: 30px 0; }
            body.browser .container { max-width: none; width: 216mm; min-height: 279mm; margin: 0 auto; padding: 12mm; box-sizing: border-box; border-radius: 0; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
        }
        @media print {
            .print-toolbar { display: none; }
        }
    </style>
</head>
<body{% if preview %} class="pdf{% if browser %} browser{% endif %}"{% endif %}>

{% if browser %}
<div class="print-toolbar">
    <button type="button" class="secondary" onclick="window.close()">Fechar</button>
    <!-- Re-sends the same form data to generate the PDF -->
    <form method="POST" action="/generate">
        {% for key, value in form_items %}
        <input type="hidden" name="{{ key }}" value="{{ value }}">
        {% endfor %}
        <button type="submit">Gerar PDF do Recibo</button>
    </form>
    <button type="button" onclick="window.print()">Imprimir</button>
</div>
{% endif %}

<div class="container">
    {% if not preview %}
    <!-- Input Web Form -->
    <h2>Gerador de Recibo v1.0</h2>
    <form method="POST" action="/visualizar" target="_blank">
        <div class="required-note"><span style="color: #e74c3c;">*</span> Campos obrigatórios</div>
        <div class="form-group">
            <label class="required">Título do Recibo:</label>
            <select name="title" required>
                <option value="Recibo de pagamento de prestação de serviços">Recibo de pagamento de prestação de serviços</option>
                <option value="Recibo de pagamento">Recibo de pagamento</option>
            </select>
        </div>
        <div class="form-group">
            <label class="required">Nome do pagador:</label>
            <select name="pagador" required>
                <option value="Alexandre de Santana de Souza">Alexandre de Santana de Souza</option>
            </select>
        </div>
        <div class="form-group">
            <label class="required">Nome do Recebedor (Quem recebeu / Prestador do serviço):</label>
            <input type="text" name="name" placeholder="Ex: João Silva" required>
        </div>
        <div class="form-group">
            <label class="required">Tipo de serviço:</label>
            <select name="tipo_servico" required>
                <option value="Serviços domésticos">Serviços domésticos</option>
                <option value="Limpeza e faxina">Limpeza e faxina</option>
                <option value="Babá">Babá</option>
                <option value="Cuidador(a) de idosos">Cuidador(a) de idosos</option>
                <option value="Cozinheiro(a)">Cozinheiro(a)</option>
                <option value="Jardinagem">Jardinagem</option>
                <option value="Pintura">Pintura</option>
                <option value="Serviços elétricos">Serviços elétricos</option>
                <option value="Serviços hidráulicos">Serviços hidráulicos</option>
                <option value="Manutenção e reparos">Manutenção e reparos</option>
                <option value="Motorista">Motorista</option>
                <option value="Aulas particulares">Aulas particulares</option>
                <option value="Outros serviços">Outros serviços</option>
            </select>
        </div>
        <div class="form-group">
            <label>Descrição do Serviço:</label>
            <textarea name="description" placeholder="Ex: Descreva as atividades realizadas, no contexto do tipo dos serviços prestados."></textarea>
        </div>
        <div class="form-group">
            <label class="required">Forma de pagamento:</label>
            <div class="radio-group">
                <label><input type="radio" name="forma_pagamento" value="dia" checked> Pagamento por dia</label>
                <label><input type="radio" name="forma_pagamento" value="hora"> Pagamento por hora</label>
            </div>
        </div>
        <div class="form-group">
            <label id="valor-label" class="required">Valor por dia (R$):</label>
            <input type="text" name="valor" id="valor" placeholder="Ex: 150,00" required>
        </div>
        <div class="form-group">
            <label id="quantidade-label" class="required">Quantidade de dias:</label>
            <input type="number" name="quantidade" id="quantidade" min="0.01" step="any" placeholder="Ex: 5" required>
        </div>
        <div class="form-group">
            <label>Complementos:</label>
            <div class="complemento-group" id="complementos"></div>
        </div>
        <div class="form-group">
            <label class="required">Forma de Pagamento:</label>
            <select name="meio_pagamento" required>
                <option value="Pix">Pix</option>
                <option value="Débito">Débito</option>
                <option value="Crédito">Crédito</option>
                <option value="Dinheiro">Dinheiro</option>
            </select>
        </div>
        <div class="total-box">Total: R$ <span id="total">0,00</span></div>
        <div class="form-group">
            <label class="required">Data:</label>
            <input type="date" name="data" required>
        </div>
        <button type="submit">Visualizar impressão</button>
    </form>

    <template id="complemento-template">
        <div class="complemento-row">
            <input type="text" name="complemento_valor" class="complemento-valor" placeholder="Valor (R$) Ex: 50,00">
            <select name="complemento_tipo" class="complemento-tipo">
                <option value="">Complemento...</option>
                <option value="Passagem">Passagem</option>
                <option value="Bonificação">Bonificação</option>
                <option value="Hora Extra">Hora Extra</option>
            </select>
            <button type="button" class="remove-btn" title="Remover">×</button>
        </div>
    </template>

    <script>
        // Converts "1.500,00", "1500", "1500,5" or "1500.50" into 1500.00
        function parseBR(text) {
            text = text.replace(/[R$\\s]/g, '');
            if (text.includes(',')) {
                text = text.replace(/\\./g, '').replace(',', '.');
            } else if (!/^\\d+\\.\\d{1,2}$/.test(text)) {
                text = text.replace(/\\./g, '');
            }
            const n = parseFloat(text);
            return isNaN(n) ? 0 : n;
        }

        // Rewrites a currency field in the Brazilian format when leaving it ("150" -> "150,00")
        function autoFormatCurrency(input) {
            input.addEventListener('blur', () => {
                if (input.value.trim() !== '') {
                    input.value = formatBR(parseBR(input.value));
                    updateTotal();
                }
            });
        }

        function formatBR(number) {
            return number.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        const complementos = document.getElementById('complementos');

        // Adds a new empty "Valor + Complemento" row at the end of the group
        function addComplementoRow() {
            const row = document.getElementById('complemento-template').content.firstElementChild.cloneNode(true);
            const valor = row.querySelector('.complemento-valor');
            const tipo = row.querySelector('.complemento-tipo');

            valor.addEventListener('input', updateTotal);
            autoFormatCurrency(valor);
            tipo.addEventListener('change', () => {
                // The value becomes required once a complement type is chosen
                valor.required = tipo.value !== '';
                if (tipo.value !== '' && row === complementos.lastElementChild) {
                    addComplementoRow();
                }
                updateTotal();
            });
            row.querySelector('.remove-btn').addEventListener('click', () => {
                row.remove();
                updateTotal();
            });

            complementos.appendChild(row);
        }

        function updateTotal() {
            const forma = document.querySelector('input[name="forma_pagamento"]:checked').value;
            const unidade = forma === 'dia' ? 'dia' : 'hora';
            document.getElementById('valor-label').textContent = 'Valor por ' + unidade + ' (R$):';
            document.getElementById('quantidade-label').textContent = 'Quantidade de ' + unidade + 's:';

            const valor = parseBR(document.getElementById('valor').value);
            const quantidade = parseFloat(document.getElementById('quantidade').value) || 0;
            let total = valor * quantidade;

            complementos.querySelectorAll('.complemento-row').forEach(row => {
                if (row.querySelector('.complemento-tipo').value !== '') {
                    total += parseBR(row.querySelector('.complemento-valor').value);
                }
            });

            document.getElementById('total').textContent = formatBR(total);
        }

        document.querySelectorAll('input[name="forma_pagamento"], #valor, #quantidade').forEach(el => el.addEventListener('input', updateTotal));
        autoFormatCurrency(document.getElementById('valor'));
        addComplementoRow();
        updateTotal();
    </script>

    {% else %}
    <!-- HTML Document structure meant for PDF Compilation -->
    {% for via in ["1ª via", "2ª via"] %}
    {% if not loop.first %}<div class="cut-line">✂ recorte aqui</div>{% endif %}
    <div class="receipt-print">
        <div class="receipt-via"><span>{{ mes_referencia }}</span><span>{{ via }}</span></div>
        <div class="receipt-header">{{ title }}</div>
        <div class="receipt-body">
            Eu, <span class="highlight">&nbsp;{{ name }}&nbsp;</span>, recebi de
            <span class="highlight">&nbsp;{{ pagador }}&nbsp;</span> a importância de
            <span class="highlight">&nbsp;R$ {{ total }}&nbsp;</span>, referente aos itens descritos abaixo:
        </div>
        <table class="receipt-table">
            <thead>
                <tr>
                    <th>Descrição</th>
                    <th class="num">Quantidade</th>
                    <th class="num">Valor unitário</th>
                    <th class="num">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{{ tipo_servico }}{% if description %} - {{ description }}{% endif %}</td>
                    <td class="num">{{ quantidade }} {{ unidade }}</td>
                    <td class="num">R$ {{ valor }} / {{ forma_pagamento }}</td>
                    <td class="num">R$ {{ subtotal_servico }}</td>
                </tr>
                {% for item in complementos %}
                <tr>
                    <td>{{ item.tipo }}</td>
                    <td class="num">-</td>
                    <td class="num">-</td>
                    <td class="num">R$ {{ item.valor }}</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3">Total</td>
                    <td class="num">R$ {{ total }}</td>
                </tr>
            </tfoot>
        </table>
        <div class="receipt-body">
            Forma de pagamento: <span class="highlight">&nbsp;{{ meio_pagamento }}&nbsp;</span>.
            Para clareza e firmeza do pagamento, firmo o presente recibo.
        </div>
        <div class="receipt-footer">
            {{ cidade }}, {{ data }}.
            <div class="signatures">
                <div class="signature-line">{{ pagador }}<span class="signature-role">Pagador</span></div>
                <div class="signature-line">{{ name }}<span class="signature-role">Recebedor</span></div>
            </div>
        </div>
    </div>
    {% endfor %}
    {% endif %}
</div>

</body>
</html>
"""

def parse_br(text):
    # Converts "1.500,00", "1500", "1500,5" or "1500.50" into 1500.0
    text = text.replace('R$', '').replace(' ', '')
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    elif not re.fullmatch(r'\d+\.\d{1,2}', text):
        text = text.replace('.', '')
    return float(text)

def format_br(number, decimals=2):
    # Converts 1500.0 into "1.500,00"
    return f"{number:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')

CIDADE = "Rio de Janeiro"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

def format_date_extenso(text):
    # Converts "2026-10-29" into ("29 de outubro de 2026", "Outubro/2026")
    try:
        date = datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return text, ""
    mes = MESES[date.month - 1]
    return f"{date.day} de {mes} de {date.year}", f"{mes.capitalize()}/{date.year}"

@app.route('/')
def index():
    return render_template_string(TEMPLATE, preview=False)

def build_receipt_data():
    # Returns (receipt data, error message) from the posted form
    # Calculate the total according to the payment type (per day or per hour)
    forma_pagamento = request.form.get('forma_pagamento', 'dia')
    try:
        valor = parse_br(request.form.get('valor', ''))
        quantidade = float(request.form.get('quantidade', ''))
    except ValueError:
        return None, "Valor ou quantidade inválidos. Use o formato 1.500,00 para o valor."

    unidade = forma_pagamento if quantidade == 1 else forma_pagamento + 's'
    quantidade_texto = str(int(quantidade)) if quantidade.is_integer() else format_br(quantidade)
    subtotal_servico = valor * quantidade

    # Extra items (Passagem, Bonificação); rows without a chosen type are ignored
    complementos = []
    for tipo, valor_complemento in zip(request.form.getlist('complemento_tipo'), request.form.getlist('complemento_valor')):
        if not tipo:
            continue
        try:
            complementos.append({"tipo": tipo, "valor": parse_br(valor_complemento)})
        except ValueError:
            return None, f"Valor inválido para o complemento {tipo}. Use o formato 1.500,00."

    total = subtotal_servico + sum(item["valor"] for item in complementos)
    data_extenso, mes_referencia = format_date_extenso(request.form.get('data', ''))

    # Extract values directly from form post parameters
    form_data = {
        "title": request.form.get('title'),
        "pagador": request.form.get('pagador'),
        "name": request.form.get('name'),
        "tipo_servico": request.form.get('tipo_servico'),
        "description": request.form.get('description'),
        "forma_pagamento": forma_pagamento,
        "valor": format_br(valor),
        "quantidade": quantidade_texto,
        "unidade": unidade,
        "subtotal_servico": format_br(subtotal_servico),
        "complementos": [{"tipo": item["tipo"], "valor": format_br(item["valor"])} for item in complementos],
        "total": format_br(total),
        "cidade": CIDADE,
        "data": data_extenso,
        "mes_referencia": mes_referencia,
        "meio_pagamento": request.form.get('meio_pagamento'),
        "preview": True
    }
    return form_data, None

@app.route('/visualizar', methods=['POST'])
def visualizar():
    # Shows the receipt in the browser, ready to print
    form_data, error = build_receipt_data()
    if error:
        return error, 400
    return render_template_string(TEMPLATE, browser=True, form_items=list(request.form.items(multi=True)), **form_data)

@app.route('/generate', methods=['POST'])
def generate():
    form_data, error = build_receipt_data()
    if error:
        return error, 400

    # Process the data variables inside the HTML string layout template
    html_content = render_template_string(TEMPLATE, **form_data)

    # Build a temporary path location to save your file cleanly
    pdf_file = os.path.join(tempfile.gettempdir(), "recibo.pdf")

    # Render and output code directly to file
    HTML(string=html_content).write_pdf(pdf_file)

    return send_file(pdf_file, as_attachment=True, download_name="recibo.pdf")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
