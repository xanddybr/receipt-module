import { calcTotal, formatBR, parseBR } from './format.js';

const TITULOS = ['Recibo de pagamento de prestação de serviços', 'Recibo de pagamento'];
const PAGADORES = ['Alexandre de Santana de Souza'];
const TIPOS_SERVICO = ['Serviços domésticos', 'Limpeza e faxina', 'Babá', 'Cuidador(a) de idosos',
    'Cozinheiro(a)', 'Jardinagem', 'Pintura', 'Serviços elétricos', 'Serviços hidráulicos',
    'Manutenção e reparos', 'Motorista', 'Aulas particulares', 'Outros serviços'];
const TIPOS_COMPLEMENTO = ['Passagem', 'Bonificação', 'Hora Extra'];
const MEIOS_PAGAMENTO = ['Pix', 'Débito', 'Crédito', 'Dinheiro'];

let nextId = 0;
export function emptyComplemento() {
    return { id: nextId++, valor: '', tipo: '' };
}

// Rewrites a currency value in the Brazilian format when leaving the field ("150" -> "150,00")
function autoFormat(text) {
    const number = parseBR(text);
    return text.trim() === '' || isNaN(number) ? text : formatBR(number);
}

export default function ReceiptForm({ form, setForm, onSubmit }) {
    const unidade = form.forma_pagamento;

    function setField(field, value) {
        setForm(prev => ({ ...prev, [field]: value }));
    }

    function updateComplemento(id, changes) {
        setForm(prev => {
            let complementos = prev.complementos.map(item => (item.id === id ? { ...item, ...changes } : item));
            // Choosing a type on the last row adds a new empty row at the end
            const last = complementos[complementos.length - 1];
            if (last.id === id && last.tipo !== '') {
                complementos = [...complementos, emptyComplemento()];
            }
            return { ...prev, complementos };
        });
    }

    function removeComplemento(id) {
        setForm(prev => ({ ...prev, complementos: prev.complementos.filter(item => item.id !== id) }));
    }

    function handleSubmit(event) {
        event.preventDefault();
        onSubmit();
    }

    return (
        <div className="container">
            <h2>Gerador de Recibo v1.0</h2>
            <form onSubmit={handleSubmit}>
                <div className="required-note"><span style={{ color: '#e74c3c' }}>*</span> Campos obrigatórios</div>
                <div className="form-group">
                    <label className="required">Título do Recibo:</label>
                    <select value={form.title} onChange={e => setField('title', e.target.value)} required>
                        {TITULOS.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>
                <div className="form-group">
                    <label className="required">Nome do pagador:</label>
                    <select value={form.pagador} onChange={e => setField('pagador', e.target.value)} required>
                        {PAGADORES.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                </div>
                <div className="form-group">
                    <label className="required">Nome do Recebedor (Quem recebeu / Prestador do serviço):</label>
                    <input type="text" value={form.name} onChange={e => setField('name', e.target.value)}
                        placeholder="Ex: João Silva" required />
                </div>
                <div className="form-group">
                    <label className="required">Tipo de serviço:</label>
                    <select value={form.tipo_servico} onChange={e => setField('tipo_servico', e.target.value)} required>
                        {TIPOS_SERVICO.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>
                <div className="form-group">
                    <label>Descrição do Serviço:</label>
                    <textarea value={form.description} onChange={e => setField('description', e.target.value)}
                        placeholder="Ex: Descreva as atividades realizadas, no contexto do tipo dos serviços prestados." />
                </div>
                <div className="form-group">
                    <label className="required">Forma de pagamento:</label>
                    <div className="radio-group">
                        <label>
                            <input type="radio" name="forma_pagamento" checked={unidade === 'dia'}
                                onChange={() => setField('forma_pagamento', 'dia')} /> Pagamento por dia
                        </label>
                        <label>
                            <input type="radio" name="forma_pagamento" checked={unidade === 'hora'}
                                onChange={() => setField('forma_pagamento', 'hora')} /> Pagamento por hora
                        </label>
                    </div>
                </div>
                <div className="form-group">
                    <label className="required">Valor por {unidade} (R$):</label>
                    <input type="text" value={form.valor} onChange={e => setField('valor', e.target.value)}
                        onBlur={e => setField('valor', autoFormat(e.target.value))} placeholder="Ex: 150,00" required />
                </div>
                <div className="form-group">
                    <label className="required">Quantidade de {unidade}s:</label>
                    <input type="number" value={form.quantidade} onChange={e => setField('quantidade', e.target.value)}
                        min="0.01" step="any" placeholder="Ex: 5" required />
                </div>
                <div className="form-group">
                    <label>Complementos:</label>
                    <div className="complemento-group">
                        {form.complementos.map(item => (
                            <div className="complemento-row" key={item.id}>
                                <input type="text" value={item.valor} placeholder="Valor (R$) Ex: 50,00"
                                    // The value becomes required once a complement type is chosen
                                    required={item.tipo !== ''}
                                    onChange={e => updateComplemento(item.id, { valor: e.target.value })}
                                    onBlur={e => updateComplemento(item.id, { valor: autoFormat(e.target.value) })} />
                                <select value={item.tipo} onChange={e => updateComplemento(item.id, { tipo: e.target.value })}>
                                    <option value="">Complemento...</option>
                                    {TIPOS_COMPLEMENTO.map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                                <button type="button" className="remove-btn" title="Remover"
                                    onClick={() => removeComplemento(item.id)}>×</button>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="form-group">
                    <label className="required">Forma de Pagamento:</label>
                    <select value={form.meio_pagamento} onChange={e => setField('meio_pagamento', e.target.value)} required>
                        {MEIOS_PAGAMENTO.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
                <div className="total-box">Total: R$ <span>{formatBR(calcTotal(form))}</span></div>
                <div className="form-group">
                    <label className="required">Data:</label>
                    <input type="date" value={form.data} onChange={e => setField('data', e.target.value)} required />
                </div>
                <button type="submit">Visualizar impressão</button>
            </form>
        </div>
    );
}
