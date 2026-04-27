export function buildSpotlightButtonsMarkup(spots) {
  return spots
    .map((spot) => `
      <button type="button" class="spotlight-button ${spot.active ? "is-active" : ""}" data-spotlight="${spot.id}">
        <strong>${spot.name}</strong>
        <span>${spot.code} · ${spot.label}</span>
      </button>
    `)
    .join("");
}

export function buildExamSpotButtonsMarkup(visibleSpots, activeSpotId) {
  return visibleSpots
    .map((spot) => {
      const active = activeSpotId === spot.id;
      return `
        <button type="button" class="spotlight-button exam-spotlight-button ${active ? "is-active" : ""}" data-exam-spotlight="${spot.id}">
          <span class="spotlight-button-row">
            <strong>${spot.name}</strong>
            <span class="spotlight-badge">${spot.examCount}회</span>
          </span>
          <span>${spot.examCode} · ${spot.note}</span>
        </button>
      `;
    })
    .join("");
}

export function buildMissionStepsMarkup(missions, activeMissionId) {
  return missions
    .map((item) => `
      <button type="button" class="mission-step ${item.id === activeMissionId ? "is-active" : ""}" data-mission-id="${item.id}">
        <span>${item.order}</span>
        <strong>${item.title}</strong>
      </button>
    `)
    .join("");
}

export function buildMissionCardMarkup({ mission, concept }) {
  return `
    <div class="mission-focus">
      <strong>${mission.title}</strong>
      <p>${mission.focus}</p>
    </div>
    <div class="inline-chips">
      ${mission.knobTargets.map((target) => `<span class="mini-chip">${target}</span>`).join("")}
    </div>
    <div class="mission-grid">
      <section>
        <span>학생 과제</span>
        <p>${mission.studentTask}</p>
      </section>
      <section>
        <span>관찰 포인트</span>
        <p>${mission.observation}</p>
      </section>
      <section>
        <span>질문</span>
        <p>${mission.guidingQuestion}</p>
      </section>
      <section>
        <span>성공 기준</span>
        <p>${mission.successCheck}</p>
      </section>
    </div>
    ${concept ? `
      <div class="concept-card">
        <strong>${concept.title}</strong>
        <p>${concept.prompt}</p>
        <ul>
          ${concept.cues.map((cue) => `<li>${cue}</li>`).join("")}
        </ul>
      </div>
    ` : ""}
  `;
}

export function buildScenarioGuidanceMarkup({ guidance, recommendedPresetName }) {
  return `
    <div class="guidance-card">
      <div>
        <span class="eyebrow">Teacher Tip</span>
        <strong>${guidance.title}</strong>
      </div>
      <p>${guidance.useWhen}</p>
      <div class="inline-chips">
        <span class="mini-chip">추천 프리셋: ${recommendedPresetName}</span>
      </div>
      <ul>
        ${guidance.suggestedMoves.map((step) => `<li>${step}</li>`).join("")}
      </ul>
      <p class="guidance-note">${guidance.teacherNote}</p>
      <button type="button" class="guidance-button" data-guidance-preset="${guidance.recommendedPreset}">추천 프리셋 적용</button>
    </div>
  `;
}
