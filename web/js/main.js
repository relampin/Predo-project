/**
 * AI Bridge Test Page — JavaScript
 * Interatividade mínima para validação do fluxo.
 */

document.addEventListener('DOMContentLoaded', () => {
  const btnValidate = document.getElementById('btn-validate');
  const resultContainer = document.getElementById('validation-result');
  const flowSteps = document.querySelectorAll('.flow__step');

  /**
   * Simula a validação do ciclo ai-bridge, ativando os
   * passos do flow indicator em sequência.
   */
  btnValidate.addEventListener('click', async () => {
    btnValidate.classList.add('cta__button--running');
    btnValidate.innerHTML = '<span class="cta__icon">⏳</span> Validando...';
    resultContainer.hidden = true;

    // Anima cada passo do fluxo
    for (let i = 0; i < flowSteps.length; i++) {
      await delay(600);
      flowSteps[i].classList.add('flow__step--active');
      if (i > 0) {
        flowSteps[i - 1].classList.remove('flow__step--active');
        flowSteps[i - 1].classList.add('flow__step--complete');
      }
    }

    // Marca último passo como completo
    await delay(600);
    flowSteps[flowSteps.length - 1].classList.remove('flow__step--active');
    flowSteps[flowSteps.length - 1].classList.add('flow__step--complete');

    // Exibe resultado
    showResult();
  });

  /**
   * Exibe o resultado da validação simulada.
   */
  function showResult() {
    const now = new Date().toLocaleString('pt-BR');
    resultContainer.innerHTML = `
      <div style="margin-bottom: 12px;">
        <strong style="color: #22c55e;">✅ Validação concluída com sucesso</strong>
      </div>
      <div style="color: var(--color-text-muted); line-height: 1.8;">
        <div>📋 <strong>TASK gerado:</strong> TASK-${getDateId()}-002</div>
        <div>🔄 <strong>Estado:</strong> ready_for_audit</div>
        <div>👤 <strong>Próximo dono:</strong> auditor</div>
        <div>🕐 <strong>Timestamp:</strong> ${now}</div>
      </div>
    `;
    resultContainer.classList.remove('cta__result--error');
    resultContainer.classList.add('cta__result--success');
    resultContainer.hidden = false;

    btnValidate.classList.remove('cta__button--running');
    btnValidate.innerHTML = '<span class="cta__icon">✓</span> Validação Completa';
  }

  /**
   * Gera ID de data no formato YYYYMMDD.
   */
  function getDateId() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}${m}${day}`;
  }

  /**
   * Utilitário de delay.
   */
  function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
});
