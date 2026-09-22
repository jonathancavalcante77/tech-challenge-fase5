const form = document.querySelector('#recommendation-form');
const feedbackArea = document.querySelector('#feedback-area');
const statusElement = document.querySelector('#status');
let lastDecisionId = null;

function contextFromForm() {
  const values = Object.fromEntries(new FormData(form).entries());
  return {
    recency: Number(values.recency),
    history: Number(values.history),
    mens: Number(values.mens),
    womens: Number(values.womens),
    newbie: Number(values.newbie),
    zip_code: values.zip_code,
    channel: values.channel,
  };
}

function showDecision(decision) {
  const offer = window.catalog.find((item) => item.key === decision.action);
  document.querySelector('#offer-label').textContent = offer ? offer.label : decision.action;
  document.querySelector('#decision-copy').textContent = offer ? offer.description : 'Ação selecionada pela política.';
  document.querySelector('#segment').textContent = decision.segment;
  document.querySelector('#exploration').textContent = decision.exploration ? 'Sim' : 'Não';
  document.querySelector('#version').textContent = decision.policy_version;
  lastDecisionId = decision.decision_id;
  feedbackArea.hidden = decision.mode === 'readonly';
  statusElement.textContent = decision.mode === 'readonly' ? 'Demonstração pública em modo somente leitura.' : '';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusElement.textContent = 'Consultando a política…';
  const response = await fetch('/recommend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(contextFromForm()) });
  const body = await response.json();
  if (!response.ok) { statusElement.textContent = body.detail || 'Não foi possível gerar a recomendação.'; return; }
  showDecision(body);
});

document.querySelectorAll('[data-reward]').forEach((button) => {
  button.addEventListener('click', async () => {
    if (!lastDecisionId) return;
    const response = await fetch('/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision_id: lastDecisionId, reward: Number(button.dataset.reward) }) });
    const body = await response.json();
    statusElement.textContent = response.ok ? `Feedback registrado: ${body.status}.` : (body.detail || 'Não foi possível registrar o feedback.');
  });
});
