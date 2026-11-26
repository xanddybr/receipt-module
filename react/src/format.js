// Converts "1.500,00", "1500", "1500,5" or "1500.50" into 1500.00 (NaN when invalid)
export function parseBR(text) {
    text = String(text ?? '').replace(/[R$\s]/g, '');
    if (text.includes(',')) {
        text = text.replace(/\./g, '').replace(',', '.');
    } else if (!/^\d+\.\d{1,2}$/.test(text)) {
        text = text.replace(/\./g, '');
    }
    return /^\d*\.?\d+$/.test(text) ? parseFloat(text) : NaN;
}

// Converts 1500 into "1.500,00"
export function formatBR(number) {
    return number.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export const CIDADE = 'Rio de Janeiro';

const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];

// Converts "2026-10-29" into ["29 de outubro de 2026", "Outubro/2026"]
export function formatDateExtenso(text) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
    if (!match) {
        return [text, ''];
    }
    const [, ano, mesNum, dia] = match;
    const mes = MESES[Number(mesNum) - 1];
    return [`${Number(dia)} de ${mes} de ${ano}`, `${mes[0].toUpperCase()}${mes.slice(1)}/${ano}`];
}

// Live total shown in the form; invalid fields count as zero
export function calcTotal(form) {
    const valor = parseBR(form.valor) || 0;
    const quantidade = parseFloat(form.quantidade) || 0;
    return form.complementos
        .filter(item => item.tipo !== '')
        .reduce((total, item) => total + (parseBR(item.valor) || 0), valor * quantidade);
}

// Returns { data } with the receipt fields, or { error } with a message
export function buildReceiptData(form) {
    const valor = parseBR(form.valor);
    const quantidade = parseFloat(form.quantidade);
    if (isNaN(valor) || isNaN(quantidade)) {
        return { error: 'Valor ou quantidade inválidos. Use o formato 1.500,00 para o valor.' };
    }

    const unidade = quantidade === 1 ? form.forma_pagamento : form.forma_pagamento + 's';
    const quantidadeTexto = Number.isInteger(quantidade) ? String(quantidade) : formatBR(quantidade);
    const subtotalServico = valor * quantidade;

    // Extra items (Passagem, Bonificação); rows without a chosen type are ignored
    const complementos = [];
    for (const item of form.complementos) {
        if (!item.tipo) {
            continue;
        }
        const valorComplemento = parseBR(item.valor);
        if (isNaN(valorComplemento)) {
            return { error: `Valor inválido para o complemento ${item.tipo}. Use o formato 1.500,00.` };
        }
        complementos.push({ tipo: item.tipo, valor: valorComplemento });
    }

    const total = subtotalServico + complementos.reduce((sum, item) => sum + item.valor, 0);
    const [dataExtenso, mesReferencia] = formatDateExtenso(form.data);

    return {
        data: {
            title: form.title,
            pagador: form.pagador,
            name: form.name,
            tipo_servico: form.tipo_servico,
            description: form.description,
            forma_pagamento: form.forma_pagamento,
            valor: formatBR(valor),
            quantidade: quantidadeTexto,
            unidade,
            subtotal_servico: formatBR(subtotalServico),
            complementos: complementos.map(item => ({ tipo: item.tipo, valor: formatBR(item.valor) })),
            total: formatBR(total),
            cidade: CIDADE,
            data: dataExtenso,
            mes_referencia: mesReferencia,
            meio_pagamento: form.meio_pagamento,
        },
    };
}
