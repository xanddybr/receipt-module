import { useState } from 'react';
import ReceiptForm, { emptyComplemento } from './ReceiptForm.jsx';
import ReceiptPreview from './ReceiptPreview.jsx';
import { buildReceiptData } from './format.js';

const INITIAL_FORM = {
    title: 'Recibo de pagamento de prestação de serviços',
    pagador: 'Alexandre de Santana de Souza',
    name: '',
    tipo_servico: 'Serviços domésticos',
    description: '',
    forma_pagamento: 'dia',
    valor: '',
    quantidade: '',
    complementos: [emptyComplemento()],
    meio_pagamento: 'Pix',
    data: '',
};

export default function App() {
    // The form is kept in state so "Voltar" returns to it with everything filled in
    const [form, setForm] = useState(INITIAL_FORM);
    const [receipt, setReceipt] = useState(null);

    function handleVisualizar() {
        const { data, error } = buildReceiptData(form);
        if (error) {
            alert(error);
            return;
        }
        setReceipt(data);
    }

    if (receipt) {
        return <ReceiptPreview receipt={receipt} onBack={() => setReceipt(null)} />;
    }
    return <ReceiptForm form={form} setForm={setForm} onSubmit={handleVisualizar} />;
}
