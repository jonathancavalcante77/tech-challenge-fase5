const form = document.querySelector('#recommendation-form');
const recommendButton = document.querySelector('#recommend-button');
const formStatus = document.querySelector('#form-status');
const feedbackStatus = document.querySelector('#feedback-status');
const feedbackButtons = [...document.querySelectorAll('[data-reward]')];
const exampleButtons = [...document.querySelectorAll('[data-example]')];
const emptyState = document.querySelector('#empty-state');
const decisionContent = document.querySelector('#decision-content');
const evidencePanel = document.querySelector('#evidence-panel');
const feedbackPanel = document.querySelector('#feedback-panel');
const feedbackControls = document.querySelector('#feedback-controls');
const comparison = document.querySelector('#action-comparison');
const categoryError = document.querySelector('#category-error');
const categoryFields = document.querySelector('.category-fields');
const themeToggle = document.querySelector('#theme-toggle');
const themeToggleText = document.querySelector('#theme-toggle-text');
const percentage = new Intl.NumberFormat('pt-BR', {
  style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2,
});

let currentDecisionId = null;
let activeRecommendation = null;
let sendingFeedback = false;

function savedTheme() {
  try { return localStorage.getItem('datathon-theme'); } catch { return null; }
}

function applyTheme(theme, persist = false) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#17191e' : '#f6f7f8';
  themeToggle.setAttribute('aria-label', theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro');
  themeToggleText.textContent = theme === 'dark' ? 'Tema claro' : 'Tema escuro';
  if (persist) {
    try { localStorage.setItem('datathon-theme', theme); } catch {}
  }
}

applyTheme(document.documentElement.dataset.theme || 'light');
themeToggle.addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark', true);
});
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (event) => {
  if (!savedTheme()) applyTheme(event.matches ? 'dark' : 'light');
});

function setCategoryError(visible) {
  categoryError.hidden = !visible;
  categoryFields.setAttribute('aria-invalid', String(visible));
  for (const name of ['mens', 'womens']) {
    form.elements.namedItem(name).setAttribute('aria-invalid', String(visible));
  }
}

function setMessage(element, text, kind = '') {
  element.textContent = text;
  element.className = kind ? `message ${kind}` : 'message';
}

function errorMessage(error, fallback) {
  return error instanceof TypeError || error instanceof SyntaxError
    ? fallback
    : error.message || fallback;
}

function setExampleSelection(id) {
  for (const button of exampleButtons) {
    button.setAttribute('aria-pressed', String(button.dataset.example === id));
  }
}

function clearDecision() {
  currentDecisionId = null;
  emptyState.hidden = false;
  decisionContent.hidden = true;
  evidencePanel.hidden = true;
  feedbackPanel.hidden = true;
  feedbackControls.hidden = false;
  for (const button of feedbackButtons) {
    button.disabled = false;
    button.classList.remove('recorded');
  }
  setMessage(feedbackStatus, '');
}

function invalidateDecision() {
  if (activeRecommendation) activeRecommendation.abort();
  activeRecommendation = null;
  recommendButton.disabled = false;
  recommendButton.classList.remove('is-loading');
  form.removeAttribute('aria-busy');
  recommendButton.textContent = 'Gerar recomendação';
  clearDecision();
  setMessage(formStatus, '');
}

function contextFromForm() {
  const values = Object.fromEntries(new FormData(form).entries());
  return {
    recency: Number(values.recency),
    history: Number(values.history),
    mens: form.elements.namedItem('mens').checked ? 1 : 0,
    womens: form.elements.namedItem('womens').checked ? 1 : 0,
    newbie: Number(values.newbie),
    zip_code: values.zip_code,
    channel: values.channel,
  };
}

function segmentLabel(segment) {
  const [period, category] = segment.split(':');
  const periods = {
    recent: 'Compra recente (até 3 meses)',
    middle: 'Compra entre 4 e 6 meses',
    old: 'Compra entre 7 e 12 meses',
  };
  const categories = {
    mens: 'compras na categoria masculina',
    womens: 'compras na categoria feminina',
    mixed: 'compras nas duas categorias',
  };
  return `${periods[period] || 'Recência registrada'} · ${categories[category] || 'categoria não informada'}`;
}

function renderComparison(decision) {
  comparison.replaceChildren();
  const highest = Math.max(...Object.values(decision.posterior_means));
  const ceiling = Math.max(0.005, Math.ceil(highest * 1200) / 1000);
  document.querySelector('#plot-scale-max').textContent = percentage.format(ceiling);
  for (const offer of window.catalog) {
    const value = decision.posterior_means[offer.key];
    const row = document.createElement('div');
    row.className = offer.key === decision.action ? 'action-row chosen' : 'action-row';
    row.setAttribute('role', 'listitem');
    row.setAttribute('aria-label', `${offer.label}: ${percentage.format(value)}`);

    const header = document.createElement('div');
    header.className = 'action-row-header';
    const name = document.createElement('span');
    name.className = 'action-name';
    name.textContent = offer.label;
    if (offer.key === decision.action) {
      const tag = document.createElement('span');
      tag.className = 'chosen-tag';
      tag.textContent = 'Escolhida';
      name.append(tag);
    }
    const estimate = document.createElement('strong');
    estimate.className = 'action-value';
    estimate.textContent = percentage.format(value);
    header.append(name, estimate);

    const track = document.createElement('div');
    track.className = 'bar-track';
    track.setAttribute('aria-hidden', 'true');
    const marker = document.createElement('span');
    marker.className = 'plot-marker';
    marker.style.left = `${(value / ceiling) * 100}%`;
    track.append(marker);
    row.append(header, track);
    comparison.append(row);
  }
}

function renderDecision(decision) {
  const offer = window.catalog.find((item) => item.key === decision.action);
  const candidates = window.catalog.filter((item) => item.key in decision.posterior_means);
  if (!offer || candidates.length !== window.catalog.length) {
    throw new Error('A recomendação não pôde ser apresentada. Tente novamente.');
  }
  const strongest = candidates.reduce((best, item) =>
    decision.posterior_means[item.key] > decision.posterior_means[best.key] ? item : best,
  );

  document.querySelector('#offer-label').textContent = offer.label;
  document.querySelector('#decision-copy').textContent = offer.description;
  document.querySelector('#segment-label').textContent = segmentLabel(decision.segment);
  const estimateReason = decision.exploration
    ? `Nesta rodada, a política selecionou ${offer.label.toLowerCase()}. ${strongest.label} tem a maior média estimada para este grupo; testar outra ação ajuda a política a aprender.`
    : `Nesta rodada, a política selecionou ${offer.label.toLowerCase()}, que também tem a maior média estimada para este grupo.`;
  const category = decision.segment.split(':')[1];
  const differentCategory = (category === 'mens' && decision.action === 'womens_email')
    || (category === 'womens' && decision.action === 'mens_email');
  const categoryNote = differentCategory
    ? ' As compras anteriores definem o grupo, mas não limitam a campanha: as três ações são comparadas.'
    : '';
  document.querySelector('#decision-reason').textContent = estimateReason + categoryNote;
  document.querySelector('#segment-code').textContent = decision.segment;
  document.querySelector('#version-code').textContent = decision.policy_version;
  document.querySelector('#exploration-code').textContent = decision.exploration ? 'Sim' : 'Não';
  renderComparison(decision);

  currentDecisionId = decision.decision_id;
  emptyState.hidden = true;
  decisionContent.hidden = false;
  evidencePanel.hidden = false;
  feedbackPanel.hidden = false;
  const readonly = decision.mode === 'readonly';
  feedbackControls.hidden = readonly;
  document.querySelector('#feedback-intro').textContent = readonly
    ? 'Esta demonstração está em modo somente leitura. O resultado não pode ser registrado e a política não aprende nesta sessão.'
    : 'Registre a resposta fictícia observada para esta decisão. O modelo usará esse resultado nas próximas escolhas locais.';
}

form.addEventListener('input', () => {
  setExampleSelection(null);
  invalidateDecision();
  if (form.elements.namedItem('mens').checked || form.elements.namedItem('womens').checked) {
    setCategoryError(false);
  }
});

for (const button of exampleButtons) {
  button.addEventListener('click', () => {
    const example = window.examples.find((item) => item.id === button.dataset.example);
    if (!example) return;
    invalidateDecision();
    for (const [name, value] of Object.entries(example.context)) {
      const input = form.elements.namedItem(name);
      if (input?.type === 'checkbox') input.checked = Boolean(value);
      else if (input) input.value = String(value);
    }
    setCategoryError(false);
    setExampleSelection(example.id);
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  invalidateDecision();
  const context = contextFromForm();
  setCategoryError(false);
  if (context.mens === 0 && context.womens === 0) {
    setCategoryError(true);
    form.elements.namedItem('mens').focus();
    return;
  }

  const controller = new AbortController();
  activeRecommendation = controller;
  recommendButton.disabled = true;
  recommendButton.classList.add('is-loading');
  form.setAttribute('aria-busy', 'true');
  recommendButton.textContent = 'Calculando…';
  setMessage(formStatus, 'Consultando a política para este perfil…', 'pending');
  try {
    const response = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(context),
      signal: controller.signal,
    });
    const body = await response.json();
    if (activeRecommendation !== controller) return;
    if (!response.ok) {
      const detail = typeof body.detail === 'string' ? body.detail : 'Confira os dados informados e tente novamente.';
      throw new Error(detail);
    }
    renderDecision(body);
    setMessage(formStatus, 'Recomendação gerada para o perfil informado.', 'success');
    if (window.matchMedia('(max-width: 910px)').matches) {
      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      document.querySelector('.analysis-panel').scrollIntoView({
        behavior: reducedMotion ? 'auto' : 'smooth', block: 'start',
      });
    }
  } catch (error) {
    if (activeRecommendation !== controller || error.name === 'AbortError') return;
    clearDecision();
    setMessage(formStatus, errorMessage(error, 'Falha de conexão. Tente novamente.'), 'error');
  } finally {
    if (activeRecommendation === controller) {
      activeRecommendation = null;
      recommendButton.disabled = false;
      recommendButton.classList.remove('is-loading');
      form.removeAttribute('aria-busy');
      recommendButton.textContent = 'Gerar recomendação';
    }
  }
});

for (const button of feedbackButtons) {
  button.addEventListener('click', async () => {
    if (!currentDecisionId || sendingFeedback || button.disabled) return;
    const decisionId = currentDecisionId;
    const reward = Number(button.dataset.reward);
    sendingFeedback = true;
    for (const control of feedbackButtons) control.disabled = true;
    setMessage(feedbackStatus, 'Registrando o resultado...', 'pending');
    try {
      const response = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision_id: decisionId, reward }),
      });
      const body = await response.json();
      if (currentDecisionId !== decisionId) return;
      if (!response.ok) {
        if (response.status === 409) {
          setMessage(feedbackStatus, 'Já existe outro resultado registrado para esta decisão. Gere uma nova recomendação.', 'error');
          return;
        }
        throw new Error('Não foi possível registrar o resultado. Tente novamente.');
      }
      const outcome = reward === 1 ? 'Compra registrada.' : 'Ausência de compra registrada.';
      const detail = body.status === 'duplicate'
        ? ' Este resultado já havia sido registrado.'
        : ' A política local foi atualizada para as próximas decisões.';
      setMessage(feedbackStatus, outcome + detail, 'success');
      button.classList.add('recorded');
    } catch (error) {
      if (currentDecisionId !== decisionId) return;
      for (const control of feedbackButtons) control.disabled = false;
      setMessage(feedbackStatus, errorMessage(error, 'Falha de conexão. Tente novamente.'), 'error');
    } finally {
      sendingFeedback = false;
    }
  });
}
