import { useEffect, useRef, useState } from 'react';

function Receipt({ receipt, via }) {
    const r = receipt;
    return (
        <div className="receipt-print">
            <div className="receipt-via"><span>{r.mes_referencia}</span><span>{via}</span></div>
            <div className="receipt-header">{r.title}</div>
            <div className="receipt-body">
                Eu, <span className="highlight">&nbsp;{r.name}&nbsp;</span>, recebi de{' '}
                <span className="highlight">&nbsp;{r.pagador}&nbsp;</span> a importância de{' '}
                <span className="highlight">&nbsp;R$ {r.total}&nbsp;</span>, referente aos itens descritos abaixo:
            </div>
            <table className="receipt-table">
                <thead>
                    <tr>
                        <th>Descrição</th>
                        <th className="num">Quantidade</th>
                        <th className="num">Valor unitário</th>
                        <th className="num">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{r.tipo_servico}{r.description && ` - ${r.description}`}</td>
                        <td className="num">{r.quantidade} {r.unidade}</td>
                        <td className="num">R$ {r.valor} / {r.forma_pagamento}</td>
                        <td className="num">R$ {r.subtotal_servico}</td>
                    </tr>
                    {r.complementos.map((item, i) => (
                        <tr key={i}>
                            <td>{item.tipo}</td>
                            <td className="num">-</td>
                            <td className="num">-</td>
                            <td className="num">R$ {item.valor}</td>
                        </tr>
                    ))}
                </tbody>
                <tfoot>
                    <tr>
                        <td colSpan="3">Total</td>
                        <td className="num">R$ {r.total}</td>
                    </tr>
                </tfoot>
            </table>
            <div className="receipt-body">
                Forma de pagamento: <span className="highlight">&nbsp;{r.meio_pagamento}&nbsp;</span>.
                Para clareza e firmeza do pagamento, firmo o presente recibo.
            </div>
            <div className="receipt-footer">
                {r.cidade}, {r.data}.
                <div className="signatures">
                    <div className="signature-line">{r.pagador}<span className="signature-role">Pagador</span></div>
                    <div className="signature-line">{r.name}<span className="signature-role">Recebedor</span></div>
                </div>
            </div>
        </div>
    );
}

export default function ReceiptPreview({ receipt, onBack }) {
    const sheetRef = useRef(null);
    const [generating, setGenerating] = useState(false);

    // Switches the page background to the gray "sheet on a desk" look while previewing
    useEffect(() => {
        document.body.classList.add('browser');
        return () => document.body.classList.remove('browser');
    }, []);

    async function handleGeneratePdf() {
        setGenerating(true);
        try {
            // Loaded on demand so the form opens faster
            const { default: html2pdf } = await import('html2pdf.js');
            await html2pdf()
                .set({
                    margin: 12,
                    filename: 'recibo.pdf',
                    html2canvas: { scale: 2 },
                    jsPDF: { unit: 'mm', format: 'letter', orientation: 'portrait' },
                })
                .from(sheetRef.current)
                .save();
        } finally {
            setGenerating(false);
        }
    }

    return (
        <>
            <div className="print-toolbar">
                <button type="button" className="secondary" onClick={onBack}>Voltar</button>
                <button type="button" onClick={handleGeneratePdf} disabled={generating}>
                    {generating ? 'Gerando...' : 'Gerar PDF do Recibo'}
                </button>
                <button type="button" onClick={() => window.print()}>Imprimir</button>
            </div>
            <div className="container sheet">
                <div ref={sheetRef}>
                    <Receipt receipt={receipt} via="1ª via" />
                    <div className="cut-line">✂ recorte aqui</div>
                    <Receipt receipt={receipt} via="2ª via" />
                </div>
            </div>
        </>
    );
}
